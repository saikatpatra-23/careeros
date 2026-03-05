"""
CareerOS Naukri Watcher
========================
Background mein chalta rehta hai:
  - 9:30 AM aur 2:00 PM pe automatically run karta hai
  - Make.com WhatsApp trigger: POST http://localhost:8765/trigger
  - Manual: careeros/job_applier/trigger.txt file banao

Setup:
  1. python watcher.py         — start karo
  2. ngrok http 8765           — public URL milega
  3. Make.com mein wo URL set karo
"""

import time
import subprocess
import os
import json
import threading
from datetime import datetime, date
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE_DIR     = Path(__file__).parent
SCRIPT       = BASE_DIR / "run.py"
LOG_FILE     = BASE_DIR / "logs" / "watcher.log"
TRIGGER_FILE = BASE_DIR / "trigger.txt"
STATE_FILE   = BASE_DIR / "watcher_state.json"

SCHEDULED_TIMES = ["09:30", "14:00"]
WEBHOOK_PORT    = 8765
CHECK_INTERVAL  = 60   # seconds

LOG_FILE.parent.mkdir(exist_ok=True)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── State ──────────────────────────────────────────────────────────────────────
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


# ── Run script ─────────────────────────────────────────────────────────────────
def run_automation(reason: str):
    log(f"{'='*50}")
    log(f"TRIGGER: {reason}")
    log(f"{'='*50}")
    try:
        result = subprocess.run(
            ["python", "-u", str(SCRIPT)],
            cwd=str(BASE_DIR),
            timeout=7200
        )
        log(f"Done. Exit code: {result.returncode}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log("TIMEOUT — script ran too long")
        return False
    except Exception as e:
        log(f"ERROR: {e}")
        return False


# ── Webhook server (Make.com → WhatsApp trigger) ───────────────────────────────
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
        pass   # suppress default HTTP logs


def start_webhook_server():
    server = HTTPServer(("0.0.0.0", WEBHOOK_PORT), WebhookHandler)
    log(f"Webhook server running on port {WEBHOOK_PORT}")
    server.serve_forever()


# ── Main loop ──────────────────────────────────────────────────────────────────
def main():
    log("=" * 55)
    log("  CareerOS Naukri Watcher — Started")
    log(f"  Scheduled: {', '.join(SCHEDULED_TIMES)}")
    log(f"  Webhook:   http://localhost:{WEBHOOK_PORT}/trigger")
    log(f"  Manual:    create trigger.txt in job_applier/")
    log("=" * 55)

    # Start webhook server in background thread
    t = threading.Thread(target=start_webhook_server, daemon=True)
    t.start()

    state = load_state()

    while True:
        current_time = datetime.now().strftime("%H:%M")

        # 1. Scheduled times
        for t_sched in SCHEDULED_TIMES:
            run_key = f"scheduled_{t_sched}"
            if current_time >= t_sched and not already_ran_today(state, run_key):
                run_automation(f"Scheduled {t_sched}")
                mark_ran(state, run_key)
                state = load_state()
                break

        # 2. Trigger file (Make.com webhook creates this)
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
