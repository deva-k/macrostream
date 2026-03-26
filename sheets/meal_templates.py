"""Meal template CRUD — per-profile, per-slot templates stored in Sheets."""

import json
import uuid
from datetime import datetime

import streamlit as st

from sheets.client import get_spreadsheet, get_or_create_worksheet, retry_on_quota

SHEET_PREFIX = "MealTemplates_"
HEADERS = ["id", "meal_slot", "day_type", "template_name", "food_items_json", "created_at"]

MEAL_SLOTS = ["Breakfast", "Lunch", "Dinner", "Snack"]

# Pre-loaded defaults seeded on first use per profile
_DEFAULTS = [
    {"meal_slot": "Breakfast", "day_type": "any",      "template_name": "Overnight Oats Bowl",
     "items": [
         {"food_name": "rolled oats",  "quantity_g": 42},
         {"food_name": "skyr",         "quantity_g": 100},
         {"food_name": "whey protein", "quantity_g": 30},
         {"food_name": "chia seeds",   "quantity_g": 12},
         {"food_name": "flax seeds",   "quantity_g": 10},
         {"food_name": "almonds",      "quantity_g": 6},
     ]},
    {"meal_slot": "Lunch", "day_type": "training", "template_name": "Chicken & Chickpeas",
     "items": [
         {"food_name": "grilled chicken breast", "quantity_g": 150},
         {"food_name": "chickpeas",              "quantity_g": 100},
         {"food_name": "olive oil",              "quantity_g": 10},
     ]},
    {"meal_slot": "Lunch", "day_type": "rest", "template_name": "Egg & Lentil Bowl",
     "items": [
         {"food_name": "eggs",        "quantity_g": 150},
         {"food_name": "green lentils","quantity_g": 100},
         {"food_name": "olive oil",   "quantity_g": 10},
     ]},
    {"meal_slot": "Dinner", "day_type": "training", "template_name": "Salmon & Sona Masoori Rice",
     "items": [
         {"food_name": "salmon fillet",      "quantity_g": 150},
         {"food_name": "sona masoori rice",  "quantity_g": 80},
     ]},
    {"meal_slot": "Dinner", "day_type": "rest", "template_name": "Chicken & Sweet Potato",
     "items": [
         {"food_name": "grilled chicken breast", "quantity_g": 150},
         {"food_name": "sweet potato",           "quantity_g": 200},
     ]},
    {"meal_slot": "Snack", "day_type": "any", "template_name": "Casein Night Snack",
     "items": [
         {"food_name": "skyr",    "quantity_g": 200},
         {"food_name": "walnuts", "quantity_g": 15},
     ]},
]


# ── Internal helpers ───────────────────────────────────────────────────────────

def _ws(profile_id: str):
    ss = get_spreadsheet()
    if ss is None:
        return None
    return get_or_create_worksheet(ss, f"{SHEET_PREFIX}{profile_id}", HEADERS)


@retry_on_quota()
def _read(ws):
    return ws.get_all_records()


@retry_on_quota()
def _write(ws, row):
    ws.append_row(row)


@retry_on_quota()
def _update(ws, row_num, row):
    ws.update(f"A{row_num}:F{row_num}", [row])


@retry_on_quota()
def _delete(ws, row_num):
    ws.delete_rows(row_num)


def _to_row(t: dict) -> list:
    return [
        t["id"],
        t.get("meal_slot", "Breakfast"),
        t.get("day_type", "any"),
        t.get("template_name", ""),
        json.dumps(t.get("items", [])),
        t.get("created_at", datetime.now().isoformat()),
    ]


# ── Public API ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def get_templates(profile_id: str) -> list[dict]:
    ws = _ws(profile_id)
    if ws is None:
        return []
    try:
        rows = _read(ws)
        result = []
        for r in rows:
            if not r.get("id"):
                continue
            t = dict(r)
            try:
                t["items"] = json.loads(t.get("food_items_json") or "[]")
            except Exception:
                t["items"] = []
            result.append(t)
        return result
    except Exception:
        return []


def seed_defaults(profile_id: str) -> None:
    """Write default templates on first use. No-op if templates already exist."""
    if get_templates(profile_id):
        return
    ws = _ws(profile_id)
    if ws is None:
        return
    for d in _DEFAULTS:
        _write(ws, _to_row({**d, "id": str(uuid.uuid4())[:8], "created_at": datetime.now().isoformat()}))
    get_templates.clear()


def save_template(profile_id: str, template: dict) -> bool:
    ws = _ws(profile_id)
    if ws is None:
        return False
    is_new = not template.get("id")
    if is_new:
        template["id"] = str(uuid.uuid4())[:8]
        template["created_at"] = datetime.now().isoformat()
    try:
        if is_new:
            _write(ws, _to_row(template))
        else:
            rows = _read(ws)
            for i, r in enumerate(rows):
                if r.get("id") == template["id"]:
                    _update(ws, i + 2, _to_row(template))
                    break
        get_templates.clear()
        return True
    except Exception:
        return False


def delete_template(profile_id: str, template_id: str) -> bool:
    ws = _ws(profile_id)
    if ws is None:
        return False
    try:
        rows = _read(ws)
        for i, r in enumerate(rows):
            if r.get("id") == template_id:
                _delete(ws, i + 2)
                get_templates.clear()
                return True
    except Exception:
        pass
    return False
