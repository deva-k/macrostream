"""Food log and food cache CRUD against Google Sheets."""

from datetime import date, datetime

import streamlit as st

from sheets.client import get_spreadsheet, get_or_create_worksheet, retry_on_quota

LOG_HEADERS = [
    "id", "date", "meal", "food_name", "quantity_g",
    "calories", "protein", "carbs", "fat", "fibre",
    "sat_fat", "omega6", "gi", "day_type", "timestamp",
]

CACHE_HEADERS = [
    "food_key", "food_name",
    "calories_per100", "protein_per100", "carbs_per100", "fat_per100",
    "fibre_per100", "sat_fat_per100", "omega6_per100", "gi", "timestamp",
]


def _log_ws(profile_id: str):
    ss = get_spreadsheet()
    if ss is None:
        return None
    return get_or_create_worksheet(ss, f"FoodLog_{profile_id}", LOG_HEADERS)


def _cache_ws():
    ss = get_spreadsheet()
    if ss is None:
        return None
    return get_or_create_worksheet(ss, "FoodCache", CACHE_HEADERS)


# ── Retry-wrapped raw API calls ────────────────────────────────────────────────

@retry_on_quota()
def _get_all_records(ws):
    return ws.get_all_records()

@retry_on_quota()
def _append_row(ws, row):
    ws.append_row(row)

@retry_on_quota()
def _delete_row(ws, row_num):
    ws.delete_rows(row_num)


# ── Cached reads ───────────────────────────────────────────────────────────────

# TTL = 2 min — short enough to reflect new log entries, long enough to avoid hammering API
@st.cache_data(ttl=120, show_spinner=False)
def get_today_log(profile_id: str) -> list[dict]:
    ws = _log_ws(profile_id)
    if ws is None:
        return []
    today = date.today().isoformat()
    try:
        records = _get_all_records(ws)
        return [dict(r) for r in records if str(r.get("date", "")) == today]
    except Exception:
        return []


# TTL = 10 min — historical data changes infrequently
@st.cache_data(ttl=600, show_spinner=False)
def get_log_range(profile_id: str, start_date: str, end_date: str) -> list[dict]:
    ws = _log_ws(profile_id)
    if ws is None:
        return []
    try:
        records = _get_all_records(ws)
        return [
            dict(r) for r in records
            if r.get("date") and start_date <= str(r["date"]) <= end_date
        ]
    except Exception:
        return []


# ── Writes ─────────────────────────────────────────────────────────────────────

def add_food_entry(profile_id: str, entry: dict) -> bool:
    ws = _log_ws(profile_id)
    if ws is None:
        return False

    row_id = datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]
    try:
        _append_row(ws, [
            row_id,
            entry.get("date", date.today().isoformat()),
            entry.get("meal", ""),
            entry.get("food_name", ""),
            round(float(entry.get("quantity_g", 0)), 1),
            round(float(entry.get("calories", 0)), 1),
            round(float(entry.get("protein", 0)), 1),
            round(float(entry.get("carbs", 0)), 1),
            round(float(entry.get("fat", 0)), 1),
            round(float(entry.get("fibre", 0)), 1),
            round(float(entry.get("sat_fat", 0)), 1),
            round(float(entry.get("omega6", 0)), 1),
            entry.get("gi", ""),
            entry.get("day_type", "training"),
            datetime.now().isoformat(),
        ])
        get_today_log.clear()
        get_log_range.clear()
        return True
    except Exception:
        return False


def delete_food_entry(profile_id: str, entry_id: str) -> bool:
    ws = _log_ws(profile_id)
    if ws is None:
        return False
    try:
        records = _get_all_records(ws)
        for i, r in enumerate(records):
            if str(r.get("id")) == str(entry_id):
                _delete_row(ws, i + 2)
                get_today_log.clear()
                get_log_range.clear()
                return True
    except Exception:
        pass
    return False


# ── Food cache ─────────────────────────────────────────────────────────────────

# TTL = 1 hour — nutrition data for a food name doesn't change
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_food(food_key: str) -> dict | None:
    ws = _cache_ws()
    if ws is None:
        return None
    try:
        records = _get_all_records(ws)
        for r in records:
            if r.get("food_key") == food_key:
                return dict(r)
    except Exception:
        pass
    return None


def cache_food(food_key: str, data: dict) -> None:
    ws = _cache_ws()
    if ws is None:
        return
    try:
        _append_row(ws, [
            food_key,
            data.get("food_name", ""),
            round(float(data.get("calories_per100", 0)), 1),
            round(float(data.get("protein_per100", 0)), 1),
            round(float(data.get("carbs_per100", 0)), 1),
            round(float(data.get("fat_per100", 0)), 1),
            round(float(data.get("fibre_per100", 0)), 1),
            round(float(data.get("sat_fat_per100", 0)), 1),
            round(float(data.get("omega6_per100", 0)), 1),
            data.get("gi", ""),
            datetime.now().isoformat(),
        ])
        get_cached_food.clear()
    except Exception:
        pass
