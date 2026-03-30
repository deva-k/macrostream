"""Log Food — search, confirm macros, add to log."""

import streamlit as st
from datetime import date

st.set_page_config(page_title="Log Food · MacroStream", page_icon="🍽️", layout="wide")

from utils.styles import inject_css
from utils.sidebar import render_sidebar
from utils.macros import get_macro_targets
from nutrition.search import get_nutrition, get_nutrition_from_image
from nutrition.alerts import get_food_alerts
import re as _re
from sheets.food_log import add_food_entry, get_today_log, delete_food_entry, cache_food

inject_css()
active_profile, day_type = render_sidebar()

st.markdown(
    '<h1 style="margin:0 0 4px;font-size:1.6em;font-weight:800;letter-spacing:-.02em">Log Food</h1>'
    '<p style="color:var(--text-muted);font-size:.82em;margin-bottom:20px">Search any food — macros auto-scale to your quantity</p>',
    unsafe_allow_html=True,
)

if active_profile is None:
    st.stop()

profile_id = active_profile["id"]
targets = get_macro_targets(active_profile, day_type)

# ── Quick-add templates ───────────────────────────────────────────────────────
OVERNIGHT_OATS = [
    {"food_name": "rolled oats",  "quantity_g": 42},
    {"food_name": "skyr",         "quantity_g": 100},
    {"food_name": "whey protein", "quantity_g": 30},
    {"food_name": "chia seeds",   "quantity_g": 12},
    {"food_name": "flax seeds",   "quantity_g": 10},
    {"food_name": "almonds",      "quantity_g": 6},
]
FAVOURITE_FOODS = [
    "grilled chicken breast 150g", "salmon fillet 150g", "whole eggs 2",
    "lentils 100g", "chickpeas 100g", "sweet potato 150g",
    "brown rice 80g", "sona masoori rice 80g", "quinoa 80g",
]

if "pending_food" not in st.session_state:
    st.session_state.pending_food = None
if "search_query" not in st.session_state:
    st.session_state.search_query = ""


def _resolve_and_set(query: str) -> None:
    with st.spinner(f"Looking up '{query}'…"):
        result = get_nutrition(query)
    if result:
        st.session_state.pending_food = result
        st.session_state.search_query = query
    else:
        st.error(f"Could not find nutrition data for **'{query}'**. Try rephrasing or check your Gemini API key.")


# ── Meal selector + search ────────────────────────────────────────────────────
from datetime import datetime as _dt
_hour = _dt.now().hour + _dt.now().minute / 60
_default_meal = "Breakfast" if _hour < 11.5 else ("Lunch" if _hour < 17 else "Dinner")
_meal_options = ["Breakfast", "Lunch", "Dinner", "Snack"]

col_meal, col_search, col_btn = st.columns([1.4, 4, 0.8])
meal = col_meal.selectbox("Meal", _meal_options, index=_meal_options.index(_default_meal), key="meal_selector", label_visibility="collapsed")
query_input = col_search.text_input(
    "Search",
    placeholder="e.g. grilled chicken breast 150g  ·  mutton curry 200g  ·  oats 50g",
    label_visibility="collapsed",
    key="food_query_input",
)
search_clicked = col_btn.button("Search 🔍", use_container_width=True, type="primary")

if search_clicked and query_input.strip():
    _resolve_and_set(query_input.strip())

# ── Quick-add ─────────────────────────────────────────────────────────────────
with st.expander("⚡ Quick Add — Favourites & Templates"):
    if st.button("🥣 Overnight Oats → Breakfast", use_container_width=True, type="primary"):
        added = 0
        for item in OVERNIGHT_OATS:
            result = get_nutrition(f"{item['food_name']} {item['quantity_g']}g")
            if result:
                entry = {
                    "date": date.today().isoformat(), "meal": "Breakfast",
                    "food_name": result["food_name"], "quantity_g": result["quantity_g"],
                    "calories": result.get("calories", 0), "protein": result.get("protein", 0),
                    "carbs": result.get("carbs", 0), "fat": result.get("fat", 0),
                    "fibre": result.get("fibre", 0), "sat_fat": result.get("sat_fat", 0),
                    "omega6": result.get("omega6", 0), "gi": result.get("gi", ""),
                    "day_type": day_type,
                }
                add_food_entry(profile_id, entry)
                added += 1
        st.toast(f"✅ Added overnight oats ({added} items) to Breakfast!", icon="✅")
        st.rerun()

    st.markdown('<div style="font-size:.72em;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-muted);margin:12px 0 6px">Favourites</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, fav in enumerate(FAVOURITE_FOODS):
        if cols[i % 3].button(fav, key=f"fav_{i}", use_container_width=True):
            _resolve_and_set(fav)

# ── Nutrition label scan ──────────────────────────────────────────────────────
with st.expander("📷 Scan Nutrition Label"):
    import os as _os
    try:
        gemini_ready = bool(st.secrets.get("GEMINI_API_KEY") or _os.getenv("GEMINI_API_KEY"))
    except Exception:
        gemini_ready = bool(_os.getenv("GEMINI_API_KEY"))
    if not gemini_ready:
        st.warning("Add a **GEMINI_API_KEY** in your `.env` / Streamlit secrets to enable label scanning. It's free at aistudio.google.com.")
    else:
        st.markdown(
            '<div style="font-size:.82em;color:var(--text-muted);margin-bottom:8px">'
            'Point your camera at any nutrition facts panel — Gemini reads the macros instantly. '
            'Free, works in any language.</div>',
            unsafe_allow_html=True,
        )

        def _run_scan(img_bytes: bytes, mime: str) -> None:
            with st.spinner("Reading nutrition label…"):
                result = get_nutrition_from_image(img_bytes, mime)
            if result:
                st.session_state.pending_food = result
                st.session_state.search_query = result.get("food_name", "scanned food")
                st.rerun()
            else:
                st.error("Could not read the label. Try a clearer photo, or enter the food manually above.")

        tab_cam, tab_upload = st.tabs(["📷 Camera", "📁 Upload File"])

        with tab_cam:
            st.markdown(
                '<div style="font-size:.78em;color:var(--text-muted);margin-bottom:6px">'
                'On mobile this opens your camera directly. Photo is scanned automatically.</div>',
                unsafe_allow_html=True,
            )
            camera_img = st.camera_input("Take a photo of the nutrition label", label_visibility="collapsed", key="label_camera")
            if camera_img is not None:
                # Auto-scan as soon as a photo is taken; avoid re-scanning the same frame
                img_id = hash(camera_img.getvalue())
                if st.session_state.get("_last_cam_scan") != img_id:
                    st.session_state["_last_cam_scan"] = img_id
                    _run_scan(camera_img.getvalue(), "image/jpeg")

        with tab_upload:
            uploaded = st.file_uploader(
                "Upload nutrition label",
                type=["jpg", "jpeg", "png", "webp", "heic"],
                label_visibility="collapsed",
                key="label_upload",
            )
            if uploaded is not None:
                col_img, col_btn = st.columns([3, 1])
                col_img.image(uploaded, use_container_width=True)
                if col_btn.button("Scan Label 📷", use_container_width=True, type="primary", key="scan_btn"):
                    _run_scan(uploaded.read(), uploaded.type or "image/jpeg")

# ── Confirmation card ─────────────────────────────────────────────────────────
pf = st.session_state.pending_food
if pf:
    food_key = pf.get("food_name", "")
    per100 = {k[len("_per100_"):]: v for k, v in pf.items() if k.startswith("_per100_")}
    _CF_MACROS = ["calories", "protein", "carbs", "fat", "fibre", "sat_fat", "omega6"]

    # Egg detection — use count input instead of grams
    _EGG_G = 60.0  # large egg ≈ 60 g
    _is_egg = any(t in food_key.lower() for t in ["egg"])

    def _per100_val(m: str) -> float:
        """Return per-100g base value for macro m, deriving it if _per100_ keys are absent."""
        if m in per100 and per100[m] is not None:
            return float(per100[m])
        # Fall back: derive per-100g from the original quantity's value
        orig_qty = max(float(pf.get("quantity_g") or 100), 1)
        return float(pf.get(m) or 0) * 100.0 / orig_qty

    def _apply_scaled_ss(qty_g: float) -> None:
        factor = qty_g / 100.0
        for m in _CF_MACROS:
            st.session_state[f"cf_{m}"] = round(_per100_val(m) * factor, 1)
        gi_base = per100.get("gi") if "gi" in per100 and per100.get("gi") is not None else (pf.get("gi") or 0)
        st.session_state["cf_gi"] = float(gi_base or 0)

    if st.session_state.get("_cf_food_key") != food_key:
        st.session_state["_cf_food_key"] = food_key
        # Leave name blank for label scans so the user must type it
        st.session_state["cf_name"] = "" if pf.get("source") == "label_scan" else food_key.title()
        init_qty = float(pf.get("quantity_g", 100))
        if _is_egg:
            init_count = max(1, round(init_qty / _EGG_G))
            st.session_state["cf_egg_count"] = init_count
            init_qty = init_count * _EGG_G
        st.session_state["cf_qty"] = init_qty
        st.session_state["_cf_last_qty"] = init_qty
        _apply_scaled_ss(init_qty)

    if _is_egg:
        current_qty = float(st.session_state.get("cf_egg_count", 1)) * _EGG_G
    else:
        current_qty = float(st.session_state.get("cf_qty", pf.get("quantity_g", 100)))
    if current_qty != st.session_state.get("_cf_last_qty"):
        st.session_state["cf_qty"] = current_qty
        _apply_scaled_ss(current_qty)
        st.session_state["_cf_last_qty"] = current_qty

    # RED alerts
    for alert in get_food_alerts(food_key):
        if alert["level"] == "red":
            st.markdown(f'<div class="alert-pill alert-red">🔴 {alert["message"]}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Macro preview badges
    kcal = st.session_state.get("cf_calories", 0)
    prot = st.session_state.get("cf_protein", 0)
    carb = st.session_state.get("cf_carbs", 0)
    fat_ = st.session_state.get("cf_fat", 0)
    fib_ = st.session_state.get("cf_fibre", 0)
    src  = pf.get("source", "unknown")
    st.markdown(
        f'<div class="section-label">Confirm &amp; Edit — <span style="font-weight:400;text-transform:none;letter-spacing:0">{food_key.title()}</span></div>'
        f'<div class="badges">'
        f'<span class="badge badge-kcal">🔥 {kcal:.0f} kcal</span>'
        f'<span class="badge badge-prot">💪 {prot:.1f}g protein</span>'
        f'<span class="badge badge-carb">🌾 {carb:.1f}g carbs</span>'
        f'<span class="badge badge-fat">🥑 {fat_:.1f}g fat</span>'
        f'<span class="badge badge-fib">🌿 {fib_:.1f}g fibre</span>'
        f'<span class="badge badge-src">via {src}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.container():
        c1, c2 = st.columns([3, 1])
        food_name = c1.text_input(
            "Food name *",
            placeholder="Enter food name…" if pf.get("source") == "label_scan" else "",
            key="cf_name",
        )
        if _is_egg:
            st.number_input("Count (eggs) — change to rescale all macros", min_value=1, max_value=20, step=1, key="cf_egg_count")
            quantity_g = st.session_state["cf_egg_count"] * _EGG_G
        else:
            st.number_input("Quantity (g) — change to rescale all macros", min_value=0.0, step=5.0, key="cf_qty")
            quantity_g = st.session_state["cf_qty"]

        st.markdown(
            '<div style="font-size:.75em;color:var(--text-muted);margin:8px 0 4px">'
            'Fine-tune individual values if needed — '
            '<span style="color:var(--text)">corrections are saved back to the cache so next search uses your values</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
        ec1.number_input("Calories (kcal)", min_value=0.0, step=1.0,                   key="cf_calories")
        ec2.number_input("Protein (g)",     min_value=0.0, step=0.1,                   key="cf_protein")
        ec3.number_input("Carbs (g)",       min_value=0.0, step=0.1,                   key="cf_carbs")
        ec4.number_input("Fat (g)",         min_value=0.0, step=0.1,                   key="cf_fat")
        ec5.number_input("Fibre (g)",       min_value=0.0, step=0.1,                   key="cf_fibre")
        ec6, ec7, ec8, _ = st.columns(4)
        ec6.number_input("Sat Fat (g)",  min_value=0.0, step=0.1,                      key="cf_sat_fat")
        ec7.number_input("Omega-6 (g)", min_value=0.0, step=0.1,                      key="cf_omega6")
        ec8.number_input("GI (0–100)",  min_value=0.0, max_value=100.0, step=1.0,     key="cf_gi")

        col1, col2 = st.columns([3, 1])
        if col1.button("✅ Add to Log", use_container_width=True, type="primary"):
            if not food_name.strip():
                st.error("Please enter a food name before adding to the log.")
                st.stop()
            gi_raw = st.session_state.get("cf_gi", 0)
            entry = {
                "date": date.today().isoformat(), "meal": meal,
                "food_name": food_name.lower().strip(), "quantity_g": quantity_g,
                "calories": st.session_state.get("cf_calories", 0),
                "protein":  st.session_state.get("cf_protein", 0),
                "carbs":    st.session_state.get("cf_carbs", 0),
                "fat":      st.session_state.get("cf_fat", 0),
                "fibre":    st.session_state.get("cf_fibre", 0),
                "sat_fat":  st.session_state.get("cf_sat_fat", 0),
                "omega6":   st.session_state.get("cf_omega6", 0),
                "gi":       int(gi_raw) if gi_raw else "",
                "day_type": day_type,
            }
            if add_food_entry(profile_id, entry):
                # Write back to FoodCache with the user's confirmed name + final macros.
                # Dividing by quantity_g gives per-100g — so manual corrections persist to
                # future searches. get_cached_food returns the LAST row, so this overrides
                # any previously cached (possibly wrong) values.
                if quantity_g > 0:
                    _confirmed_name = food_name.lower().strip()
                    _food_key = _re.sub(r"\s+", "_", _confirmed_name)
                    _gi_val = st.session_state.get("cf_gi", 0)
                    cache_food(_food_key, {
                        "food_name": _confirmed_name,
                        **{
                            f"{m}_per100": round(
                                float(st.session_state.get(f"cf_{m}", 0)) / quantity_g * 100, 2
                            )
                            for m in ["calories", "protein", "carbs", "fat", "fibre", "sat_fat", "omega6"]
                        },
                        "gi": int(_gi_val) if _gi_val else "",
                    })
                st.toast(f"✅ Added {food_name} to {meal}!", icon="✅")
                for k in ["_cf_food_key", "_cf_last_qty", "cf_qty", "cf_name",
                          "cf_calories", "cf_protein", "cf_carbs", "cf_fat",
                          "cf_fibre", "cf_sat_fat", "cf_omega6", "cf_gi"]:
                    st.session_state.pop(k, None)
                st.session_state.pending_food = None
                st.session_state.search_query = ""
                st.rerun()
            else:
                st.error("Failed to save — check your Google Sheets connection.")

        if col2.button("✖ Cancel", use_container_width=True):
            for k in ["_cf_food_key", "_cf_last_qty", "cf_qty"]:
                st.session_state.pop(k, None)
            st.session_state.pending_food = None
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ── Today's log ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Today\'s Log</div>', unsafe_allow_html=True)
food_log = get_today_log(profile_id)

if not food_log:
    st.markdown(
        '<div class="card" style="text-align:center;padding:20px;color:var(--text-muted);font-size:.85em">'
        'Nothing logged yet.</div>',
        unsafe_allow_html=True,
    )
else:
    meal_icons = {"Breakfast": "🌅", "Lunch": "☀️", "Dinner": "🌙", "Snack": "🍎"}
    meals_order = ["Breakfast", "Lunch", "Dinner", "Snack"]
    for meal_name in meals_order:
        entries = [e for e in food_log if str(e.get("meal", "")).capitalize() == meal_name]
        if not entries:
            continue
        meal_kcal = sum(float(e.get("calories", 0) or 0) for e in entries)
        icon = meal_icons.get(meal_name, "🍽️")
        with st.expander(f"{icon} **{meal_name}** — {meal_kcal:.0f} kcal"):
            for e in entries:
                col_name, col_cal, col_p, col_c, col_f, col_del = st.columns([3, 1, 1, 1, 1, 0.5])
                fname = str(e.get('food_name', '')).lower()
                qty_g = float(e.get('quantity_g', 0))
                if "egg" in fname and qty_g > 0:
                    qty_label = f"{round(qty_g / 60)} egg{'s' if round(qty_g / 60) != 1 else ''}"
                else:
                    qty_label = f"{qty_g:.0f}g"
                col_name.markdown(f"**{str(e.get('food_name','')).title()}** <span style='color:var(--text-muted);font-size:.85em'>({qty_label})</span>", unsafe_allow_html=True)
                col_cal.markdown(f"<span style='font-weight:600'>{float(e.get('calories',0) or 0):.0f}</span> kcal", unsafe_allow_html=True)
                col_p.markdown(f"<span style='color:#93C5FD'>P</span> {float(e.get('protein',0) or 0):.1f}g", unsafe_allow_html=True)
                col_c.markdown(f"<span style='color:#FCD34D'>C</span> {float(e.get('carbs',0) or 0):.1f}g", unsafe_allow_html=True)
                col_f.markdown(f"<span style='color:#C4B5FD'>F</span> {float(e.get('fat',0) or 0):.1f}g", unsafe_allow_html=True)
                if col_del.button("🗑", key=f"del_{e.get('id')}"):
                    delete_food_entry(profile_id, str(e.get("id")))
                    st.rerun()
