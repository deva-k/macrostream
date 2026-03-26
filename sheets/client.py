"""Google Sheets authentication and low-level helpers."""

import json
import os
import random
import time
from functools import wraps

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ── Retry on quota errors ──────────────────────────────────────────────────────

def retry_on_quota(max_retries: int = 4, base_delay: float = 2.0):
    """Retry a Sheets API call on 429 rate-limit errors with exponential back-off.

    Delays: ~2s, ~4s, ~8s, ~16s (plus jitter) before giving up.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except gspread.exceptions.APIError as exc:
                    status = getattr(exc.response, "status_code", None)
                    if status == 429 and attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator


# ── Auth ───────────────────────────────────────────────────────────────────────

def is_configured() -> bool:
    try:
        has_creds = (
            ("gcp_service_account" in st.secrets)
            or os.path.exists(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json"))
        )
        has_sheet = bool(
            st.secrets.get("GOOGLE_SHEET_ID") or os.getenv("GOOGLE_SHEET_ID")
        )
        return has_creds and has_sheet
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _get_client() -> gspread.Client | None:
    try:
        if "gcp_service_account" in st.secrets:
            creds_info = dict(st.secrets["gcp_service_account"])
        else:
            sa_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")
            with open(sa_path) as f:
                creds_info = json.load(f)

        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def _get_spreadsheet_cached() -> gspread.Spreadsheet | None:
    """Cache the Spreadsheet object itself — avoids repeated open_by_key() calls."""
    client = _get_client()
    if client is None:
        return None
    sheet_id = None
    try:
        sheet_id = st.secrets.get("GOOGLE_SHEET_ID") or os.getenv("GOOGLE_SHEET_ID")
    except Exception:
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        return None
    try:
        return client.open_by_key(sheet_id)
    except Exception:
        return None


def get_spreadsheet() -> gspread.Spreadsheet | None:
    return _get_spreadsheet_cached()


# ── Worksheet object cache ─────────────────────────────────────────────────────
# Caching Worksheet objects avoids repeated spreadsheet.worksheet() API reads.

@st.cache_resource(show_spinner=False)
def _ws_cache() -> dict:
    return {}


def get_or_create_worksheet(
    spreadsheet: gspread.Spreadsheet,
    title: str,
    headers: list[str] | None = None,
) -> gspread.Worksheet:
    """Return a Worksheet object, creating it if needed. Object is cached in memory."""
    cache = _ws_cache()
    key = f"{spreadsheet.id}::{title}"

    if key not in cache:
        try:
            ws = spreadsheet.worksheet(title)
            if headers:
                existing = ws.row_values(1)
                if not existing:
                    ws.append_row(headers)
        except gspread.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(
                title=title, rows=2000, cols=len(headers or []) + 5
            )
            if headers:
                ws.append_row(headers)
        cache[key] = ws

    return cache[key]
