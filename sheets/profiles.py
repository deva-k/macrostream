"""Profile CRUD against the 'Profiles' sheet tab."""

import uuid
from datetime import datetime

import streamlit as st

from sheets.client import get_spreadsheet, get_or_create_worksheet, retry_on_quota

SHEET_NAME = "Profiles"
HEADERS = [
    "id", "name", "gender", "weight_kg", "height_cm",
    "age", "training_days", "goal", "restrictions", "created_at",
]


def _ws():
    ss = get_spreadsheet()
    if ss is None:
        return None
    return get_or_create_worksheet(ss, SHEET_NAME, HEADERS)


# TTL = 5 min — profiles change rarely; sidebar reads this on every rerun
@st.cache_data(ttl=300, show_spinner=False)
def get_all_profiles() -> list[dict]:
    ws = _ws()
    if ws is None:
        return []
    try:
        records = _read_records(ws)
        return [dict(r) for r in records if r.get("id")]
    except Exception:
        return []


@retry_on_quota()
def _read_records(ws):
    return ws.get_all_records()


def save_profile(profile: dict) -> bool:
    ws = _ws()
    if ws is None:
        return False

    if not profile.get("id"):
        profile["id"] = str(uuid.uuid4())[:8]
    if not profile.get("created_at"):
        profile["created_at"] = datetime.now().isoformat()

    def _row(p):
        return [
            p.get("id", ""),
            p.get("name", ""),
            p.get("gender", "male"),
            p.get("weight_kg", 80),
            p.get("height_cm", 175),
            p.get("age", 30),
            p.get("training_days", 3),
            p.get("goal", ""),
            p.get("restrictions", ""),
            p.get("created_at", datetime.now().isoformat()),
        ]

    try:
        records = _read_records(ws)
        for i, r in enumerate(records):
            if r.get("id") == profile["id"]:
                _update_row(ws, i + 2, _row(profile))
                get_all_profiles.clear()
                return True
        _append_row(ws, _row(profile))
        get_all_profiles.clear()
        return True
    except Exception:
        return False


@retry_on_quota()
def _update_row(ws, row_num, row_data):
    ws.update(f"A{row_num}:J{row_num}", [row_data])


@retry_on_quota()
def _append_row(ws, row_data):
    ws.append_row(row_data)


def delete_profile(profile_id: str) -> bool:
    ws = _ws()
    if ws is None:
        return False
    try:
        records = _read_records(ws)
        for i, r in enumerate(records):
            if r.get("id") == profile_id:
                _delete_row(ws, i + 2)
                get_all_profiles.clear()
                return True
    except Exception:
        pass
    return False


@retry_on_quota()
def _delete_row(ws, row_num):
    ws.delete_rows(row_num)
