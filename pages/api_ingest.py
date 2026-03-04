# -*- coding: utf-8 -*-
"""
CareerOS — Results Ingest API
Accepts POST requests from the local runner to sync run results to the web app.

Endpoint (via Streamlit query params):
  GET  /api_ingest?token=TOKEN&action=ping          → health check
  POST via st.query_params + form body is not standard Streamlit,
  so we use a hidden Streamlit page with st.query_params to accept
  a JSON payload encoded as a base64 query param.

URL format the local runner POSTs to:
  https://<app>.streamlit.app/api_ingest
  with JSON body: {"token": "...", "email": "...", "results": {...}}

Because Streamlit Cloud doesn't support raw HTTP POST endpoints,
we use a workaround: the local runner encodes results as base64
and calls the URL with a GET + query param. The page reads it,
validates the token, and writes to UserStore.
"""
import os
import sys
import json
import base64
import hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from persistence.store import UserStore
from config import _get_secret

st.set_page_config(page_title="CareerOS Sync", page_icon="🔄", layout="centered")

# ── Token validation ──────────────────────────────────────────────────────────
SYNC_SECRET = _get_secret("SYNC_SECRET", "")

params = st.query_params

action = params.get("action", "")
token  = params.get("token", "")
data_b64 = params.get("data", "")

# ── Health check ──────────────────────────────────────────────────────────────
if action == "ping":
    st.json({"status": "ok", "service": "CareerOS Results Ingest"})
    st.stop()

# ── Ingest results ────────────────────────────────────────────────────────────
if data_b64 and token:
    if not SYNC_SECRET:
        st.error("SYNC_SECRET not configured on server.")
        st.stop()

    if token != SYNC_SECRET:
        st.error("Invalid token.")
        st.stop()

    try:
        payload = json.loads(base64.b64decode(data_b64).decode("utf-8"))
        email   = payload.get("email", "")
        results = payload.get("results", {})

        if not email or not results:
            st.error("Missing email or results in payload.")
            st.stop()

        store = UserStore(email)

        # Save run to history
        store.save_apply_run(results)

        # Save HR invites
        for inv in results.get("hr_invites", []):
            store.save_hr_invite(inv)

        st.success(f"Results synced for {email}: {results.get('jobs_applied', 0)} applied, {results.get('jobs_found', 0)} scanned.")
        st.json({"status": "ok", "jobs_applied": results.get("jobs_applied", 0)})

    except Exception as e:
        st.error(f"Sync failed: {e}")

else:
    # Show instructions if accessed directly
    st.markdown("""
    ## CareerOS Results Sync Endpoint

    This page receives automated run results from the CareerOS local runner.

    **Not meant for manual use.** If you're seeing this, your local runner
    is configured to sync results to this app automatically.

    To configure sync, add `careeros_sync_url` to your `careeros_config.json`:
    ```json
    "careeros_sync_url": "https://your-app.streamlit.app/api_ingest?token=YOUR_SYNC_SECRET&data="
    ```

    Then add `SYNC_SECRET` to your Streamlit Cloud secrets.
    """)
