"""
CareerOS Naukri Watcher
========================
Webhook/manual mode mein chalta hai:
  - Schedule Windows Task Scheduler handle karta hai
  - Make.com WhatsApp trigger: POST http://localhost:8765/trigger
  - Manual: careeros/job_applier/trigger.txt file banao

Setup:
  1. python watcher.py         - start karo
  2. ngrok http 8765           - public URL milega
  3. Make.com mein wo URL set karo
"""

import json
import msvcrt
import os
import subprocess
import threading
import time
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).parent
SCRIPT = BASE_DIR / "run.py"
LOG_FILE = BASE_DIR / "logs" / "watcher.log"
TRIGGER_FILE = BASE_DIR / "trigger.txt"
STATE_FILE = BASE_DIR / "watcher_state.json"
LOCK_FILE = BASE_DIR / "watcher.lock"

SCHEDULED_TIMES = []  # Scheduling is handled by Windows Task Scheduler; watcher is manual/webhook-only
WEBHOOK_PORT = 8765
CHECK_INTERVAL = 60

LOG_FILE.parent.mkdir(exist_ok=True)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state():
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
    except Exception:
        pass
    return {"last_run_dates": {}}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state))


def already_ran_today(state, key):
    return state.get("last_run_dates", {}).get(key) == date.today().isoformat()


def mark_ran(state, key):
    state.setdefault("last_run_dates", {})[key] = date.today().isoformat()
    save_state(state)


def acquire_single_instance():
    LOCK_FILE.parent.mkdir(exist_ok=True)
    lock_handle = open(LOCK_FILE, "a+", encoding="utf-8")
    try:
        msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
        lock_handle.seek(0)
        lock_handle.truncate()
        lock_handle.write(str(os.getpid()))
        lock_handle.flush()
        return lock_handle
    except OSError:
        lock_handle.close()
        return None


def run_automation(reason: str):
    log(f"{'=' * 50}")
    log(f"TRIGGER: {reason}")
    log(f"{'=' * 50}")
    try:
        result = subprocess.run(["python", "-u", str(SCRIPT)], cwd=str(BASE_DIR), timeout=7200)
        log(f"Done. Exit code: {result.returncode}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log("TIMEOUT - script ran too long")
        return False
    except Exception as e:
        log(f"ERROR: {e}")
        return False


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/trigger":
            TRIGGER_FILE.write_text("whatsapp")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "triggered"}')
            log("WhatsApp trigger received via Make.com webhook")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


def start_webhook_server():
    server = HTTPServer(("0.0.0.0", WEBHOOK_PORT), WebhookHandler)
    log(f"Webhook server running on port {WEBHOOK_PORT}")
    server.serve_forever()


def main():
    lock_handle = acquire_single_instance()
    if not lock_handle:
        log("Another watcher instance is already running. Exiting duplicate watcher.")
        return

    log("=" * 55)
    log("  CareerOS Naukri Watcher - Started")
    schedule_display = ', '.join(SCHEDULED_TIMES) if SCHEDULED_TIMES else 'disabled (Task Scheduler owns schedule)'
    log(f"  Scheduled: {schedule_display}")
    log(f"  Webhook:   http://localhost:{WEBHOOK_PORT}/trigger")
    log("  Manual:    create trigger.txt in job_applier/")
    log("=" * 55)

    thread = threading.Thread(target=start_webhook_server, daemon=True)
    thread.start()

    state = load_state()
    while True:
        current_time = datetime.now().strftime("%H:%M")

        if SCHEDULED_TIMES:
            for scheduled_time in SCHEDULED_TIMES:
                run_key = f"scheduled_{scheduled_time}"
                if current_time >= scheduled_time and not already_ran_today(state, run_key):
                    success = run_automation(f"Scheduled {scheduled_time}")
                    if success:
                        mark_ran(state, run_key)
                    else:
                        log(f"Scheduled run {scheduled_time} failed - slot will retry on next check.")
                    state = load_state()
                    break

        if TRIGGER_FILE.exists():
            reason = TRIGGER_FILE.read_text().strip() or "manual"
            TRIGGER_FILE.unlink()
            run_automation(f"Trigger: {reason}")
            state = load_state()

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Watcher stopped.")
