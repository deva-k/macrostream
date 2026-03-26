"""Log Food — search, confirm macros, add to log."""

import streamlit as st
from datetime import date

st.set_page_config(page_title="Log Food · MacroStream", page_icon="🍽️", layout="wide")

from utils.styles import inject_css
from utils.sidebar import render_sidebar
from utils.macros import get_macro_targets
from nutrition.search import get_nutrition
from nutrition.alerts import get_food_alerts
from sheets.food_log import add_food_entry, get_today_log, delete_food_entry

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
col_meal, col_search, col_btn = st.columns([1.4, 4, 0.8])
meal = col_meal.selectbox("Meal", ["Breakfast", "Lunch", "Dinner", "Snack"], key="meal_selector", label_visibility="collapsed")
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

# ── Confirmation card ─────────────────────────────────────────────────────────
pf = st.session_state.pending_food
if pf:
    food_key = pf.get("food_name", "")
    per100 = {k[len("_per100_"):]: v for k, v in pf.items() if k.startswith("_per100_")}
    _CF_MACROS = ["calories", "protein", "carbs", "fat", "fibre", "sat_fat", "omega6"]

    def _apply_scaled_ss(qty_g: float) -> None:
        factor = qty_g / 100.0
        for m in _CF_MACROS:
            raw = per100.get(m) or pf.get(m) or 0
            st.session_state[f"cf_{m}"] = round(float(raw) * factor, 1)
        gi = per100.get("gi") or pf.get("gi") or 0
        st.session_state["cf_gi"] = float(gi or 0)

    if st.session_state.get("_cf_food_key") != food_key:
        st.session_state["_cf_food_key"] = food_key
        init_qty = float(pf.get("quantity_g", 100))
        st.session_state["cf_qty"] = init_qty
        st.session_state["_cf_last_qty"] = init_qty
        _apply_scaled_ss(init_qty)

    current_qty = float(st.session_state.get("cf_qty", pf.get("quantity_g", 100)))
    if current_qty != st.session_state.get("_cf_last_qty"):
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
        food_name = c1.text_input("Food name", value=food_key.title(), key="cf_name")
        st.number_input("Quantity (g) — change to rescale all macros", min_value=0.0, step=5.0, key="cf_qty")
        quantity_g = st.session_state["cf_qty"]

        st.markdown('<div style="font-size:.75em;color:var(--text-muted);margin:8px 0 4px">Fine-tune individual values if needed</div>', unsafe_allow_html=True)
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
                col_name.markdown(f"**{str(e.get('food_name','')).title()}** <span style='color:var(--text-muted);font-size:.85em'>({float(e.get('quantity_g',0)):.0f}g)</span>", unsafe_allow_html=True)
                col_cal.markdown(f"<span style='font-weight:600'>{float(e.get('calories',0) or 0):.0f}</span> kcal", unsafe_allow_html=True)
                col_p.markdown(f"<span style='color:#93C5FD'>P</span> {float(e.get('protein',0) or 0):.1f}g", unsafe_allow_html=True)
                col_c.markdown(f"<span style='color:#FCD34D'>C</span> {float(e.get('carbs',0) or 0):.1f}g", unsafe_allow_html=True)
                col_f.markdown(f"<span style='color:#C4B5FD'>F</span> {float(e.get('fat',0) or 0):.1f}g", unsafe_allow_html=True)
                if col_del.button("🗑", key=f"del_{e.get('id')}"):
                    delete_food_entry(profile_id, str(e.get("id")))
                    st.rerun()
