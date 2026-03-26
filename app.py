"""MacroStream — Dashboard. Run with: streamlit run app.py"""

import streamlit as st
from datetime import date

st.set_page_config(
    page_title="MacroStream",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.styles import inject_css
from utils.sidebar import render_sidebar
from utils.macros import get_macro_targets, get_weighted_gi
from utils.skin_score import calculate_skin_score, score_color, score_label
from nutrition.alerts import get_all_alerts
from sheets.food_log import get_today_log

inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
active_profile, day_type = render_sidebar()

# ── Page header ───────────────────────────────────────────────────────────────
today_str = date.today().strftime("%A, %d %B %Y")
day_html = (
    '<span class="day-badge day-training">🏋️ Training Day</span>'
    if day_type == "training"
    else '<span class="day-badge day-rest">🛋️ Rest Day</span>'
)
st.markdown(
    f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">'
    f'<h1 style="margin:0;font-size:1.6em;font-weight:800;letter-spacing:-.02em">Dashboard</h1>'
    f'{day_html}</div>'
    f'<p style="color:var(--text-muted);font-size:.82em;margin-bottom:20px">{today_str}</p>',
    unsafe_allow_html=True,
)

if active_profile is None:
    st.markdown(
        '<div class="card" style="text-align:center;padding:40px">'
        '<div style="font-size:2em;margin-bottom:12px">👋</div>'
        '<div style="font-size:1.1em;font-weight:600;margin-bottom:6px">Welcome to MacroStream</div>'
        '<div style="color:var(--text-muted);font-size:.9em">Set up your profile in Settings to get started.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

profile_id = active_profile["id"]
targets = get_macro_targets(active_profile, day_type)
food_log = get_today_log(profile_id)

# ── Macro totals ──────────────────────────────────────────────────────────────
totals = {
    "calories": sum(float(e.get("calories", 0) or 0) for e in food_log),
    "protein":  sum(float(e.get("protein",  0) or 0) for e in food_log),
    "carbs":    sum(float(e.get("carbs",    0) or 0) for e in food_log),
    "fat":      sum(float(e.get("fat",      0) or 0) for e in food_log),
    "fibre":    sum(float(e.get("fibre",    0) or 0) for e in food_log),
    "sat_fat":  sum(float(e.get("sat_fat",  0) or 0) for e in food_log),
    "omega6":   sum(float(e.get("omega6",   0) or 0) for e in food_log),
}


def _ring_color(pct: float) -> str:
    if pct >= 100: return "#EF4444"
    if pct >= 80:  return "#F59E0B"
    return "#4CAF50"


def _macro_ring(label: str, consumed: float, target: float, unit: str, color_override: str | None = None) -> str:
    pct = min(consumed / target * 100, 100) if target > 0 else 0
    color = color_override or _ring_color(pct)
    remaining = max(target - consumed, 0)
    # SVG circle: r=15.9155, circumference≈100
    filled = round(pct, 1)
    gap = 100 - filled
    return f"""
    <div class="ring-card">
      <div class="ring-label">{label}</div>
      <svg width="92" height="92" viewBox="0 0 36 36" class="ring-svg">
        <circle class="ring-bg"   cx="18" cy="18" r="15.9155"/>
        <circle class="ring-fill" cx="18" cy="18" r="15.9155"
                stroke="{color}"
                stroke-dasharray="{filled} {gap}"/>
        <text x="18" y="18" class="ring-center" style="font-size:6px;font-weight:700;fill:{color}">
          {int(pct)}%
        </text>
      </svg>
      <div class="ring-value">{consumed:.0f}<span style="font-size:.65em;font-weight:500;color:var(--text-muted)"> / {target:.0f}{unit}</span></div>
      <div class="ring-sub">{remaining:.0f}{unit} left</div>
    </div>
    """


# ── Main layout: rings + skin score ──────────────────────────────────────────
col_rings, col_skin = st.columns([3, 1], gap="medium")

with col_rings:
    st.markdown('<div class="section-label">Today\'s Macros</div>', unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    r1.markdown(_macro_ring("Calories", totals["calories"], targets["calories"], " kcal", "#4CAF50"), unsafe_allow_html=True)
    r2.markdown(_macro_ring("Protein",  totals["protein"],  targets["protein"],  "g",     "#60A5FA"), unsafe_allow_html=True)
    r3.markdown(_macro_ring("Carbs",    totals["carbs"],    targets["carbs"],    "g",     "#FCD34D"), unsafe_allow_html=True)
    r4.markdown(_macro_ring("Fat",      totals["fat"],      targets["fat"],      "g",     "#C084FC"), unsafe_allow_html=True)

    # Secondary metrics row
    avg_gi = get_weighted_gi(food_log)
    gi_val = f"{avg_gi:.0f}" if avg_gi else "—"
    gi_color = "#EF4444" if avg_gi and avg_gi > 55 else "var(--text)"

    st.markdown(f"""
    <div class="chip-grid" style="margin-top:10px">
      <div class="chip">
        <div class="chip-label">Fibre</div>
        <div class="chip-value">{totals['fibre']:.1f}g</div>
        <div class="chip-sub">target {targets['fibre']}g</div>
      </div>
      <div class="chip">
        <div class="chip-label">Sat Fat</div>
        <div class="chip-value" style="color:{'#EF4444' if totals['sat_fat'] > targets['sat_fat_cap'] else 'var(--text)'}">{totals['sat_fat']:.1f}g</div>
        <div class="chip-sub">cap {targets['sat_fat_cap']}g</div>
      </div>
      <div class="chip">
        <div class="chip-label">Omega-6</div>
        <div class="chip-value" style="color:{'#F59E0B' if totals['omega6'] > targets['omega6_cap'] else 'var(--text)'}">{totals['omega6']:.1f}g</div>
        <div class="chip-sub">cap {targets['omega6_cap']}g</div>
      </div>
      <div class="chip">
        <div class="chip-label">Avg GI</div>
        <div class="chip-value" style="color:{gi_color}">{gi_val}</div>
        <div class="chip-sub">target ≤55</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_skin:
    st.markdown('<div class="section-label">Skin Score</div>', unsafe_allow_html=True)
    skin = calculate_skin_score(food_log, targets)
    color = score_color(skin)
    label = score_label(skin)
    st.markdown(f"""
    <div class="skin-card">
      <div class="skin-score" style="color:{color}">{skin:.1f}</div>
      <div class="skin-label" style="color:{color}">{label}</div>
      <div class="skin-sub">out of 10</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Alert feed ────────────────────────────────────────────────────────────────
alerts = get_all_alerts(food_log, targets, day_type)
st.markdown('<div class="section-label">Alerts & Indicators</div>', unsafe_allow_html=True)
if alerts:
    icons = {"red": "🔴", "yellow": "🟡", "green": "🟢"}
    for a in alerts:
        st.markdown(
            f'<div class="alert-pill alert-{a["level"]}">'
            f'<span>{icons.get(a["level"], "")}</span>'
            f'<span>{a["message"]}</span></div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        '<div class="card" style="text-align:center;padding:14px;color:var(--text-muted);font-size:.85em">'
        'No alerts — log food to see insights.</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Today's log ───────────────────────────────────────────────────────────────
log_col, refresh_col = st.columns([6, 1])
log_col.markdown('<div class="section-label">Today\'s Log</div>', unsafe_allow_html=True)
if refresh_col.button("↺ Refresh", key="refresh"):
    get_today_log.clear()
    st.rerun()

if not food_log:
    st.markdown(
        '<div class="card" style="text-align:center;padding:20px;color:var(--text-muted);font-size:.85em">'
        'Nothing logged yet. Head to <b>Log Food</b> to add meals.</div>',
        unsafe_allow_html=True,
    )
else:
    meal_icons = {"Breakfast": "🌅", "Lunch": "☀️", "Dinner": "🌙", "Snack": "🍎"}
    meals_order = ["Breakfast", "Lunch", "Dinner", "Snack"]
    meals_data: dict[str, list] = {m: [] for m in meals_order}
    for entry in food_log:
        meal = str(entry.get("meal", "Snack")).capitalize()
        meals_data.setdefault(meal, []).append(entry)

    for meal_name in meals_order:
        entries = meals_data[meal_name]
        if not entries:
            continue
        meal_kcal = sum(float(e.get("calories", 0) or 0) for e in entries)
        icon = meal_icons.get(meal_name, "🍽️")

        rows_html = ""
        for e in entries:
            rows_html += (
                f'<div class="food-item">'
                f'<span class="fi-name">{str(e.get("food_name","")).title()} '
                f'<span style="color:var(--text-muted);font-size:.85em">({float(e.get("quantity_g",0)):.0f}g)</span></span>'
                f'<span class="fi-kcal">{float(e.get("calories",0) or 0):.0f} kcal</span>'
                f'<span class="fi-macro">P {float(e.get("protein",0) or 0):.1f}g</span>'
                f'<span class="fi-macro">C {float(e.get("carbs",0) or 0):.1f}g</span>'
                f'<span class="fi-macro">F {float(e.get("fat",0) or 0):.1f}g</span>'
                f'</div>'
            )

        st.markdown(f"""
        <div class="card-sm" style="margin-bottom:8px">
          <div class="meal-head">
            <span class="meal-name">{icon} {meal_name}</span>
            <span class="meal-kcal">{meal_kcal:.0f} kcal</span>
          </div>
          {rows_html}
        </div>
        """, unsafe_allow_html=True)
