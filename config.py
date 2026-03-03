# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

load_dotenv()

def _get_secret(key: str, default: str = "") -> str:
    val = os.getenv(key, "")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default

# backward compat alias
_secret = _get_secret

ANTHROPIC_API_KEY   = _secret("ANTHROPIC_API_KEY")
CLAUDE_MODEL        = "claude-sonnet-4-6"
MAX_TOKENS_PROBE    = 1024
MAX_TOKENS_GENERATE = 8192
MAX_PROBE_ROUNDS    = 14
MIN_PROBE_ROUNDS    = 6      # min exchanges before resume can be generated

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "users")
