"""
CareerOS Job Applier â€” Local Runner
Run locally so your residential IP bypasses Naukri's bot detection.
Schedule via Windows Task Scheduler.
"""
import asyncio
import json
import random
import requests
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from cryptography.fernet import Fernet

import anthropic
from playwright.async_api import async_playwright

# ntfy notifications (inline â€” no CareerOS module import needed in local runner)
import hashlib

def _ntfy_topic(email: str) -> str:
    return "careeros-" + hashlib.md5(email.lower().strip().encode()).hexdigest()[:10]

def _ntfy(topic: str, title: str, message: str, priority: str = "default",
          tags: list = None, click_url: str = "") -> None:
    try:
        headers = {"Title": title, "Priority": priority}
        if tags:       headers["Tags"]  = ",".join(tags)
        if click_url:  headers["Click"] = click_url
        requests.post(f"https://ntfy.sh/{topic}", data=message.encode("utf-8"),
                      headers=headers, timeout=5)
    except Exception:
        pass

def _sync_results(email: str, results: dict,
                  supabase_url: str = "", supabase_key: str = "",
                  sync_url: str = "") -> None:
    """
    Push run results to CareerOS web app.
    Mode 1 (preferred): Supabase â€” direct DB write, bypasses Streamlit auth gate.
    Mode 2 (legacy):    api_ingest URL â€” blocked by Streamlit Google OAuth.
    Mode 3 (dev):       Same-machine local file write.
    """
    # â”€â”€ Mode 1: Supabase â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if supabase_url and supabase_key:
        try:
            headers = {
                "apikey":        supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type":  "application/json",
                "Prefer":        "return=minimal",
            }
            row = {
                "user_email":   email,
                "run_date":     results.get("date", ""),
                "jobs_found":   results.get("jobs_found", 0),
                "jobs_applied": results.get("jobs_applied", 0),
                "jobs_skipped": results.get("jobs_skipped", 0),
                "applied_list": results.get("applied_list", []),
                "skipped_list": results.get("skipped_list", []),
                "hr_invites":   results.get("hr_invites", []),
                "errors":       results.get("errors", []),
            }
            resp = requests.post(
                f"{supabase_url.rstrip('/')}/rest/v1/run_history",
                headers=headers, json=row, timeout=15,
            )
            if resp.status_code in (200, 201):
                log.info("Results synced to Supabase.")
            else:
                log.warning(f"Supabase sync returned {resp.status_code}: {resp.text[:200]}")

            # Insert each HR invite as an individual row
            for inv in results.get("hr_invites", []):
                if not inv.get("company"):
                    continue
                requests.post(
                    f"{supabase_url.rstrip('/')}/rest/v1/hr_invites",
                    headers=headers,
                    json={
                        "user_email":  email,
                        "company":     inv.get("company", ""),
                        "title":       inv.get("title", ""),
                        "url":         inv.get("url", ""),
                        "hr_name":     inv.get("hr_name", ""),
                        "applied":     inv.get("applied", False),
                        "reason":      inv.get("reason", ""),
                        "detected_at": results.get("date", ""),
                    },
                    timeout=10,
                )
        except Exception as e:
            log.warning(f"Supabase sync failed (non-fatal): {e}")
        return

    # â”€â”€ Mode 2: api_ingest URL (legacy) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if sync_url:
        try:
            import base64 as _b64
            payload  = json.dumps({"email": email, "results": results}, ensure_ascii=False)
            encoded  = _b64.b64encode(payload.encode("utf-8")).decode("ascii")
            full_url = sync_url.rstrip("=").rstrip("&data") + "&data=" + encoded
            resp     = requests.get(full_url, timeout=15)
            if resp.status_code == 200:
                log.info("Results synced to CareerOS cloud.")
            else:
                log.warning(f"Cloud sync returned {resp.status_code}")
        except Exception as e:
            log.warning(f"Cloud sync failed (non-fatal): {e}")
        return

    # â”€â”€ Mode 2: Same-machine local sync â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Only works when web app and runner are on the same PC.
    # Tries common paths: same folder, one level up, two levels up.
    user_id = hashlib.md5(email.lower().encode()).hexdigest()[:12]
    base    = Path(__file__).parent
    candidates = [
        base.parent.parent / "data" / "users" / user_id,   # careeros project layout
        base.parent / "data" / "users" / user_id,           # one level up
        base / "data" / "users" / user_id,                  # same folder
    ]
    data_dir = next((p for p in candidates if p.parent.parent.exists()), candidates[0])
    try:
        data_dir.mkdir(parents=True, exist_ok=True)

        hist_file = data_dir / "apply_history.json"
        history   = json.loads(hist_file.read_text(encoding="utf-8")) if hist_file.exists() else []
        history.insert(0, results)
        hist_file.write_text(json.dumps(history[:30], indent=2, ensure_ascii=False), encoding="utf-8")

        inv_file = data_dir / "hr_invites.json"
        invites  = json.loads(inv_file.read_text(encoding="utf-8")) if inv_file.exists() else []
        for inv in results.get("hr_invites", []):
            invites.insert(0, inv)
        inv_file.write_text(json.dumps(invites[:50], indent=2, ensure_ascii=False), encoding="utf-8")

        log.info(f"Results synced locally â†’ {data_dir}")
    except Exception as e:
        log.warning(f"Local sync failed (non-fatal): {e}")


# â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CONFIG_FILE = Path(__file__).parent / "config.json"
LOG_FILE    = Path(__file__).parent / "logs" / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
LOG_FILE.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# â”€â”€ Entry point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def main():
    LOG_FILE.parent.mkdir(exist_ok=True)

    if not CONFIG_FILE.exists():
        log.error(f"config.json not found at {CONFIG_FILE}")
        return

    with open(CONFIG_FILE, encoding="utf-8-sig") as f:
        inp = json.load(f)

    # â”€â”€ Decrypt password â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    fernet_key   = inp.get("fernet_key", "")
    pass_enc     = inp.get("naukri_pass_enc", "")
    naukri_email = inp.get("naukri_email", "")

    if not (fernet_key and pass_enc and naukri_email):
        log.error("Missing credentials in config.json")
        return

    try:
        naukri_password = Fernet(fernet_key.encode()).decrypt(pass_enc.encode()).decode()
    except Exception as e:
        log.error(f"Decryption failed: {e}")
        return

    # â”€â”€ Params â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    resume_data   = inp.get("resume_data", {})
    target_role   = resume_data.get("target_title", "Business Analyst")
    domain_family = resume_data.get("domain_family", "enterprise_IT")
    locations      = inp.get("preferred_locations", ["Pune"])
    current_loc    = inp.get("current_location", locations[0] if locations else "Mumbai")
    salary_min     = inp.get("salary_min", 0)
    max_apply      = inp.get("max_jobs_per_run", 5)
    max_jobs_scan  = max(max_apply, inp.get("max_jobs_to_scan", 60))
    exp_min_cfg    = int(inp.get("exp_min", 0) or 0)
    title_limit    = max(1, int(inp.get("search_titles_per_run", 4) or 4))
    location_limit = max(1, int(inp.get("search_locations_per_run", 3) or 3))

    exp_years = sum(
        _parse_years(job.get("period", ""))
        for job in resume_data.get("experience", [])
    )
    exp_years = max(1, min(exp_years, 20))
    exp_min   = max(exp_min_cfg, max(0, exp_years - 2))
    exp_max   = max(exp_years + 2, exp_min + 2)

    ai_client     = anthropic.Anthropic(api_key=inp.get("anthropic_key", ""))
    make_webhook  = inp.get("make_webhook_url", "")
    notif_pref    = inp.get("notif_pref", "email")
    notif_contact = inp.get("notification_contact", "")
    current_ctc   = inp.get("current_ctc_lacs", 11.15)
    expected_ctc  = inp.get("expected_ctc_lacs", 21.0)
    notice_days   = inp.get("notice_period_days", 30)
    alt_titles    = inp.get("alt_titles", [])

    results = {
        "date":              datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user_email":        inp.get("user_email", naukri_email),
        "jobs_found":        0,
        "jobs_matched":      0,
        "jobs_applied":      0,
        "jobs_skipped":      0,
        "applied_list":      [],
        "skipped_list":      [],
        "hr_invites_found":  0,
        "hr_invites_applied": 0,
        "hr_invites":        [],
        "errors":            [],
    }

    # â”€â”€ Search URL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    search_plans = _build_search_plans(
        target_role=target_role,
        alt_titles=alt_titles,
        locations=locations,
        exp_min=exp_min,
        exp_max=exp_max,
        salary_min=salary_min,
        title_limit=title_limit,
        location_limit=location_limit,
    )

    primary_location = locations[0] if locations else "Pune"
    log.info(f"Target: {target_role} | Primary location: {primary_location} | Exp: {exp_min}-{exp_max} yrs")
    log.info(f"Search breadth: {len(search_plans)} query combination(s), scan cap {max_jobs_scan}, apply cap {max_apply}")
    for plan in search_plans:
        log.info(f"Search plan: {plan['title']} | {plan['location']} | {plan['url']}")

    # â”€â”€ Browser â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async with async_playwright() as pw:
        headless = inp.get("headless", True)  # True = service/scheduled mode, False = debug
        # Use real Chrome (channel="chrome") in headless mode â€” Naukri blocks Playwright Chromium.
        # Falls back to Chromium if Chrome is not installed (headless=False debug mode).
        import shutil
        use_chrome = headless and shutil.which("chrome") or (
            headless and Path("C:/Program Files/Google/Chrome/Application/chrome.exe").exists()
        )
        launch_kwargs = {
            "headless": headless,
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        if use_chrome:
            launch_kwargs["channel"] = "chrome"
            log.info("Using real Chrome (headless) to bypass bot detection")
        browser = await pw.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/133.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
        )
        page = await context.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        logged_in = await _login_naukri(page, naukri_email, naukri_password, results)

        jobs        = []
        hr_invites  = []
        if logged_in:
            # â”€â”€ P1: Check recruiter inbox FIRST (highest priority) â”€â”€â”€â”€â”€â”€â”€â”€â”€
            log.info("Checking Naukri recruiter inbox...")
            hr_invites = await _scrape_recruiter_inbox(page, results)
            results["hr_invites_found"] = len(hr_invites)
            if hr_invites:
                log.info(f"Found {len(hr_invites)} HR invite(s) â€” processing as P1")

            # â”€â”€ P2: Regular job search â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            jobs = await _collect_jobs_for_search_plans(page, search_plans, results, max_jobs_scan)
            results["jobs_found"] = len(jobs)
            log.info(f"Collected {len(jobs)} unique jobs across all search plans")

        # â”€â”€ Process HR invites (P1 â€” always process, no cap) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        for invite in hr_invites:
            matched, reason = _domain_match(ai_client, invite, resume_data, domain_family, alt_titles)
            invite_record = {
                "title":   invite.get("title"),
                "company": invite.get("company"),
                "url":     invite.get("url"),
                "hr_name": invite.get("hr_name", ""),
                "reason":  reason,
                "applied": False,
            }

            if matched:
                tailored = _tailor_resume(ai_client, invite, resume_data)
                applied  = await _apply_job(page, invite, tailored, make_webhook,
                                            notif_contact, notif_pref, current_loc,
                                            is_hr_invite=True, ai_client=ai_client,
                                            current_ctc=current_ctc, expected_ctc=expected_ctc,
                                            notice_days=notice_days)
                invite_record["applied"] = applied
                if applied:
                    results["hr_invites_applied"] += 1
                    log.info(f"HR-INVITE APPLY  {invite.get('title')} @ {invite.get('company')}")
                _notify_hr_invite(make_webhook, invite, applied, notif_contact, notif_pref,
                                  user_email=inp.get("user_email", naukri_email))
            else:
                log.info(f"HR-INVITE SKIP  {invite.get('title')} @ {invite.get('company')} â€” {reason}")

            results["hr_invites"].append(invite_record)
            await asyncio.sleep(random.uniform(2, 4))

        # â”€â”€ Process jobs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        for job in jobs:
            if results["jobs_applied"] >= max_apply:
                break

            matched, reason = _domain_match(ai_client, job, resume_data, domain_family, alt_titles)
            if not matched:
                results["jobs_skipped"] += 1
                results["skipped_list"].append({
                    "title": job.get("title"), "company": job.get("company"), "reason": reason
                })
                log.info(f"SKIP  {job.get('title')} @ {job.get('company')} â€” {reason}")
                continue

            results["jobs_matched"] += 1
            tailored = _tailor_resume(ai_client, job, resume_data)
            applied  = await _apply_job(page, job, tailored, make_webhook,
                                        notif_contact, notif_pref, current_loc,
                                        is_hr_invite=False, ai_client=ai_client,
                                        current_ctc=current_ctc, expected_ctc=expected_ctc,
                                        notice_days=notice_days)

            if applied:
                results["jobs_applied"] += 1
                log.info(f"APPLY {job.get('title')} @ {job.get('company')}")
                results["applied_list"].append({
                    "title": job.get("title"), "company": job.get("company"),
                    "url": job.get("url"), "easy_apply": job.get("is_easy_apply"),
                })

            await asyncio.sleep(random.uniform(2, 4))

        await browser.close()

    # â”€â”€ Save results locally â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    results_file = Path(__file__).parent / "logs" / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # â”€â”€ Sync results to web app (cloud or local) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _sync_results(
        email        = inp.get("user_email", naukri_email),
        results      = results,
        supabase_url = inp.get("supabase_url", ""),
        supabase_key = inp.get("supabase_key", ""),
        sync_url     = inp.get("careeros_sync_url", ""),
    )

    log.info(
        f"Done â€” HR invites: {results['hr_invites_found']} found, "
        f"{results['hr_invites_applied']} applied | "
        f"Jobs: {results['jobs_found']} found, "
        f"{results['jobs_matched']} matched, "
        f"{results['jobs_applied']} applied"
    )

    # â”€â”€ Push notification via ntfy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ntfy_topic = _ntfy_topic(inp.get("user_email", naukri_email))
    hr_count   = results.get("hr_invites_applied", 0)
    parts      = [f"Jobs scanned: {results['jobs_found']}",
                  f"Applied: {results['jobs_applied']}"]
    if hr_count:
        parts.insert(0, f"HR invites processed: {hr_count}")
    _ntfy(ntfy_topic, "CareerOS Run Complete", "\n".join(parts),
          priority="low", tags=["white_check_mark"])


# â”€â”€ Login â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def _login_naukri(page, email: str, password: str, results: dict) -> bool:
    login_debug_dir = Path(__file__).parent / "logs"
    login_debug_dir.mkdir(exist_ok=True)

    async def _save_login_debug(prefix: str):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shot_path = login_debug_dir / f"{prefix}_{stamp}.png"
        html_path = login_debug_dir / f"{prefix}_{stamp}.html"
        try:
            await page.screenshot(path=str(shot_path), full_page=True)
        except Exception as shot_err:
            log.warning(f"Could not save login screenshot: {shot_err}")
        try:
            html_path.write_text(await page.content(), encoding="utf-8")
        except Exception as html_err:
            log.warning(f"Could not save login HTML dump: {html_err}")
        return shot_path, html_path

    try:
        log.info("Opening Naukri login page...")
        await page.goto("https://www.naukri.com/nlogin/login",
                        wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(random.randint(2000, 3000))

        log.info("Filling email...")
        await page.fill("#usernameField", email, timeout=10000)
        await page.wait_for_timeout(random.randint(400, 700))

        log.info("Filling password...")
        await page.fill("#passwordField", password, timeout=5000)
        await page.wait_for_timeout(random.randint(400, 700))

        log.info("Clicking Login...")
        await page.click("button:has-text('Login')", timeout=5000)

        login_success_selectors = [
            "div.nI-gNb-drawer",
            "div.view-profile-wrapper",
            "a[href*='mnjuser/profile']",
            "a[title*='View profile' i]",
            "a[href*='/mnjuser/homepage']",
        ]
        login_issue_selectors = [
            "iframe[title*='captcha' i]",
            "iframe[src*='captcha']",
            "div.captcha",
            "div.server-err",
            "div.formError",
            "span.error",
            "div[class*='error']",
            "input[autocomplete='one-time-code']",
            "input[name*='otp' i]",
        ]

        for _ in range(15):
            await page.wait_for_timeout(1000)
            current_url = (page.url or "").lower()
            if "nlogin" not in current_url and "login" not in current_url:
                log.info(f"Login successful via URL change - {page.url}")
                return True

            for sel in login_success_selectors:
                try:
                    if await page.locator(sel).first.is_visible(timeout=250):
                        log.info(f"Login successful via selector {sel} - {page.url}")
                        return True
                except Exception:
                    continue

        issue_text = ""
        for sel in login_issue_selectors:
            try:
                locator = page.locator(sel).first
                if await locator.is_visible(timeout=250):
                    try:
                        issue_text = (await locator.inner_text(timeout=500)).strip()
                    except Exception:
                        issue_text = sel
                    break
            except Exception:
                continue

        shot_path, html_path = await _save_login_debug("login_failure")
        message = f"Login failed - still on login page: {page.url}"
        if issue_text:
            message += f" | issue: {issue_text[:200]}"
        message += f" | screenshot: {shot_path.name} | html: {html_path.name}"
        log.error(message)
        results["errors"].append(message)
        return False

    except Exception as e:
        shot_path, html_path = await _save_login_debug("login_error")
        message = f"Login error: {str(e)[:200]} | screenshot: {shot_path.name} | html: {html_path.name}"
        log.error(message)
        results["errors"].append(message)
        return False

def _slugify_search_term(value: str) -> str:
    cleaned = " ".join((value or "").strip().lower().split())
    return quote_plus(cleaned.replace("/", " ")).replace("+", "-")


def _build_search_url(title: str, location: str, exp_min: int, exp_max: int, salary_min: int) -> str:
    title_slug = _slugify_search_term(title)
    location_slug = _slugify_search_term(location or "india")
    url = (
        f"https://www.naukri.com/{title_slug}-jobs-in-{location_slug}"
        f"?experienceMin={exp_min}&experienceMax={exp_max}"
    )
    if salary_min:
        url += f"&salary={int(salary_min) * 100000}"
    return url


def _build_search_plans(target_role: str, alt_titles: list, locations: list, exp_min: int, exp_max: int,
                        salary_min: int, title_limit: int, location_limit: int) -> list:
    seen_titles = set()
    ordered_titles = []
    for title in [target_role] + [t for t in alt_titles if t]:
        title = (title or "").strip()
        if not title:
            continue
        key = title.lower()
        if key not in seen_titles:
            seen_titles.add(key)
            ordered_titles.append(title)
    ordered_titles = ordered_titles[:title_limit]

    seen_locations = set()
    ordered_locations = []
    for location in locations or ["Remote"]:
        location = (location or "").strip()
        if not location:
            continue
        key = location.lower()
        if key not in seen_locations:
            seen_locations.add(key)
            ordered_locations.append(location)
    ordered_locations = ordered_locations[:location_limit] or ["Remote"]

    plans = []
    seen_urls = set()
    for title in ordered_titles:
        for location in ordered_locations:
            url = _build_search_url(title, location, exp_min, exp_max, salary_min)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            plans.append({"title": title, "location": location, "url": url})
    return plans


async def _collect_jobs_for_search_plans(page, search_plans: list, results: dict, max_jobs_to_scan: int) -> list:
    jobs = []
    seen_jobs = set()
    for plan in search_plans:
        if len(jobs) >= max_jobs_to_scan:
            break
        remaining = max_jobs_to_scan - len(jobs)
        plan_jobs = await _scrape_job_listings(page, plan["url"], results, seen_jobs=seen_jobs, limit=min(remaining, 25))
        for job in plan_jobs:
            job.setdefault("search_title", plan["title"])
            job.setdefault("search_location", plan["location"])
            jobs.append(job)
            if len(jobs) >= max_jobs_to_scan:
                break
    return jobs

async def _scrape_job_listings(page, search_url: str, results: dict, seen_jobs=None, limit: int = 25) -> list:
    jobs = []
    seen_jobs = seen_jobs if seen_jobs is not None else set()
    try:
        log.info(f"Navigating to search URL...")
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(random.randint(4000, 5000))

        cards = await page.query_selector_all(
            "div.srp-jobtuple-wrapper, div.cust-job-tuple, "
            "article.jobTuple, div.jobTuple, div[data-job-id]"
        )
        log.info(f"Found {len(cards)} job cards")

        for card in cards[:40]:
            if len(jobs) >= limit:
                break
            try:
                title_el   = await card.query_selector("a.title, a[class*='title']")
                company_el = await card.query_selector("a.comp-name, a[class*='comp-name']")
                desc_el    = await card.query_selector("span.job-desc, ul.tags-gt, div[class*='desc']")
                apply_el   = await card.query_selector("button[class*='apply'], a[class*='apply']")
                meta_el    = await card.query_selector("span.job-post-day, span[class*='posting']")

                title   = (await title_el.inner_text()).strip()   if title_el   else ""
                company = (await company_el.inner_text()).strip() if company_el else ""
                desc    = (await desc_el.inner_text()).strip()     if desc_el    else ""
                url     = await title_el.get_attribute("href")    if title_el   else ""
                meta    = (await meta_el.inner_text()).strip()     if meta_el else ""

                if not title:
                    continue

                company = company.split("\n")[0].strip()
                dedupe_key = (title.lower(), company.lower())
                if dedupe_key in seen_jobs:
                    continue
                seen_jobs.add(dedupe_key)

                apply_text    = (await apply_el.inner_text()).lower() if apply_el else ""
                is_easy_apply = "apply" in apply_text and "external" not in apply_text

                jobs.append({
                    "title": title, "company": company,
                    "description": desc, "url": url,
                    "is_easy_apply": is_easy_apply,
                    "posted_meta": meta,
                })
                log.info(f"  Job: {title} @ {company}")

            except Exception:
                continue

    except Exception as e:
        log.error(f"Scrape error: {e}")
        results["errors"].append(f"Scrape error: {str(e)[:200]}")

    return jobs


# â”€â”€ Domain match (research-backed Indian job market scorer) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _domain_match(client, job, resume_data, domain_family, alt_titles=None):
    title   = job.get("title", "")
    company = job.get("company", "")
    jd      = job.get("description", "")
    age     = job.get("age_days", 0)

    target_title  = resume_data.get("target_title", "")
    alt_titles    = alt_titles or []
    skills        = ", ".join(resume_data.get("ats_keywords", [])[:15])
    experience    = resume_data.get("experience", [])
    total_exp     = sum(_parse_years(e.get("period", "")) for e in experience)
    total_exp     = max(1, min(total_exp, 25))
    summary       = resume_data.get("summary", "")
    all_titles    = ", ".join([target_title] + alt_titles) if alt_titles else target_title

    prompt = f"""You are a senior Indian recruiter. Decide: should this candidate apply to this job?

CANDIDATE:
- Primary Target Role: {target_title}
- Also acceptable roles: {", ".join(alt_titles) if alt_titles else "same as above"}
- Domain: {domain_family}
- Experience: {total_exp} years
- Skills: {skills}
- Background: {summary[:300]}

HARD REJECT â€” answer false if ANY applies:
- Job age > 21 days (stale posting)
- Seniority wrong: VP/Director/Head/C-Level OR Junior/Fresher/0-2 yrs required
- Wrong function: Software Engineer, Developer, QA, HR, Finance, Marketing, Sales, Data Scientist
- Domain completely irrelevant AND explicitly required (capital markets, pharma clinical, etc.)
- Location is fixed WFO in a city far from candidate's preferred locations

APPLY if the role matches ANY of the candidate's acceptable titles or is a natural adjacent role
(Project Manager, Program Manager, IT Manager, Delivery Manager, Technical Lead with management scope).

MATCH SIGNALS:
- Title is any of: {all_titles} or a very close variant
- Domain overlaps (same industry or adjacent â€” enterprise IT, automotive, product, SaaS all OK)
- Experience band fits (within 2-3 years)
- Program/project delivery, stakeholder management, or Agile skills appear in JD

JOB:
Title: {title}
Company: {company}
Age: {age} days old
Description: {jd[:800]}

Reply ONLY JSON (no markdown):
{{"match": true/false, "score": <0-100>, "reason": "<one line â€” specific factor>"}}"""

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
        raw  = resp.content[0].text
        data = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
        score = data.get("score", 0)
        match = data.get("match", False) and score >= 55
        return match, f"[{score}/100] {data.get('reason', '')}"
    except Exception as e:
        return False, f"Error: {e}"


# â”€â”€ Tailor resume â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _tailor_resume(client, job, resume_data):
    prompt = f"""Job: {job.get('title')} at {job.get('company')}
JD: {job.get('description', '')[:600]}
Base summary: {resume_data.get('summary', '')}
Base keywords: {', '.join(resume_data.get('ats_keywords', [])[:12])}
Rewrite summary for this job. Same facts, different emphasis.
Reply ONLY JSON: {{"tailored_summary": "...", "tailored_keywords": ["kw1",...]}}"""
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        raw      = resp.content[0].text
        tailored = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
        result   = dict(resume_data)
        result["summary"]      = tailored.get("tailored_summary", resume_data.get("summary"))
        result["ats_keywords"] = tailored.get("tailored_keywords", resume_data.get("ats_keywords"))
        return result
    except Exception:
        return resume_data


# â”€â”€ Recruiter inbox scraper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def _scrape_recruiter_inbox(page, results: dict) -> list:
    """
    Scrape Naukri's recruiter activities / messages section for HR invites.
    Returns list of invite dicts (same shape as job listings).
    """
    invites = []

    # â”€â”€ Primary: NVites dedicated inbox page â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # URL:     https://www.naukri.com/mnjuser/inbox
    # Card:    div.card.inbox-company-card
    # Title:   span.title  (or span.ellipsis.title)
    # Company: span.comp-name  (may be "Hiring for X" â€” strip that prefix)
    # Recruiter: span.posted-by-txt  (e.g. "Posted by I Square Tek")
    # Date:    span.date-time-wrap
    # Key:     data-mailid attribute (used to re-find the card for applying)
    # Note:    Cards have no <a href> â€” apply by clicking card â†’ Apply button in panel
    try:
        await page.goto("https://www.naukri.com/mnjuser/inbox",
                        wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(random.randint(2500, 3500))

        cards = await page.query_selector_all("div.card.inbox-company-card")
        log.info(f"Recruiter inbox: {len(cards)} NVite cards at /mnjuser/inbox")

        import re as _re
        for card in cards[:10]:
            try:
                mail_id   = await card.get_attribute("data-mailid") or ""
                title_el  = await card.query_selector("span.title, span.ellipsis.title")
                comp_el   = await card.query_selector("span.comp-name")
                recr_el   = await card.query_selector("span.posted-by-txt")
                date_el   = await card.query_selector("span.date-time-wrap")

                title     = (await title_el.inner_text()).strip() if title_el else ""
                company   = (await comp_el.inner_text()).strip()  if comp_el  else ""
                recruiter = (await recr_el.inner_text()).strip()  if recr_el  else ""
                date_str  = (await date_el.inner_text()).strip()  if date_el  else ""

                # Clean "Hiring for " prefix and "Posted by " prefix
                company   = _re.sub(r"^Hiring for\s*", "", company).strip()
                recruiter = _re.sub(r"^Posted by\s*", "", recruiter).strip()

                # Estimate age in days from date string (e.g. "4 Mar", "26 Feb")
                age_days = 0
                try:
                    from datetime import datetime as _dt
                    parsed = _dt.strptime(f"{date_str} {_dt.now().year}", "%d %b %Y")
                    age_days = (datetime.now() - parsed).days
                except Exception:
                    pass

                if not title:
                    continue

                invites.append({
                    "title":         title,
                    "company":       company or recruiter,
                    "hr_name":       recruiter,
                    "description":   "",
                    "url":           f"https://www.naukri.com/mnjuser/inbox#{mail_id}",
                    "mail_id":       mail_id,
                    "is_easy_apply": True,
                    "source":        "hr_invite",
                    "age_days":      age_days,
                })
                log.info(f"  NVite: {title} @ {company} | by {recruiter} | {date_str}")
            except Exception as e:
                log.warning(f"  NVite card parse error: {e}")
                continue

    except Exception as e:
        log.warning(f"NVites inbox check failed: {e}")
        results["errors"].append(f"NVites inbox error: {str(e)[:150]}")

    # â”€â”€ Fallback: homepage power-invite-card widget â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if not invites:
        try:
            await page.goto("https://www.naukri.com/mnjuser/homepage",
                            wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(random.randint(2000, 3000))

            for card in await page.query_selector_all("div.power-invite-card")[:5]:
                try:
                    title_el = await card.query_selector("h2.comp-name, h2")
                    comp_el  = await card.query_selector("h4.rmj-title, h4")
                    title    = (await title_el.inner_text()).strip() if title_el else ""
                    company  = (await comp_el.inner_text()).strip()  if comp_el  else ""
                    if not title:
                        continue
                    invites.append({
                        "title":    title,
                        "company":  company.replace("Hiring for ", "").strip(),
                        "hr_name":  "",
                        "description": "",
                        "url":      "https://www.naukri.com/mnjuser/homepage",
                        "mail_id":  "",
                        "is_easy_apply": True,
                        "source":   "hr_invite",
                        "age_days": 0,
                    })
                    log.info(f"  Power-invite: {title} @ {company}")
                except Exception:
                    continue
        except Exception as e:
            log.warning(f"Homepage invite fallback failed: {e}")

    return invites


# â”€â”€ HR invite instant notification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _notify_hr_invite(make_webhook: str, invite: dict, applied: bool,
                      contact: str, notif_pref: str, user_email: str = ""):
    """Instant push notification (ntfy) when an HR invite is detected."""
    topic  = _ntfy_topic(user_email or contact)
    status = "Auto-applied by CareerOS" if applied else "Reviewed â€” not a strong match"
    _ntfy(
        topic     = topic,
        title     = f"HR Invite â€” {invite.get('company', 'Unknown')}",
        message   = (
            f"Role: {invite.get('title', 'Unknown')}\n"
            f"HR: {invite.get('hr_name', 'Unknown')}\n"
            f"Status: {status}"
        ),
        priority  = "urgent",
        tags      = ["fire", "briefcase"],
        click_url = invite.get("url", ""),
    )
    log.info(f"ntfy notification sent for HR invite from {invite.get('company')}")


# â”€â”€ AI-powered chatbot question answering â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _ai_chatbot_answer(client, question: str, options: list, resume_data: dict,
                        current_ctc: float, expected_ctc: float,
                        notice_days: int, location: str) -> str:
    """Use Claude Haiku to answer a Naukri chatbot apply question."""
    opts_str = "\n".join(f"- {o}" for o in options) if options else "(free text â€” short answer)"

    prompt = f"""You are filling a Naukri job application chatbot for this candidate:
- Experience: 8 years in IT program/project management
- Current CTC: {current_ctc} Lacs per annum
- Expected CTC: {expected_ctc} Lacs per annum
- Notice period: {notice_days} days
- Current location: {location}
- Target role: {resume_data.get("target_title", "Technical Program Manager")}
- Skills: {", ".join(resume_data.get("ats_keywords", [])[:10])}
- Background: {resume_data.get("summary", "")[:200]}

CHATBOT QUESTION: "{question}"

{"AVAILABLE OPTIONS (pick ONE):" if options else ""}
{opts_str}

Rules:
- For "current CTC" â†’ reply "{current_ctc}"
- For "expected CTC" â†’ reply "{expected_ctc}"
- For "notice period" or "joining time" â†’ reply "{notice_days}"
- For "years of experience": pick the highest option that is â‰¤ 8; if all options exceed 8 pick lowest; if no numeric option pick "Skip this question"
- For location â†’ reply "{location}"
- For yes/no willingness/interest questions â†’ reply "Yes"
- For "residing in" location questions â†’ reply "Yes"
- If question asks about a specific tech skill the candidate lacks (e.g. Java, .NET, Oracle, Python, Coding): reply "0" for free text OR pick "Skip this question" if available
- For years-of-experience free text: reply with a single number like "5" or "8" (no "years" suffix)
- For options list: reply with the EXACT option text (copy exactly, case-sensitive)
- For free text: reply with a SHORT, direct answer â€” single word or number preferred

Reply with ONLY the answer, no explanation."""
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception:
        # Heuristic fallback
        q = question.lower()
        if "current ctc" in q:       return str(current_ctc)
        if "expected ctc" in q:      return str(expected_ctc)
        if "notice" in q or "joining" in q: return str(notice_days)
        if "location" in q or "city" in q:  return location
        if options:
            # Pick highest numeric non-skip option
            nums = []
            for o in options:
                try: nums.append((float(o.split()[0]), o))
                except: pass
            if nums:
                return max(n for n in nums if n[0] <= 8)[1] if any(n[0] <= 8 for n in nums) else nums[0][1]
            # Pick any non-skip
            for o in options:
                if "skip" not in o.lower(): return o
            return options[-1]
        return "8"


# â”€â”€ Naukri chatbot apply handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def _handle_chatbot_apply(page, ai_client, resume_data: dict, job_title: str = "",
                                 current_ctc: float = 11.15, expected_ctc: float = 21.0,
                                 notice_days: int = 30, current_loc: str = "Mumbai") -> bool:
    """
    Handle Naukri's post-Apply chatbot panel.
    After clicking Apply, Naukri may open a chat sidebar with recruiter questions.
    Supports text input (contenteditable div) and radio button questions.
    Returns True if application submitted successfully.
    """
    # Wait for chatbot drawer to become VISIBLE (element may be in DOM but hidden)
    chatbot_visible = False
    for sel in ["div.chatbot_Drawer", "._chatBotContainer", "[class*='chatbot_Drawer']"]:
        try:
            await page.wait_for_selector(sel, state="visible", timeout=8000)
            chatbot_visible = True
            break
        except Exception:
            continue
    if not chatbot_visible:
        try:
            from pathlib import Path as _Path
            _ss_dir = _Path(__file__).parent / "logs"
            _ss_dir.mkdir(exist_ok=True)
            await page.screenshot(path=str(_ss_dir / f"chatbot_miss_{job_title[:20].replace(' ','_')}.png"))
            log.info(f"Chatbot not found â€” screenshot saved to logs/")
        except Exception:
            pass
        return False

    log.info(f"Chatbot panel detected for: {job_title}")
    await page.wait_for_timeout(1500)

    for round_num in range(15):
        await page.wait_for_timeout(1500)

        # â”€â”€ Check for success â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        try:
            btn = await page.query_selector("button[class*='apply-button']")
            if btn and "applied" in (await btn.inner_text()).lower():
                log.info("Chatbot apply confirmed â€” button shows Applied")
                return True
        except Exception:
            pass
        try:
            msgs = await page.query_selector_all("li.botItem.chatbot_ListItem .botMsg span")
            if msgs:
                last = (await msgs[-1].inner_text()).lower()
                if any(w in last for w in ["applied", "success", "thank you for apply", "submitted"]):
                    log.info(f"Chatbot success: '{last[:60]}'")
                    return True
        except Exception:
            pass

        # â”€â”€ Get current question â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        question_text = ""
        try:
            msgs = await page.query_selector_all("li.botItem.chatbot_ListItem .botMsg span")
            if msgs:
                question_text = (await msgs[-1].inner_text()).strip()
        except Exception:
            pass

        if not question_text:
            log.debug(f"Chatbot round {round_num}: no question, assuming done")
            break

        log.info(f"Chatbot Q{round_num}: '{question_text[:80]}'")

        # â”€â”€ Radio button question â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        radio_options = await page.query_selector_all("input.ssrc__radio[type='radio']")
        if radio_options:
            option_values = []
            for radio in radio_options:
                val = await radio.get_attribute("value") or await radio.get_attribute("id") or ""
                if val:
                    option_values.append(val)

            log.info(f"Radio options: {option_values}")
            chosen = _ai_chatbot_answer(ai_client, question_text, option_values, resume_data,
                                        current_ctc, expected_ctc, notice_days, current_loc)
            log.info(f"AI chose: '{chosen}'")

            clicked = False
            # Exact match first
            for opt_val in option_values:
                if chosen.strip().lower() == opt_val.strip().lower():
                    try:
                        label = await page.query_selector(f'label[for="{opt_val}"]')
                        if label:
                            await label.click()
                            clicked = True
                            log.info(f"Clicked radio: '{opt_val}'")
                            break
                    except Exception:
                        pass

            # Fuzzy match
            if not clicked:
                for opt_val in option_values:
                    words = [w for w in opt_val.lower().split() if len(w) > 2]
                    if any(w in chosen.lower() for w in words):
                        try:
                            label = await page.query_selector(f'label[for="{opt_val}"]')
                            if label:
                                await label.click()
                                clicked = True
                                log.info(f"Fuzzy-clicked radio: '{opt_val}'")
                                break
                        except Exception:
                            pass

            # Fallback: Skip
            if not clicked:
                try:
                    skip = await page.query_selector('label[for="Skip this question"]')
                    if skip:
                        await skip.click()
                        clicked = True
                        log.info("Fallback: clicked Skip this question")
                except Exception:
                    pass

            if not clicked:
                log.warning("Could not click any radio option, stopping")
                break

            await page.wait_for_timeout(600)

        else:
            # â”€â”€ Text input question â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            chat_input = await page.query_selector("div.textArea[contenteditable='true']")
            if not chat_input:
                log.warning(f"Round {round_num}: no radio and no text input")
                break

            answer = _ai_chatbot_answer(ai_client, question_text, [], resume_data,
                                        current_ctc, expected_ctc, notice_days, current_loc)
            log.info(f"Chatbot text answer: '{answer}'")
            await chat_input.click()
            await page.evaluate("document.querySelector(\"div.textArea[contenteditable='true']\").textContent = ''")
            await page.keyboard.type(answer)
            await page.wait_for_timeout(500)

        # â”€â”€ Click Save (it's a div.sendMsg, not a button) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        saved = False
        for sel in ["div.sendMsg", ".sendMsg"]:
            try:
                save_div = await page.query_selector(sel)
                if save_div and await save_div.is_visible():
                    await save_div.click()
                    saved = True
                    log.info("Clicked Save (div.sendMsg)")
                    await page.wait_for_timeout(2000)
                    break
            except Exception:
                pass

        if not saved:
            log.warning("sendMsg Save div not found/not clickable")
            break

    # Final applied check â€” wait for Naukri to update state after last Save
    await page.wait_for_timeout(4000)
    try:
        btn = await page.query_selector("button[class*='apply-button']")
        if btn and "applied" in (await btn.inner_text()).lower():
            log.info("Chatbot apply confirmed â€” Apply button changed to Applied")
            return True
    except Exception:
        pass
    # Also check page body for confirmation text (navigated to success page)
    try:
        body = await page.evaluate("document.body.innerText")
        if any(w in body.lower() for w in ["applied to", "application submitted", "application sent", "you have applied"]):
            log.info("Chatbot apply confirmed â€” confirmation text found on page")
            return True
    except Exception:
        pass
    return False


# â”€â”€ Fill Naukri Easy Apply modal (location / CTC / notice period) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def _handle_easy_apply_modal(page, current_loc: str = "Mumbai"):
    """
    After clicking Apply/Easy Apply on Naukri, a modal may appear asking for:
    - Current location (typeahead)
    - Current CTC / Expected CTC (inputs)
    - Notice period (dropdown)

    Fills what it can find and ignores fields that aren't present.
    Returns True if any modal field was found (modal was present).
    """
    modal_found = False
    try:
        await page.wait_for_timeout(1000)

        # â”€â”€ Current location typeahead â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        loc_selectors = [
            "input[placeholder*='current city' i]",
            "input[placeholder*='Current City' i]",
            "input[placeholder*='current location' i]",
            "input[id*='currentCity' i]",
            "input[id*='currentLocation' i]",
            "[class*='currentCity'] input",
            "[class*='currentLocation'] input",
            "[class*='location'] input[type='text']",
        ]
        for sel in loc_selectors:
            try:
                loc_input = await page.query_selector(sel)
                if loc_input and await loc_input.is_visible():
                    modal_found = True
                    await loc_input.triple_click()
                    await loc_input.type(current_loc, delay=80)
                    await page.wait_for_timeout(1200)
                    suggestion_selectors = [
                        "[class*='suggestItem']",
                        "[class*='suggestion-item']",
                        "[class*='autocomplete'] li",
                        "[class*='dropdown'] li",
                        "ul.suggestions li",
                        "[role='option']",
                    ]
                    clicked = False
                    for ssel in suggestion_selectors:
                        try:
                            sug = await page.query_selector(ssel)
                            if sug and await sug.is_visible():
                                await sug.click()
                                clicked = True
                                break
                        except Exception:
                            continue
                    if not clicked:
                        await loc_input.press("Enter")
                    log.info(f"Location filled: {current_loc}")
                    await page.wait_for_timeout(600)
                    break
            except Exception:
                continue

        # â”€â”€ Current CTC â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        ctc_selectors = [
            "input[placeholder*='current ctc' i]",
            "input[placeholder*='Current CTC' i]",
            "input[id*='currentCtc' i]",
            "input[id*='current_ctc' i]",
            "[class*='currentCtc'] input",
            "input[name*='currentCtc' i]",
        ]
        for sel in ctc_selectors:
            try:
                ctc_input = await page.query_selector(sel)
                if ctc_input and await ctc_input.is_visible():
                    modal_found = True
                    await ctc_input.triple_click()
                    await ctc_input.type("1500000", delay=60)   # 15 LPA default
                    log.info("Current CTC filled: 15 LPA")
                    await page.wait_for_timeout(400)
                    break
            except Exception:
                continue

        # â”€â”€ Expected CTC â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        ectc_selectors = [
            "input[placeholder*='expected ctc' i]",
            "input[placeholder*='Expected CTC' i]",
            "input[id*='expectedCtc' i]",
            "input[id*='expected_ctc' i]",
            "[class*='expectedCtc'] input",
            "input[name*='expectedCtc' i]",
        ]
        for sel in ectc_selectors:
            try:
                ectc_input = await page.query_selector(sel)
                if ectc_input and await ectc_input.is_visible():
                    modal_found = True
                    await ectc_input.triple_click()
                    await ectc_input.type("2000000", delay=60)  # 20 LPA default
                    log.info("Expected CTC filled: 20 LPA")
                    await page.wait_for_timeout(400)
                    break
            except Exception:
                continue

        # â”€â”€ Notice period dropdown â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        notice_selectors = [
            "select[id*='notice' i]",
            "select[name*='notice' i]",
            "[class*='noticePeriod'] select",
            "[class*='notice-period'] select",
        ]
        for sel in notice_selectors:
            try:
                notice_el = await page.query_selector(sel)
                if notice_el and await notice_el.is_visible():
                    modal_found = True
                    await notice_el.select_option(index=1)
                    log.info("Notice period set")
                    break
            except Exception:
                continue

    except Exception as e:
        log.debug(f"Easy Apply modal handler: {e}")

    return modal_found


# â”€â”€ Apply: NVites inbox flow (click card â†’ Apply button in detail panel) â”€â”€â”€â”€â”€â”€â”€
async def _apply_inbox_invite(page, job, make_webhook, notif_contact, notif_pref,
                              current_loc: str = "Mumbai", ai_client=None,
                              current_ctc: float = 11.15, expected_ctc: float = 21.0,
                              notice_days: int = 30):
    """
    Apply to a Naukri NVite by clicking the inbox card and then the Apply button.
    Handles chatbot apply panel with AI-powered question answering.
    """
    title   = job.get("title", "Unknown")
    company = job.get("company", "Unknown")
    mail_id = job.get("mail_id", "")
    resume_data = job.get("resume_data", {})

    try:
        await page.goto("https://www.naukri.com/mnjuser/inbox",
                        wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(random.randint(2000, 3000))

        # Find the specific card by data-mailid
        card = await page.query_selector(f"div.card.inbox-company-card[data-mailid='{mail_id}']")
        if not card:
            cards = await page.query_selector_all("div.card.inbox-company-card")
            if cards:
                card = cards[0]
                log.info(f"mail_id not matched, using first inbox card for {title}")
            else:
                log.warning(f"No inbox cards found for {title} @ {company}")
                return False

        await card.click()
        await page.wait_for_timeout(random.randint(1500, 2500))

        apply_selectors = [
            "button:has-text('Apply Now')",
            "button:has-text('Easy Apply')",
            "button:has-text('Apply')",
            "[class*='apply-btn']",
            "[class*='applyBtn']",
        ]
        apply_btn = None
        for sel in apply_selectors:
            try:
                apply_btn = await page.query_selector(sel)
                if apply_btn:
                    btn_text = (await apply_btn.inner_text()).strip().lower()
                    if "applied" in btn_text:
                        log.info(f"Already applied (inbox) â€” {title} @ {company}")
                        return False
                    break
            except Exception:
                continue

        if not apply_btn:
            log.warning(f"Apply button not found in inbox panel â€” {title} @ {company}")
            return False

        await apply_btn.click()
        await page.wait_for_timeout(random.randint(1500, 2500))

        # Handle chatbot apply panel
        submitted = False
        if ai_client:
            submitted = await _handle_chatbot_apply(
                page, ai_client, resume_data, job_title=f"{title} @ {company}",
                current_ctc=current_ctc, expected_ctc=expected_ctc,
                notice_days=notice_days, current_loc=current_loc,
            )
        if not submitted:
            try:
                btn = await page.query_selector("button[class*='apply-button']")
                if btn and "applied" in (await btn.inner_text()).lower():
                    submitted = True
            except Exception:
                pass

        if not submitted:
            log.warning(f"NVite submit not confirmed â€” {title} @ {company}")
            return False

        log.info(f"NVite applied (inbox flow) â€” {title} @ {company}")

        if make_webhook:
            try:
                requests.post(make_webhook, json={
                    "type": "hr_invite_apply",
                    "job_title": title, "company": company,
                    "mail_id": mail_id, "contact": notif_contact,
                    "notif_pref": notif_pref, "is_hr_invite": True,
                }, timeout=5)
            except Exception:
                pass

        return True

    except Exception as e:
        log.warning(f"Inbox apply failed for {title} @ {company}: {e}")
        return False


# â”€â”€ Apply â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def _apply_job(page, job, resume_data, make_webhook, notif_contact, notif_pref,
                     current_loc: str = "Mumbai", is_hr_invite: bool = False,
                     ai_client=None, current_ctc: float = 11.15,
                     expected_ctc: float = 21.0, notice_days: int = 30):
    """
    Navigate to the job URL and click Apply on Naukri.
    Handles Naukri's chatbot-style apply panel (questions answered by Claude AI).
    Falls back gracefully if apply button not found or already applied.
    """
    url     = job.get("url", "")
    title   = job.get("title", "Unknown")
    company = job.get("company", "Unknown")

    try:
        if not url:
            log.warning(f"No URL for {title} @ {company} â€” skipping apply")
            return False

        # â”€â”€ Special flow: NVites inbox invites â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        mail_id = job.get("mail_id", "")
        if is_hr_invite and mail_id and "mnjuser/inbox" in url:
            return await _apply_inbox_invite(page, job, make_webhook, notif_contact, notif_pref,
                                             current_loc, ai_client=ai_client,
                                             current_ctc=current_ctc, expected_ctc=expected_ctc,
                                             notice_days=notice_days)

        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(random.randint(2000, 3000))

        # â”€â”€ Step 1: Find and click the main Apply button â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        apply_selectors = [
            "button[class*='apply-button']",
            "a[class*='apply-button']",
            ".applyButton",
            "button.apply-button",
            "button:has-text('Easy Apply')",
            "button:has-text('Apply Now')",
            "button:has-text('Apply')",
            "#apply-button",
        ]
        apply_btn = None
        for sel in apply_selectors:
            try:
                apply_btn = await page.query_selector(sel)
                if apply_btn:
                    is_disabled = await apply_btn.get_attribute("disabled")
                    btn_text = (await apply_btn.inner_text()).strip().lower()
                    if is_disabled is not None or "applied" in btn_text:
                        log.info(f"Already applied / disabled â€” {title} @ {company}")
                        return False
                    break
            except Exception:
                continue

        if not apply_btn:
            log.warning(f"Apply button not found â€” {title} @ {company}")
            return False

        log.info(f"Attempting apply: {title} @ {company}")
        await apply_btn.click()
        await page.wait_for_timeout(random.randint(3000, 4000))  # chatbot needs time to init

        # â”€â”€ Step 2: Handle chatbot apply panel (AI-powered) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if ai_client:
            submitted = await _handle_chatbot_apply(
                page, ai_client, resume_data, job_title=f"{title} @ {company}",
                current_ctc=current_ctc, expected_ctc=expected_ctc,
                notice_days=notice_days, current_loc=current_loc,
            )
            if submitted:
                log.info(f"Chatbot apply done â€” {title} @ {company}")
            else:
                # Chatbot didn't appear or didn't submit â€” check direct-apply or page confirmation
                try:
                    btn = await page.query_selector("button[class*='apply-button']")
                    if btn and "applied" in (await btn.inner_text()).lower():
                        submitted = True
                        log.info(f"Direct apply confirmed â€” {title} @ {company}")
                except Exception:
                    pass
                if not submitted:
                    try:
                        body = await page.evaluate("document.body.innerText")
                        if any(w in body.lower() for w in ["applied to", "application submitted", "you have applied"]):
                            submitted = True
                            log.info(f"Direct apply confirmed via page text â€” {title} @ {company}")
                    except Exception:
                        pass
        else:
            submitted = False

        if not submitted:
            log.warning(f"Apply not confirmed â€” {title} @ {company}")
            return False

        # â”€â”€ Step 3: Webhook notification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if make_webhook:
            try:
                requests.post(make_webhook, json={
                    "type":         "hr_invite_apply" if is_hr_invite else "easy_apply",
                    "job_title":    title,
                    "company":      company,
                    "job_url":      url,
                    "contact":      notif_contact,
                    "notif_pref":   notif_pref,
                    "is_hr_invite": is_hr_invite,
                }, timeout=5)
            except Exception:
                pass

        return True

    except Exception as e:
        log.warning(f"Apply failed for {title} @ {company}: {e}")
        return False


# â”€â”€ Utility â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _parse_years(period: str) -> int:
    import re
    years = re.findall(r"\b(20\d{2}|19\d{2})\b", period)
    if len(years) >= 2:
        return int(years[-1]) - int(years[0])
    if len(years) == 1:
        return datetime.now().year - int(years[0])
    return 2


if __name__ == "__main__":
    asyncio.run(main())
