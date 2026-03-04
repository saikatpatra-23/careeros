"""
CareerOS Job Applier — Local Runner
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
from cryptography.fernet import Fernet

import anthropic
from playwright.async_api import async_playwright

# ntfy notifications (inline — no CareerOS module import needed in local runner)
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

def _sync_results(email: str, results: dict, sync_url: str = "") -> None:
    """
    Push run results to CareerOS web app.
    Two modes:
      1. sync_url set  → POST to web app API endpoint (cloud deployment)
      2. sync_url empty → try writing to local UserStore (dev / same-machine mode)
    """
    # ── Mode 1: Cloud sync via GET + base64 payload ───────────────────────────
    # sync_url should be: https://app.streamlit.app/api_ingest?token=SECRET&data=
    # We append base64-encoded JSON payload to the URL.
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

    # ── Mode 2: Same-machine local sync ───────────────────────────────────────
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

        log.info(f"Results synced locally → {data_dir}")
    except Exception as e:
        log.warning(f"Local sync failed (non-fatal): {e}")


# ── Config ─────────────────────────────────────────────────────────────────────
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


# ── Entry point ────────────────────────────────────────────────────────────────
async def main():
    LOG_FILE.parent.mkdir(exist_ok=True)

    if not CONFIG_FILE.exists():
        log.error(f"config.json not found at {CONFIG_FILE}")
        return

    with open(CONFIG_FILE, encoding="utf-8") as f:
        inp = json.load(f)

    # ── Decrypt password ───────────────────────────────────────────────────────
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

    # ── Params ─────────────────────────────────────────────────────────────────
    resume_data   = inp.get("resume_data", {})
    target_role   = resume_data.get("target_title", "Business Analyst")
    domain_family = resume_data.get("domain_family", "enterprise_IT")
    locations     = inp.get("preferred_locations", ["Pune"])
    salary_min    = inp.get("salary_min", 0)
    max_apply     = inp.get("max_jobs_per_run", 5)

    exp_years = sum(
        _parse_years(job.get("period", ""))
        for job in resume_data.get("experience", [])
    )
    exp_years = max(1, min(exp_years, 20))

    ai_client     = anthropic.Anthropic(api_key=inp.get("anthropic_key", ""))
    make_webhook  = inp.get("make_webhook_url", "")
    notif_pref    = inp.get("notif_pref", "email")
    notif_contact = inp.get("notification_contact", "")

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

    # ── Search URL ─────────────────────────────────────────────────────────────
    role_slug     = target_role.lower().replace(" ", "-")
    location      = locations[0] if locations else "pune"
    location_slug = location.lower().replace(" ", "-")
    search_url = (
        f"https://www.naukri.com/{role_slug}-jobs-in-{location_slug}"
        f"?experienceMin={max(0, exp_years - 2)}&experienceMax={exp_years + 2}"
    )
    if salary_min:
        search_url += f"&salary={salary_min * 100000}"

    log.info(f"Target: {target_role} | Location: {location} | Exp: {exp_years-2}–{exp_years+2} yrs")
    log.info(f"Search URL: {search_url}")

    # ── Browser ────────────────────────────────────────────────────────────────
    async with async_playwright() as pw:
        headless = inp.get("headless", True)  # True = service/scheduled mode, False = debug
        # Use real Chrome (channel="chrome") in headless mode — Naukri blocks Playwright Chromium.
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
            # ── P1: Check recruiter inbox FIRST (highest priority) ─────────
            log.info("Checking Naukri recruiter inbox...")
            hr_invites = await _scrape_recruiter_inbox(page, results)
            results["hr_invites_found"] = len(hr_invites)
            if hr_invites:
                log.info(f"Found {len(hr_invites)} HR invite(s) — processing as P1")

            # ── P2: Regular job search ─────────────────────────────────────
            jobs = await _scrape_job_listings(page, search_url, results)
            results["jobs_found"] = len(jobs)
            log.info(f"Found {len(jobs)} jobs")

        await browser.close()

    # ── Process HR invites (P1 — always process, no cap) ─────────────────────
    for invite in hr_invites:
        matched, reason = _domain_match(ai_client, invite, resume_data, domain_family)
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
            applied  = await _apply_job(invite, tailored, make_webhook, notif_contact, notif_pref,
                                        is_hr_invite=True)
            invite_record["applied"] = applied
            if applied:
                results["hr_invites_applied"] += 1
                log.info(f"HR-INVITE APPLY  {invite.get('title')} @ {invite.get('company')}")
            # Notify immediately via ntfy (HR invite = P1 = instant notification)
            _notify_hr_invite(make_webhook, invite, applied, notif_contact, notif_pref,
                              user_email=inp.get("user_email", naukri_email))
        else:
            log.info(f"HR-INVITE SKIP  {invite.get('title')} @ {invite.get('company')} — {reason}")

        results["hr_invites"].append(invite_record)
        await asyncio.sleep(random.uniform(2, 4))

    # ── Process jobs ───────────────────────────────────────────────────────────
    for job in jobs:
        if results["jobs_applied"] >= max_apply:
            break

        matched, reason = _domain_match(ai_client, job, resume_data, domain_family)
        if not matched:
            results["jobs_skipped"] += 1
            results["skipped_list"].append({
                "title": job.get("title"), "company": job.get("company"), "reason": reason
            })
            log.info(f"SKIP  {job.get('title')} @ {job.get('company')} — {reason}")
            continue

        results["jobs_matched"] += 1
        tailored = _tailor_resume(ai_client, job, resume_data)
        applied  = await _apply_job(job, tailored, make_webhook, notif_contact, notif_pref,
                                    is_hr_invite=False)

        if applied:
            results["jobs_applied"] += 1
            log.info(f"APPLY {job.get('title')} @ {job.get('company')}")
            results["applied_list"].append({
                "title": job.get("title"), "company": job.get("company"),
                "url": job.get("url"), "easy_apply": job.get("is_easy_apply"),
            })

        await asyncio.sleep(random.uniform(2, 4))

    # ── Save results locally ────────────────────────────────────────────────────
    results_file = Path(__file__).parent / "logs" / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # ── Sync results to web app (cloud or local) ─────────────────────────────────
    _sync_results(
        email    = inp.get("user_email", naukri_email),
        results  = results,
        sync_url = inp.get("careeros_sync_url", ""),
    )

    log.info(
        f"Done — HR invites: {results['hr_invites_found']} found, "
        f"{results['hr_invites_applied']} applied | "
        f"Jobs: {results['jobs_found']} found, "
        f"{results['jobs_matched']} matched, "
        f"{results['jobs_applied']} applied"
    )

    # ── Push notification via ntfy ─────────────────────────────────────────────
    ntfy_topic = _ntfy_topic(inp.get("user_email", naukri_email))
    hr_count   = results.get("hr_invites_applied", 0)
    parts      = [f"Jobs scanned: {results['jobs_found']}",
                  f"Applied: {results['jobs_applied']}"]
    if hr_count:
        parts.insert(0, f"HR invites processed: {hr_count}")
    _ntfy(ntfy_topic, "CareerOS Run Complete", "\n".join(parts),
          priority="low", tags=["white_check_mark"])


# ── Login ──────────────────────────────────────────────────────────────────────
async def _login_naukri(page, email: str, password: str, results: dict) -> bool:
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
        await page.wait_for_load_state("networkidle", timeout=20000)
        await page.wait_for_timeout(2000)

        if "nlogin" not in page.url.lower():
            log.info(f"✅ Login successful — {page.url}")
            return True
        else:
            log.error(f"Login failed — still on login page: {page.url}")
            results["errors"].append(f"Login failed — URL: {page.url}")
            return False

    except Exception as e:
        log.error(f"Login error: {e}")
        results["errors"].append(f"Login error: {str(e)[:200]}")
        return False


# ── Scrape ─────────────────────────────────────────────────────────────────────
async def _scrape_job_listings(page, search_url: str, results: dict) -> list:
    jobs = []
    try:
        log.info(f"Navigating to search URL...")
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(random.randint(4000, 5000))  # SPA needs extra render time

        cards = await page.query_selector_all(
            "div.srp-jobtuple-wrapper, div.cust-job-tuple, "
            "article.jobTuple, div.jobTuple, div[data-job-id]"
        )
        log.info(f"Found {len(cards)} job cards")

        for card in cards[:25]:
            try:
                title_el   = await card.query_selector("a.title, a[class*='title']")
                company_el = await card.query_selector("a.comp-name, a[class*='comp-name']")
                desc_el    = await card.query_selector("span.job-desc, ul.tags-gt, div[class*='desc']")
                apply_el   = await card.query_selector("button[class*='apply'], a[class*='apply']")

                title   = (await title_el.inner_text()).strip()   if title_el   else ""
                company = (await company_el.inner_text()).strip() if company_el else ""
                desc    = (await desc_el.inner_text()).strip()     if desc_el    else ""
                url     = await title_el.get_attribute("href")    if title_el   else ""

                if not title:
                    continue

                # Clean company name — strip ratings, reviews, newlines
                company = company.split("\n")[0].strip()

                # Deduplicate by (title, company)
                if any(j["title"] == title and j["company"] == company for j in jobs):
                    continue

                apply_text    = (await apply_el.inner_text()).lower() if apply_el else ""
                is_easy_apply = "apply" in apply_text and "external" not in apply_text

                jobs.append({
                    "title": title, "company": company,
                    "description": desc, "url": url,
                    "is_easy_apply": is_easy_apply,
                })
                log.info(f"  Job: {title} @ {company}")

            except Exception:
                continue

    except Exception as e:
        log.error(f"Scrape error: {e}")
        results["errors"].append(f"Scrape error: {str(e)[:200]}")

    return jobs


# ── Domain match (research-backed Indian job market scorer) ────────────────────
def _domain_match(client, job, resume_data, domain_family):
    title   = job.get("title", "")
    company = job.get("company", "")
    jd      = job.get("description", "")
    age     = job.get("age_days", 0)

    target_title  = resume_data.get("target_title", "")
    skills        = ", ".join(resume_data.get("ats_keywords", [])[:15])
    experience    = resume_data.get("experience", [])
    total_exp     = sum(_parse_years(e.get("period", "")) for e in experience)
    total_exp     = max(1, min(total_exp, 25))
    summary       = resume_data.get("summary", "")

    prompt = f"""You are a senior Indian recruiter. Decide: should this candidate apply to this job?

CANDIDATE:
- Target Role: {target_title}
- Domain: {domain_family}
- Experience: {total_exp} years
- Skills: {skills}
- Background: {summary[:300]}

HARD REJECT — answer false if ANY applies:
- Job age > 21 days (stale posting)
- Seniority wrong: VP/Director/Head OR Junior/Fresher/0-2 yrs required
- Wrong function: Software Engineer, Developer, QA, HR, Finance, Marketing, Sales
- Domain completely irrelevant AND explicitly required (capital markets for IT candidate, etc.)
- Location is fixed WFO in a city not preferred by candidate

MATCH SIGNALS:
- Title matches candidate's target role family
- Domain overlaps (same industry or adjacent)
- Experience band fits
- Skills appear in JD

JOB:
Title: {title}
Company: {company}
Age: {age} days old
Description: {jd[:800]}

Reply ONLY JSON (no markdown):
{{"match": true/false, "score": <0-100>, "reason": "<one line — specific factor>"}}"""

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


# ── Tailor resume ──────────────────────────────────────────────────────────────
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


# ── Recruiter inbox scraper ────────────────────────────────────────────────────
async def _scrape_recruiter_inbox(page, results: dict) -> list:
    """
    Scrape Naukri's recruiter activities / messages section for HR invites.
    Returns list of invite dicts (same shape as job listings).
    """
    invites = []
    inbox_urls = [
        "https://www.naukri.com/mnjuser/notification",
        "https://www.naukri.com/mnjuser/myapps",
    ]

    for url in inbox_urls:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(random.randint(1500, 2500))

            # Look for recruiter activity cards
            selectors = [
                "div[class*='recruiterActivity']",
                "div[class*='notification-item']",
                "li[class*='invite']",
                "div[class*='jobInvite']",
                "div[class*='recInvite']",
            ]

            cards = []
            for sel in selectors:
                cards = await page.query_selector_all(sel)
                if cards:
                    log.info(f"Found {len(cards)} recruiter activity cards via: {sel}")
                    break

            for card in cards[:10]:
                try:
                    title_el   = await card.query_selector("a[class*='title'], a[class*='job'], h3, h4")
                    company_el = await card.query_selector("span[class*='comp'], a[class*='comp'], span[class*='org']")
                    hr_el      = await card.query_selector("span[class*='recruiter'], span[class*='hr'], span[class*='sender']")
                    link_el    = await card.query_selector("a[href*='naukri.com'], a[class*='apply']")

                    title   = (await title_el.inner_text()).strip()   if title_el   else ""
                    company = (await company_el.inner_text()).strip() if company_el else ""
                    hr_name = (await hr_el.inner_text()).strip()      if hr_el      else ""
                    url_val = await link_el.get_attribute("href")     if link_el    else ""

                    if not title and not company:
                        continue

                    invites.append({
                        "title":        title or "Role from Recruiter",
                        "company":      company,
                        "hr_name":      hr_name,
                        "description":  "",
                        "url":          url_val or url,
                        "is_easy_apply": True,
                        "source":       "hr_invite",
                        "age_days":     0,  # Fresh — HR just contacted
                    })
                    log.info(f"  HR Invite: {title} @ {company}")
                except Exception:
                    continue

            if invites:
                break  # Found invites — no need to check other URLs

        except Exception as e:
            log.warning(f"Recruiter inbox check failed for {url}: {e}")
            results["errors"].append(f"Recruiter inbox error: {str(e)[:150]}")

    return invites


# ── HR invite instant notification ────────────────────────────────────────────
def _notify_hr_invite(make_webhook: str, invite: dict, applied: bool,
                      contact: str, notif_pref: str, user_email: str = ""):
    """Instant push notification (ntfy) when an HR invite is detected."""
    topic  = _ntfy_topic(user_email or contact)
    status = "Auto-applied by CareerOS" if applied else "Reviewed — not a strong match"
    _ntfy(
        topic     = topic,
        title     = f"HR Invite — {invite.get('company', 'Unknown')}",
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


# ── Apply ──────────────────────────────────────────────────────────────────────
async def _apply_job(job, resume_data, make_webhook, notif_contact, notif_pref,
                     is_hr_invite: bool = False):
    try:
        if make_webhook:
            requests.post(make_webhook, json={
                "type":         "hr_invite_apply" if is_hr_invite else (
                                "easy_apply" if job.get("is_easy_apply") else "company_portal"),
                "job_title":    job.get("title"),
                "company":      job.get("company"),
                "job_url":      job.get("url"),
                "contact":      notif_contact,
                "notif_pref":   notif_pref,
                "is_hr_invite": is_hr_invite,
            }, timeout=5)
        return True
    except Exception:
        return False


# ── Utility ────────────────────────────────────────────────────────────────────
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
