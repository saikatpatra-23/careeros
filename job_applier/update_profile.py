# -*- coding: utf-8 -*-
"""
CareerOS Naukri Profile Updater
Runs locally to update a user's Naukri profile from CareerOS-generated content.
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet
from playwright.async_api import async_playwright

CONFIG_FILE = Path(__file__).parent / "config.json"
LOG_FILE = Path(__file__).parent / "logs" / f"profile_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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


async def _save_debug(page, prefix: str) -> tuple[Path, Path]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shot_path = LOG_FILE.parent / f"{prefix}_{stamp}.png"
    html_path = LOG_FILE.parent / f"{prefix}_{stamp}.html"
    try:
        await page.screenshot(path=str(shot_path), full_page=True)
    except Exception as exc:
        log.warning(f"Could not save screenshot: {exc}")
    try:
        html_path.write_text(await page.content(), encoding="utf-8")
    except Exception as exc:
        log.warning(f"Could not save HTML dump: {exc}")
    return shot_path, html_path


async def _dismiss_chatbot(page):
    await page.evaluate(
        """() => {
            document.querySelectorAll(
                '.chatbot_Overlay, [class*="chatbot_Overlay"], ._chatBotContainer'
            ).forEach(el => {
                el.style.display = 'none';
                el.style.pointerEvents = 'none';
            });
        }"""
    )


async def _force_click(page, selector: str) -> bool:
    return await page.evaluate(
        f"""() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (el) {{ el.click(); return true; }}
            return false;
        }}"""
    )


async def _js_save_click(page) -> bool:
    return await page.evaluate(
        """() => {
            for (const btn of document.querySelectorAll('button')) {
                const txt = (btn.textContent || '').trim();
                const cls = btn.className || '';
                const visible = btn.offsetParent !== null;
                if ((txt === 'Save' || txt === 'Save Changes') &&
                    !String(cls).includes('save-photo') && visible) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }"""
    )


async def _login_naukri(page, email: str, password: str) -> bool:
    try:
        log.info("Opening Naukri login page...")
        await page.goto("https://www.naukri.com/nlogin/login", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2500)
        await page.fill("#usernameField", email, timeout=10000)
        await page.wait_for_timeout(500)
        await page.fill("#passwordField", password, timeout=5000)
        await page.wait_for_timeout(500)
        await page.click("button:has-text('Login')", timeout=5000)

        login_success_selectors = [
            "div.nI-gNb-drawer",
            "div.view-profile-wrapper",
            "a[href*='mnjuser/profile']",
            "a[title*='View profile' i]",
            "a[href*='/mnjuser/homepage']",
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

        shot_path, html_path = await _save_debug(page, "profile_login_failure")
        log.error(f"Login failed - still on login page: {page.url} | screenshot: {shot_path.name} | html: {html_path.name}")
        return False
    except Exception as exc:
        shot_path, html_path = await _save_debug(page, "profile_login_error")
        log.error(f"Login error: {exc} | screenshot: {shot_path.name} | html: {html_path.name}")
        return False


async def _open_profile_edit(page, section_name: str, selectors: list[str]) -> bool:
    await page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)
    await _dismiss_chatbot(page)
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0:
                await locator.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                await locator.click(force=True)
                await page.wait_for_timeout(2000)
                await _dismiss_chatbot(page)
                log.info(f"Opened edit modal for {section_name}")
                return True
        except Exception:
            continue
    log.warning(f"Could not open edit modal for {section_name}")
    return False


async def _update_headline(page, profile_data: dict):
    headline = (profile_data.get("headline") or "").strip()[:250]
    if not headline:
        log.warning("Headline missing in profile data. Skipping.")
        return
    opened = await _open_profile_edit(page, "headline", [".widgetHead .edit", ".resumeHeadline .edit"])
    if not opened:
        return
    for selector in [
        "textarea#resumeHeadlineTxtArea",
        "textarea[name='resumeHeadline']",
        "textarea[placeholder*='headline']",
        "textarea[placeholder*='Headline']",
    ]:
        try:
            ta = page.locator(selector).first
            if await ta.count() > 0:
                await ta.fill(headline)
                await page.wait_for_timeout(500)
                saved = await _js_save_click(page)
                await page.wait_for_timeout(2000)
                log.info(f"Headline {'updated' if saved else 'filled; save uncertain'}")
                return
        except Exception:
            continue
    log.warning("Headline textarea not found")


async def _update_summary(page, profile_data: dict):
    summary = (profile_data.get("profile_summary") or "").strip()
    if not summary:
        log.warning("Profile summary missing in profile data. Skipping.")
        return
    opened = await _open_profile_edit(page, "profile summary", [
        "div.widgetHead:has-text('Profile Summary') .edit",
        "div.widgetHead:has-text('About') .edit",
        ".profileSummary .edit",
        ".summarySection .edit",
    ])
    if not opened:
        return
    for selector in [
        "textarea[name='profileSummary']",
        "textarea[id*='summary']",
        "textarea[placeholder*='summary']",
        "textarea[placeholder*='Summary']",
    ]:
        try:
            ta = page.locator(selector).first
            if await ta.count() > 0:
                await ta.fill(summary)
                await page.wait_for_timeout(500)
                saved = await _js_save_click(page)
                await page.wait_for_timeout(2000)
                log.info(f"Profile summary {'updated' if saved else 'filled; save uncertain'}")
                return
        except Exception:
            continue
    log.warning("Profile summary textarea not found")


async def _update_skills(page, profile_data: dict):
    skills_add = [s.strip() for s in profile_data.get("skills_add", []) if str(s).strip()]
    skills_remove = [s.strip() for s in profile_data.get("skills_remove", []) if str(s).strip()]
    if not skills_add and not skills_remove:
        log.warning("No skill changes available. Skipping.")
        return
    opened = await _open_profile_edit(page, "key skills", [
        "div.widgetHead:has-text('Key skills') .edit",
        "div.widgetHead:has-text('Key Skills') .edit",
    ])
    if not opened:
        return

    for skill_name in skills_remove:
        for selector in [
            f".chip:has-text('{skill_name}') i",
            f".chip:has-text('{skill_name}') .delete",
            f".chip:has-text('{skill_name}') span[class*='close']",
        ]:
            try:
                chip_del = page.locator(selector).first
                if await chip_del.count() > 0:
                    await chip_del.click(force=True)
                    await page.wait_for_timeout(300)
                    log.info(f"Removed skill: {skill_name}")
                    break
            except Exception:
                continue

    skill_input = None
    for selector in [
        "input[placeholder*='skill']",
        "input[placeholder*='Skill']",
        ".skillInput input",
        "#skillInput",
        "input[class*='skill']",
    ]:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0:
                skill_input = locator
                break
        except Exception:
            continue
    if not skill_input:
        log.warning("Skill input not found")
        return

    existing = []
    try:
        chips = await page.locator(".chip").all()
        for chip in chips:
            existing.append((await chip.inner_text()).strip().lower())
    except Exception:
        existing = []

    for skill in skills_add:
        if skill.lower() in existing:
            continue
        try:
            await skill_input.fill(skill)
            await page.wait_for_timeout(800)
            picked = False
            for suggestion_selector in [
                f".suggestions li:has-text('{skill}')",
                f"[class*='suggest'] li:has-text('{skill}')",
                "[class*='suggest'] li",
                ".suggestions li",
            ]:
                dropdown = page.locator(suggestion_selector).first
                if await dropdown.count() > 0:
                    await dropdown.click(force=True)
                    picked = True
                    break
            if not picked:
                await skill_input.press("Enter")
            await page.wait_for_timeout(400)
            log.info(f"Added skill: {skill}")
        except Exception as exc:
            log.warning(f"Could not add skill '{skill}': {exc}")

    saved = await _js_save_click(page)
    await page.wait_for_timeout(2000)
    log.info(f"Skills {'saved' if saved else 'edited; save uncertain'}")


async def _update_preferred_locations(page, profile_data: dict, current_location: str):
    preferred_locations = [
        str(loc).strip()
        for loc in profile_data.get("preferred_locations", [])
        if str(loc).strip()
    ]
    if current_location and current_location not in preferred_locations:
        preferred_locations.insert(0, current_location)
    if not preferred_locations:
        log.warning("No preferred locations available. Skipping.")
        return

    opened = await _open_profile_edit(page, "preferred locations", [
        "div.widgetHead:has-text('Desired career profile') .edit",
        "div.widgetHead:has-text('Career profile') .edit",
        "div.widgetHead:has-text('Preferred location') .edit",
    ])
    if not opened:
        return

    loc_input = None
    for selector in [
        "input[placeholder*='location']",
        "input[placeholder*='Location']",
        "input[placeholder*='city']",
        "input[placeholder*='City']",
    ]:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0:
                loc_input = locator
                break
        except Exception:
            continue
    if not loc_input:
        log.warning("Preferred location input not found")
        return

    for loc in preferred_locations:
        try:
            await loc_input.fill(loc)
            await page.wait_for_timeout(800)
            chosen = False
            for suggestion_selector in [
                f"[class*='suggest'] li:has-text('{loc}')",
                f".suggestions li:has-text('{loc}')",
                "[class*='suggest'] li",
                ".suggestions li",
            ]:
                suggestion = page.locator(suggestion_selector).first
                if await suggestion.count() > 0:
                    await suggestion.click(force=True)
                    chosen = True
                    break
            if not chosen:
                await loc_input.press("Enter")
            await page.wait_for_timeout(400)
            log.info(f"Added location: {loc}")
        except Exception as exc:
            log.warning(f"Could not add location '{loc}': {exc}")

    saved = await _js_save_click(page)
    await page.wait_for_timeout(2000)
    log.info(f"Preferred locations {'saved' if saved else 'edited; save uncertain'}")


async def _update_employment_descriptions(page, profile_data: dict):
    descriptions = profile_data.get("employment_descriptions", []) or []
    if not descriptions:
        log.warning("No employment descriptions available. Skipping.")
        return

    await page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)
    await _dismiss_chatbot(page)

    updated = 0
    for entry in descriptions[:3]:
        company = str(entry.get("company", "")).strip()
        description = str(entry.get("description", "")).strip()
        if not company or not description:
            continue
        try:
            selectors = [
                f"section:has-text('{company}') .edit",
                f"div:has-text('{company}') .edit",
                f"[class*='employment']:has-text('{company}') .edit",
            ]
            opened = False
            for selector in selectors:
                locator = page.locator(selector).first
                if await locator.count() > 0:
                    await locator.scroll_into_view_if_needed()
                    await locator.click(force=True)
                    await page.wait_for_timeout(2000)
                    await _dismiss_chatbot(page)
                    opened = True
                    break
            if not opened:
                log.warning(f"Employment edit button not found for {company}")
                continue

            textarea = None
            for selector in [
                "textarea[name*='description']",
                "textarea[id*='desc']",
                "textarea[placeholder*='description']",
            ]:
                locator = page.locator(selector).first
                if await locator.count() > 0:
                    textarea = locator
                    break
            if not textarea:
                log.warning(f"Employment description textarea not found for {company}")
                continue

            await textarea.fill(description[:1900])
            await page.wait_for_timeout(500)
            saved = await _js_save_click(page)
            await page.wait_for_timeout(2000)
            updated += 1
            log.info(f"Employment description {'saved' if saved else 'filled; save uncertain'} for {company}")
            await page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2500)
            await _dismiss_chatbot(page)
        except Exception as exc:
            log.warning(f"Employment description update failed for {company}: {exc}")
    if updated == 0:
        log.warning("No employment descriptions were updated")


async def main():
    if not CONFIG_FILE.exists():
        log.error(f"config.json not found at {CONFIG_FILE}")
        return

    with open(CONFIG_FILE, encoding="utf-8-sig") as f:
        inp = json.load(f)

    profile_data = inp.get("naukri_profile_data") or {}
    if not profile_data:
        log.error("No naukri_profile_data found in config.json. Generate Naukri profile content in CareerOS and download the updater again.")
        return

    fernet_key = inp.get("fernet_key", "")
    pass_enc = inp.get("naukri_pass_enc", "")
    naukri_email = inp.get("naukri_email", "")
    if not (fernet_key and pass_enc and naukri_email):
        log.error("Missing Naukri credentials in config.json")
        return

    try:
        naukri_password = Fernet(fernet_key.encode()).decrypt(pass_enc.encode()).decode()
    except Exception as exc:
        log.error(f"Could not decrypt Naukri password: {exc}")
        return

    headless = bool(inp.get("headless", False))
    current_location = inp.get("current_location", "")

    async with async_playwright() as pw:
        launch_kwargs = {
            "headless": headless,
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        use_chrome = headless and (shutil.which("chrome") or Path("C:/Program Files/Google/Chrome/Application/chrome.exe").exists())
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

        logged_in = await _login_naukri(page, naukri_email, naukri_password)
        if not logged_in:
            await browser.close()
            return

        await _update_headline(page, profile_data)
        await _update_summary(page, profile_data)
        await _update_skills(page, profile_data)
        await _update_preferred_locations(page, profile_data, current_location)
        await _update_employment_descriptions(page, profile_data)

        await page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        shot_path, _ = await _save_debug(page, "profile_updated")
        log.info(f"Profile screenshot saved: {shot_path.name}")
        log.info("Naukri profile update flow completed.")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())