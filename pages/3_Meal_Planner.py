"""Meal Planner — customisable per-profile templates."""

import streamlit as st
from datetime import date

st.set_page_config(page_title="Meal Planner · MacroStream", page_icon="📋", layout="wide")

from utils.styles import inject_css
from utils.sidebar import render_sidebar
from sheets.meal_templates import get_templates, save_template, delete_template, seed_defaults, MEAL_SLOTS
from sheets.food_log import add_food_entry, get_today_log
from nutrition.search import get_nutrition

inject_css()
active_profile, day_type = render_sidebar()

st.markdown(
    '<h1 style="margin:0 0 4px;font-size:1.6em;font-weight:800;letter-spacing:-.02em">Meal Planner</h1>'
    '<p style="color:var(--text-muted);font-size:.82em;margin-bottom:20px">Build meal templates and log them with one click</p>',
    unsafe_allow_html=True,
)

if active_profile is None:
    st.stop()

profile_id = active_profile["id"]
seed_defaults(profile_id)

# ── Session state ─────────────────────────────────────────────────────────────
if "mp_editing"       not in st.session_state: st.session_state.mp_editing       = None
if "mp_adding_slot"   not in st.session_state: st.session_state.mp_adding_slot   = None
if "mp_followed_today" not in st.session_state: st.session_state.mp_followed_today = {}


# ── Dynamic item editor ───────────────────────────────────────────────────────
def _render_items(prefix: str) -> None:
    n_key = f"{prefix}_n"
    n = st.session_state.get(n_key, 1)
    for i in range(n):
        c1, c2, c3 = st.columns([5, 1.5, 0.6])
        c1.text_input(
            "Food" if i == 0 else f"Food {i+1}",
            placeholder="e.g. chicken breast",
            key=f"{prefix}_food_{i}",
            label_visibility="visible" if i == 0 else "collapsed",
        )
        c2.number_input(
            "g" if i == 0 else f"g{i}",
            min_value=0.0, step=5.0,
            key=f"{prefix}_qty_{i}",
            label_visibility="visible" if i == 0 else "collapsed",
        )
        if n > 1 and c3.button("✕", key=f"{prefix}_rm_{i}"):
            for j in range(i, n - 1):
                st.session_state[f"{prefix}_food_{j}"] = st.session_state.get(f"{prefix}_food_{j+1}", "")
                st.session_state[f"{prefix}_qty_{j}"]  = st.session_state.get(f"{prefix}_qty_{j+1}", 100.0)
            st.session_state.pop(f"{prefix}_food_{n-1}", None)
            st.session_state.pop(f"{prefix}_qty_{n-1}", None)
            st.session_state[n_key] = n - 1
            st.rerun()
    if st.button("＋ Add item", key=f"{prefix}_add_item"):
        st.session_state[f"{prefix}_food_{n}"] = ""
        st.session_state[f"{prefix}_qty_{n}"]  = 100.0
        st.session_state[n_key] = n + 1
        st.rerun()


def _collect_items(prefix: str) -> list[dict]:
    n = st.session_state.get(f"{prefix}_n", 1)
    return [
        {"food_name": st.session_state.get(f"{prefix}_food_{i}", "").strip().lower(),
         "quantity_g": float(st.session_state.get(f"{prefix}_qty_{i}", 100))}
        for i in range(n)
        if st.session_state.get(f"{prefix}_food_{i}", "").strip()
    ]


def _load_into_edit_state(template: dict) -> None:
    tid  = template["id"]
    prefix = f"mp_edit_{tid}"
    items = template.get("items", [])
    st.session_state[f"{prefix}_n"]        = max(len(items), 1)
    st.session_state[f"{prefix}_name"]     = template.get("template_name", "")
    st.session_state[f"{prefix}_day_type"] = template.get("day_type", "any")
    for i, item in enumerate(items):
        st.session_state[f"{prefix}_food_{i}"] = item.get("food_name", "")
        st.session_state[f"{prefix}_qty_{i}"]  = float(item.get("quantity_g", 100))


def _clear_new_state(slot: str) -> None:
    prefix = f"mp_new_{slot}"
    for k in [k for k in st.session_state if k.startswith(prefix)]:
        del st.session_state[k]


# ── Follow template ───────────────────────────────────────────────────────────
def _follow_template(template: dict, slot: str) -> None:
    items = template.get("items", [])
    if not items:
        st.warning("Template has no food items.")
        return

    added, nutrition_failed, write_failed = 0, [], []
    progress = st.progress(0, text="Logging items…")

    for idx, item in enumerate(items):
        food_name = item.get("food_name", "")
        qty = float(item.get("quantity_g", 100))
        progress.progress((idx + 1) / len(items), text=f"Looking up {food_name.title()}…")

        result = get_nutrition(f"{food_name} {qty:.0f}g")
        if not result:
            nutrition_failed.append(food_name)
            continue

        entry = {
            "date": date.today().isoformat(), "meal": slot,
            "food_name": result["food_name"], "quantity_g": result["quantity_g"],
            "calories": result.get("calories", 0), "protein": result.get("protein", 0),
            "carbs":    result.get("carbs",    0), "fat":     result.get("fat",     0),
            "fibre":    result.get("fibre",    0), "sat_fat": result.get("sat_fat", 0),
            "omega6":   result.get("omega6",   0), "gi":      result.get("gi", ""),
            "day_type": day_type,
        }
        if add_food_entry(profile_id, entry):
            added += 1
        else:
            write_failed.append(food_name)

    progress.empty()

    if added:
        st.session_state.mp_followed_today[template["id"]] = True
        st.toast(f"✅ Logged {added} item(s) from '{template['template_name']}' to {slot}!", icon="✅")

    if nutrition_failed:
        names = ", ".join(f.title() for f in nutrition_failed)
        if not added and not write_failed:
            st.error(
                f"**Nutrition lookup failed for:** {names}\n\n"
                "Check terminal for `[macrostream]` errors. Make sure your Gemini API key is valid."
            )
            return
        st.toast(f"⚠️ No nutrition data for: {names}", icon="⚠️")

    if write_failed:
        st.toast(f"⚠️ Sheets write failed for: {', '.join(f.title() for f in write_failed)}", icon="⚠️")

    get_today_log.clear()
    st.rerun()


# ── Slot filter ───────────────────────────────────────────────────────────────
def _slot_templates(all_templates: list[dict], slot: str) -> list[dict]:
    return [t for t in all_templates
            if t.get("meal_slot") == slot
            and t.get("day_type", "any") in (day_type, "any")]


# ── Render ────────────────────────────────────────────────────────────────────
all_templates = get_templates(profile_id)
DAY_TYPE_LABELS = {"any": "Both days", "training": "Training", "rest": "Rest"}
SLOT_ICONS = {"Breakfast": "🌅", "Lunch": "☀️", "Dinner": "🌙", "Snack": "🍎"}

for slot in MEAL_SLOTS:
    icon = SLOT_ICONS.get(slot, "🍽️")
    st.markdown(f'<div class="section-label">{icon} {slot}</div>', unsafe_allow_html=True)
    slot_templates = _slot_templates(all_templates, slot)

    if not slot_templates:
        st.markdown(
            f'<div style="color:var(--text-muted);font-size:.83em;padding:4px 0 8px">No templates for {slot} on {day_type} days yet.</div>',
            unsafe_allow_html=True,
        )

    for t in slot_templates:
        tid = t["id"]
        is_editing = st.session_state.mp_editing == tid
        was_followed = st.session_state.mp_followed_today.get(tid, False)
        dt_badge = DAY_TYPE_LABELS.get(t.get("day_type", "any"), "")
        followed_html = '<span class="tpl-followed">✅ Followed today</span>' if was_followed else ""

        # Card header
        st.markdown(
            f'<div class="tpl-card {"followed" if was_followed else ""}">'
            f'<span class="tpl-name">{t["template_name"]}</span>'
            f'<span class="tpl-badge">{dt_badge}</span>'
            f'{followed_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

        if not is_editing:
            items_col, btn_col = st.columns([4, 2])
            with items_col:
                for item in t.get("items", []):
                    st.markdown(
                        f'<div class="tpl-item">· {item["food_name"].title()} <span style="color:var(--text-muted)">{float(item["quantity_g"]):.0f}g</span></div>',
                        unsafe_allow_html=True,
                    )
            with btn_col:
                b1, b2, b3 = st.columns(3)
                if b1.button("▶ Follow", key=f"follow_{tid}", use_container_width=True, type="primary",
                              help="Log all items to today's diary"):
                    _follow_template(t, slot)
                if b2.button("✏️ Edit", key=f"edit_{tid}", use_container_width=True):
                    _load_into_edit_state(t)
                    st.session_state.mp_editing = tid
                    st.rerun()
                if b3.button("🗑", key=f"del_{tid}", use_container_width=True, help="Delete"):
                    st.session_state[f"confirm_del_{tid}"] = True

            if st.session_state.get(f"confirm_del_{tid}"):
                st.warning(f"Delete **{t['template_name']}**? This cannot be undone.")
                cy, cn = st.columns(2)
                if cy.button("Delete", key=f"yes_del_{tid}", type="primary"):
                    delete_template(profile_id, tid)
                    st.session_state.pop(f"confirm_del_{tid}", None)
                    st.rerun()
                if cn.button("Cancel", key=f"no_del_{tid}"):
                    st.session_state.pop(f"confirm_del_{tid}", None)
                    st.rerun()

        else:
            prefix = f"mp_edit_{tid}"
            st.markdown('<div style="font-size:.8em;color:var(--text-muted);margin:6px 0 10px">Editing template</div>', unsafe_allow_html=True)
            st.text_input("Template name *", key=f"{prefix}_name")
            st.selectbox("Applies to", ["any", "training", "rest"], key=f"{prefix}_day_type",
                         format_func=lambda x: DAY_TYPE_LABELS[x])
            _render_items(prefix)
            sv, cn = st.columns(2)
            if sv.button("💾 Save", key=f"save_edit_{tid}", use_container_width=True, type="primary"):
                name  = st.session_state.get(f"{prefix}_name", "").strip()
                items = _collect_items(prefix)
                if not name:
                    st.error("Template name is required.")
                elif not items:
                    st.error("Add at least one food item.")
                else:
                    updated = {**t, "template_name": name,
                               "day_type": st.session_state[f"{prefix}_day_type"], "items": items}
                    if save_template(profile_id, updated):
                        st.session_state.mp_editing = None
                        st.rerun()
                    else:
                        st.error("Failed to save — check Sheets connection.")
            if cn.button("✖ Cancel", key=f"cancel_edit_{tid}", use_container_width=True):
                st.session_state.mp_editing = None
                st.rerun()

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Add new template ──────────────────────────────────────────────────────
    if st.session_state.mp_adding_slot == slot:
        prefix = f"mp_new_{slot}"
        if f"{prefix}_n" not in st.session_state:
            st.session_state[f"{prefix}_n"] = 1

        st.markdown(f'<div style="font-size:.85em;font-weight:600;margin:8px 0 10px">New {slot} template</div>', unsafe_allow_html=True)
        st.text_input("Template name *", placeholder="e.g. High-protein bowl", key=f"{prefix}_name")
        st.selectbox("Applies to", ["any", "training", "rest"], key=f"{prefix}_day_type",
                     format_func=lambda x: DAY_TYPE_LABELS[x])
        _render_items(prefix)

        sv2, cn2 = st.columns(2)
        if sv2.button("💾 Save template", key=f"save_new_{slot}", use_container_width=True, type="primary"):
            name  = st.session_state.get(f"{prefix}_name", "").strip()
            items = _collect_items(prefix)
            if not name:
                st.error("Template name is required.")
            elif not items:
                st.error("Add at least one food item.")
            else:
                new_t = {"meal_slot": slot,
                         "day_type": st.session_state.get(f"{prefix}_day_type", "any"),
                         "template_name": name, "items": items}
                if save_template(profile_id, new_t):
                    _clear_new_state(slot)
                    st.session_state.mp_adding_slot = None
                    st.rerun()
                else:
                    st.error("Failed to save — check Sheets connection.")
        if cn2.button("✖ Cancel", key=f"cancel_new_{slot}", use_container_width=True):
            _clear_new_state(slot)
            st.session_state.mp_adding_slot = None
            st.rerun()
    else:
        if st.button(f"＋ Add {slot} template", key=f"add_btn_{slot}"):
            st.session_state.mp_adding_slot = slot
            st.session_state.mp_editing = None
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
