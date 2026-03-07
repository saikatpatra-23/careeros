# -*- coding: utf-8 -*-
"""
Lightweight product telemetry for beta operations.

Tracks:
- login events
- page views
- handled/unhandled errors
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import threading
import traceback
from pathlib import Path
from typing import Any

import streamlit as st

from config import DATA_DIR


TELEMETRY_DIR = Path(DATA_DIR).parent / "telemetry"
EVENTS_FILE = TELEMETRY_DIR / "events.jsonl"


def _now_iso() -> str:
    return dt.datetime.now().isoformat()


def _safe_write_event(event: dict[str, Any]) -> None:
    try:
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        # Telemetry must never break user flows.
        pass


def _short_email(email: str) -> str:
    email = (email or "").strip().lower()
    if "@" not in email:
        return email
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        masked = name[0] + "*"
    else:
        masked = name[:2] + "*" * (len(name) - 2)
    return f"{masked}@{domain}"


def log_event(
    event_type: str,
    email: str = "",
    page: str = "",
    level: str = "info",
    details: dict[str, Any] | None = None,
) -> None:
    event = {
        "ts": _now_iso(),
        "event_type": event_type,
        "level": level,
        "email": (email or "").strip().lower(),
        "email_masked": _short_email(email),
        "page": page or "",
        "details": details or {},
    }
    _safe_write_event(event)


def track_login(email: str, name: str = "") -> None:
    key = "_telemetry_login_sent"
    if st.session_state.get(key):
        return
    st.session_state[key] = True
    log_event("login", email=email, details={"name": name or ""})


def track_page_view(email: str, page: str) -> None:
    key = f"_telemetry_page_{page}"
    if st.session_state.get(key):
        return
    st.session_state[key] = True
    log_event("page_view", email=email, page=page)


def log_error(email: str, page: str, exc: BaseException, handled: bool = True) -> None:
    log_event(
        "error",
        email=email,
        page=page,
        level="error",
        details={
            "handled": handled,
            "type": exc.__class__.__name__,
            "message": str(exc)[:500],
            "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[:4000],
        },
    )


def install_error_tracking(email: str, page: str) -> None:
    key = f"_telemetry_hook_{page}"
    if st.session_state.get(key):
        return
    st.session_state[key] = True

    old_sys_hook = sys.excepthook
    old_thread_hook = getattr(threading, "excepthook", None)

    def _sys_hook(exc_type, exc_value, exc_tb):
        try:
            if exc_value is not None:
                log_error(email=email, page=page, exc=exc_value, handled=False)
        finally:
            old_sys_hook(exc_type, exc_value, exc_tb)

    def _thread_hook(args):
        try:
            if getattr(args, "exc_value", None) is not None:
                log_error(email=email, page=page, exc=args.exc_value, handled=False)
        finally:
            if old_thread_hook:
                old_thread_hook(args)

    sys.excepthook = _sys_hook
    if old_thread_hook is not None:
        threading.excepthook = _thread_hook


def read_events(limit: int = 2000) -> list[dict[str, Any]]:
    if not EVENTS_FILE.exists():
        return []
    events: list[dict[str, Any]] = []
    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    continue
        return events[-limit:]
    except Exception:
        return []
