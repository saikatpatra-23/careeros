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


async def _save_scope_debug(scope, prefix: str) -> Path | None:
    dump_path = LOG_FILE.parent / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    try:
        if hasattr(scope, "content"):
            dump_path.write_text(await scope.content(), encoding="utf-8")
            return dump_path
    except Exception as exc:
        log.warning(f"Could not save scoped HTML dump: {exc}")
    return None


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


async def _click_quick_link(page, label: str, action_text: str = "") -> bool:
    script = """
    ([targetLabel, targetAction]) => {
        const items = Array.from(document.querySelectorAll('.quickLink .collection-item'));
        const norm = (v) => (v || '').trim().toLowerCase();
        for (const item of items) {
            const textEl = item.querySelector('.text');
            if (!textEl || norm(textEl.textContent) !== norm(targetLabel)) continue;
            const actionEl = item.querySelector('.secondary-content');
            if (targetAction) {
                if (actionEl && norm(actionEl.textContent) === norm(targetAction)) {
                    actionEl.click();
                    return true;
                }
            } else if (actionEl) {
                actionEl.click();
                return true;
            } else {
                item.click();
                return true;
            }
        }
        return false;
    }
    """
    try:
        clicked = await page.evaluate(script, [label, action_text])
        if clicked:
            await page.wait_for_timeout(2000)
            await _dismiss_chatbot(page)
        return bool(clicked)
    except Exception:
        return False


async def _profile_form_scope(page):
    frame_el = page.locator("#dynamic-form-iframe").first
    try:
        if await frame_el.count() > 0 and await frame_el.is_visible(timeout=500):
            frame_handle = await frame_el.element_handle()
            if frame_handle:
                frame = await frame_handle.content_frame()
                if frame:
                    return frame
    except Exception:
        pass
    return page


async def _wait_for_profile_form(page, timeout_ms: int = 12000):
    deadline = asyncio.get_running_loop().time() + (timeout_ms / 1000)
    while asyncio.get_running_loop().time() < deadline:
        scope = await _profile_form_scope(page)
        selectors = [
            "textarea",
            "input[type='text']",
            "input[placeholder]",
            "div[contenteditable='true']",
            "button:has-text('Save')",
            "button:has-text('Save Changes')",
        ]
        for selector in selectors:
            try:
                locator = scope.locator(selector).first
                if await locator.count() > 0 and await locator.is_visible(timeout=250):
                    return scope
            except Exception:
                continue
        await page.wait_for_timeout(500)
    return await _profile_form_scope(page)


async def _ensure_lazy_section_loaded(page, section_id: str, ready_selectors: list[str]) -> bool:
    try:
        await page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2500)
        await _dismiss_chatbot(page)
        anchor = page.locator(f"#{section_id}").first
        if await anchor.count() == 0:
            return False
        await anchor.scroll_into_view_if_needed()
        for _ in range(18):
            await page.wait_for_timeout(800)
            await _dismiss_chatbot(page)
            for selector in ready_selectors:
                try:
                    ready = page.locator(selector).first
                    if await ready.count() > 0 and await ready.is_visible(timeout=250):
                        return True
                except Exception:
                    continue
            await page.mouse.wheel(0, 700)
        return False
    except Exception:
        return False


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


async def _try_open_profile_edit(page, section_name: str, selectors: list[str], reload_page: bool = False) -> bool:
    if reload_page:
        await page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
    await _dismiss_chatbot(page)
    for _ in range(3):
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if await locator.count() > 0 and await locator.is_visible(timeout=400):
                    await locator.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    await locator.click(force=True)
                    await page.wait_for_timeout(2000)
                    await _dismiss_chatbot(page)
                    log.info(f"Opened edit modal for {section_name}")
                    return True
            except Exception:
                continue
        await page.mouse.wheel(0, 700)
        await page.wait_for_timeout(700)
        await _dismiss_chatbot(page)
    return False


async def _open_profile_edit(page, section_name: str, selectors: list[str]) -> bool:
    opened = await _try_open_profile_edit(page, section_name, selectors, reload_page=True)
    if not opened:
        log.warning(f"Could not open edit modal for {section_name}")
    return opened


async def _open_profile_section(page, section_name: str, selectors: list[str], quick_link_label: str = "", quick_link_action: str = "") -> bool:
    opened = await _open_profile_edit(page, section_name, selectors)
    if opened:
        return True
    if quick_link_label:
        await page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        await _dismiss_chatbot(page)
        if await _click_quick_link(page, quick_link_label, quick_link_action):
            if quick_link_action:
                log.info(f"Opened {section_name} via quick link")
                return True
            opened = await _try_open_profile_edit(page, section_name, selectors, reload_page=False)
            if opened:
                log.info(f"Opened {section_name} via quick link")
                return True
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
    await _ensure_lazy_section_loaded(page, "lazyProfileSummary", [
        "#lazyProfileSummary .edit",
        "#lazyProfileSummary textarea",
        "#lazyProfileSummary [contenteditable='true']",
    ])
    opened = await _open_profile_section(page, "profile summary", [
        "#lazyProfileSummary .edit",
        "div.widgetHead:has-text('Profile Summary') .edit",
        "div.widgetHead:has-text('About') .edit",
        ".profileSummary .edit",
        ".summarySection .edit",
    ], quick_link_label="Profile summary")
    if not opened:
        return
    scope = await _wait_for_profile_form(page)
    for selector in [
        "[data-testid*='summary'] textarea",
        "[name*='summary' i]",
        "textarea[name='profileSummary']",
        "textarea[id*='summary']",
        "textarea[placeholder*='summary']",
        "textarea[placeholder*='Summary']",
        "[role='textbox']",
        "div[contenteditable='true']",
    ]:
        try:
            ta = scope.locator(selector).first
            if await ta.count() > 0 and await ta.is_visible(timeout=500):
                if "contenteditable" in selector:
                    await ta.click()
                    await ta.fill("")
                    await ta.type(summary)
                elif selector == "[role='textbox']":
                    await ta.click()
                    await ta.press("Control+A")
                    await ta.type(summary)
                else:
                    await ta.fill(summary)
                await page.wait_for_timeout(500)
                saved = await _js_save_click(page)
                if not saved and scope is not page:
                    try:
                        save_btn = scope.locator("button:has-text('Save'), button:has-text('Save Changes')").first
                        if await save_btn.count() > 0:
                            await save_btn.click()
                            saved = True
                    except Exception:
                        pass
                await page.wait_for_timeout(2000)
                log.info(f"Profile summary {'updated' if saved else 'filled; save uncertain'}")
                return
        except Exception:
            continue
    debug_path = await _save_scope_debug(scope, "profile_summary_scope")
    if debug_path:
        log.warning(f"Profile summary textarea not found | scope html: {debug_path.name}")
        return
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
    preferred_locations = list(dict.fromkeys(preferred_locations))[:10]
    if not preferred_locations:
        log.warning("No preferred locations available. Skipping.")
        return

    await page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2500)
    await _dismiss_chatbot(page)
    await _ensure_lazy_section_loaded(page, "lazyDesiredProfile", [
        "#lazyDesiredProfile .edit",
        "#lazyDesiredProfile .desiredProfile .edit",
        "#lazyDesiredProfile .widgetHead .edit",
        "#lazyDesiredProfile .add",
    ])
    opened = await _try_open_profile_edit(page, "preferred locations", [
        "#lazyDesiredProfile .desiredProfile .edit",
        "#lazyDesiredProfile .widgetHead .edit",
        "#lazyDesiredProfile .edit",
        "div.widgetHead:has-text('Career profile') .edit",
        "div.widgetHead:has-text('Desired career profile') .edit",
        "div.widgetHead:has-text('Preferred location') .edit",
    ], reload_page=False)
    if not opened:
        if await _click_quick_link(page, "Career profile"):
            await _ensure_lazy_section_loaded(page, "lazyDesiredProfile", [
                "#lazyDesiredProfile .edit",
                "#lazyDesiredProfile .widgetHead .edit",
            ])
            opened = await _try_open_profile_edit(page, "preferred locations", [
                "#lazyDesiredProfile .desiredProfile .edit",
                "#lazyDesiredProfile .widgetHead .edit",
                "#lazyDesiredProfile .edit",
            ], reload_page=False)
    if not opened:
        log.warning("Could not open edit modal for preferred locations")
        return

    scope = await _wait_for_profile_form(page)
    loc_input = None
    for selector in [
        "#locationSugg",
        ".desiredLoc .sugInp",
        "[data-testid*='location'] input",
        "input[name*='location' i]",
        "input[placeholder*='location']",
        "input[placeholder*='Location']",
        "input[placeholder*='city']",
        "input[placeholder*='City']",
        "input[placeholder*='Preferred']",
    ]:
        try:
            locator = scope.locator(selector).first
            if await locator.count() > 0 and await locator.is_visible(timeout=500):
                loc_input = locator
                break
        except Exception:
            continue
    if not loc_input:
        debug_path = await _save_scope_debug(scope, "preferred_locations_scope")
        if debug_path:
            log.warning(f"Preferred location input not found | scope html: {debug_path.name}")
        else:
            log.warning("Preferred location input not found")
        return

    for loc in preferred_locations:
        try:
            await loc_input.fill(loc)
            await page.wait_for_timeout(1000)
            chosen = False
            for suggestion_selector in [
                f"#sugDrp_locationSugg li:has-text('{loc}')",
                f".topCitiesSuggestions li:has-text('{loc}')",
                f"[class*='suggest'] li:has-text('{loc}')",
                f".suggestions li:has-text('{loc}')",
                "#sugDrp_locationSugg li",
                ".topCitiesSuggestions li",
                "[class*='suggest'] li",
                ".suggestions li",
                "[role='option']",
            ]:
                suggestion = scope.locator(suggestion_selector).first
                if await suggestion.count() > 0 and await suggestion.is_visible(timeout=500):
                    await suggestion.click(force=True)
                    chosen = True
                    break
            if not chosen:
                await loc_input.press("Enter")
            await page.wait_for_timeout(500)
            log.info(f"Added location: {loc}")
        except Exception as exc:
            log.warning(f"Could not add location '{loc}': {exc}")

    saved = False
    for selector in ["#saveDesiredProfile", "button:has-text('Save')", "button:has-text('Save Changes')", "input[type='submit']"]:
        try:
            save_btn = scope.locator(selector).first
            if await save_btn.count() > 0 and await save_btn.is_visible(timeout=500):
                await save_btn.click(force=True)
                saved = True
                break
        except Exception:
            continue
    if not saved:
        saved = await _js_save_click(page)
    await page.wait_for_timeout(2500)
    if not saved:
        debug_path = await _save_scope_debug(scope, "preferred_locations_scope")
        if debug_path:
            log.warning(f"Preferred locations save uncertain | scope html: {debug_path.name}")
    log.info(f"Preferred locations {'saved' if saved else 'edited; save uncertain'}")


async def _update_employment_descriptions(page, profile_data: dict):
    descriptions = profile_data.get("employment_descriptions", []) or []
    if not descriptions:
        log.warning("No employment descriptions available. Skipping.")
        return

    updated = 0
    for entry in descriptions[:3]:
        company = str(entry.get("company", "")).strip()
        company_root = company.split("(")[0].strip() if company else ""
        description = str(entry.get("description", "")).strip()
        if not company or not description:
            continue
        try:
            await _ensure_lazy_section_loaded(page, "lazyEmployment", [
                "#lazyEmployment .edit",
                "#lazyEmployment section",
                "#lazyEmployment .card",
            ])
            selectors = [
                f"#lazyEmployment section:has-text('{company}') .edit",
                f"#lazyEmployment div:has-text('{company}') .edit",
                f"#lazyEmployment section:has-text('{company_root}') .edit",
                f"#lazyEmployment div:has-text('{company_root}') .edit",
                f"section:has-text('{company}') .edit",
                f"div:has-text('{company}') .edit",
                f"section:has-text('{company_root}') .edit",
                f"div:has-text('{company_root}') .edit",
                f"[class*='employment']:has-text('{company}') .edit",
                "#lazyEmployment .emp-list .edit",
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
            if not opened and await _click_quick_link(page, "Employment", "Add"):
                opened = True
            elif not opened and await _click_quick_link(page, "Employment"):
                opened = True
            if not opened:
                log.warning(f"Employment edit button not found for {company}")
                continue

            scope = await _wait_for_profile_form(page)
            textarea = None
            for selector in [
                "[data-testid*='employment'] textarea",
                "textarea[name*='description' i]",
                "textarea[name*='description']",
                "textarea[id*='desc']",
                "textarea[placeholder*='description']",
                "div[contenteditable='true']",
            ]:
                locator = scope.locator(selector).first
                if await locator.count() > 0 and await locator.is_visible(timeout=500):
                    textarea = locator
                    break
            if not textarea:
                debug_path = await _save_scope_debug(scope, f"employment_scope_{updated + 1}")
                if debug_path:
                    log.warning(f"Employment description textarea not found for {company} | scope html: {debug_path.name}")
                else:
                    log.warning(f"Employment description textarea not found for {company}")
                continue

            if await textarea.get_attribute("contenteditable"):
                await textarea.click()
                await textarea.press("Control+A")
                await textarea.type(description[:1900])
            else:
                await textarea.fill(description[:1900])
            await page.wait_for_timeout(500)
            saved = await _js_save_click(page)
            if not saved and scope is not page:
                try:
                    save_btn = scope.locator("button:has-text('Save'), button:has-text('Save Changes'), input[type='submit']").first
                    if await save_btn.count() > 0 and await save_btn.is_visible(timeout=500):
                        await save_btn.click()
                        saved = True
                except Exception:
                    pass
            await page.wait_for_timeout(2000)
            updated += 1
            log.info(f"Employment description {'saved' if saved else 'filled; save uncertain'} for {company}")
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