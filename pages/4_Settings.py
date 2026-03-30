"""Settings — profile management, data export, app configuration."""

import streamlit as st
import pandas as pd
import io
from datetime import date, timedelta

st.set_page_config(page_title="Settings · MacroStream", page_icon="⚙️", layout="wide")

from utils.styles import inject_css
from utils.sidebar import render_sidebar
from utils.macros import get_macro_targets
from sheets.profiles import get_all_profiles, save_profile, delete_profile
from sheets.food_log import get_log_range
from sheets.client import is_configured

inject_css()
active_profile, day_type = render_sidebar()

st.markdown(
    '<h1 style="margin:0 0 4px;font-size:1.6em;font-weight:800;letter-spacing:-.02em">Settings</h1>'
    '<p style="color:var(--text-muted);font-size:.82em;margin-bottom:20px">Manage profiles, export data, and configure alerts</p>',
    unsafe_allow_html=True,
)

# ── Connection status ─────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Google Sheets Connection</div>', unsafe_allow_html=True)

if is_configured():
    st.markdown(
        '<div class="alert-pill alert-green">🟢 Google Sheets connected and ready</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="alert-pill alert-red">🔴 Google Sheets not configured</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Setup instructions"):
        st.markdown("""
**1. Create a Google Cloud project**
Enable the **Google Sheets API** and **Google Drive API**.

**2. Create a Service Account**
Download the JSON key file and share your spreadsheet with the service account email (Editor access).

**3. Configure credentials**

Local (`.env` file):
```
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
GOOGLE_SHEET_ID=your_spreadsheet_id
```

Streamlit Cloud (`.streamlit/secrets.toml`):
```toml
GOOGLE_SHEET_ID = "your_spreadsheet_id"
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key = "..."
client_email = "..."
```
        """)

st.markdown("<br>", unsafe_allow_html=True)

# ── Profile management ────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Profiles</div>', unsafe_allow_html=True)

tab_list, tab_create, tab_edit = st.tabs(["All Profiles", "Create New", "Edit Active"])


def _profile_form(prefix: str, defaults: dict | None = None) -> dict | None:
    d = defaults or {}

    name = st.text_input("Name *", value=d.get("name", ""), key=f"{prefix}_name")
    c1, c2, c3 = st.columns(3)
    gender = c1.selectbox("Gender", ["male", "female"],
                           index=0 if d.get("gender", "male") == "male" else 1,
                           key=f"{prefix}_gender")
    weight = c2.number_input("Weight (kg)", value=float(d.get("weight_kg", 80)),
                              min_value=30.0, max_value=250.0, step=0.5, key=f"{prefix}_weight")
    height = c3.number_input("Height (cm)", value=float(d.get("height_cm", 175)),
                              min_value=100.0, max_value=250.0, step=0.5, key=f"{prefix}_height")

    c4, c5 = st.columns(2)
    age = c4.number_input("Age", value=int(d.get("age", 25)), min_value=10, max_value=100,
                           key=f"{prefix}_age")
    training_days = c5.selectbox("Training days / week", [1, 2, 3, 4, 5, 6],
                                  index=[1,2,3,4,5,6].index(int(d.get("training_days", 3))),
                                  key=f"{prefix}_training_days")

    goal = st.text_input("Goal (optional)", value=d.get("goal", "Body recomposition"),
                          key=f"{prefix}_goal")
    restrictions = st.text_input("Dietary restrictions (comma-separated)",
                                  value=d.get("restrictions", "red meat, gluten"),
                                  key=f"{prefix}_restrictions")

    # Live macro preview
    preview_profile = {
        "gender": gender, "weight_kg": weight, "height_cm": height,
        "age": age, "training_days": training_days,
    }
    pt = get_macro_targets(preview_profile, "training")
    pr = get_macro_targets(preview_profile, "rest")

    st.markdown(f"""
<div style="margin:14px 0;padding:14px 16px;background:var(--surface-2);border-radius:10px;border:1px solid var(--border)">
  <div style="font-size:.7em;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-muted);margin-bottom:10px">Calculated targets preview</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
    <div>
      <div style="font-size:.72em;color:var(--text-muted);margin-bottom:4px">🏋️ Training day</div>
      <div style="font-size:.9em;font-weight:600">{pt['calories']} kcal</div>
      <div style="font-size:.78em;color:var(--text-muted)">P {pt['protein']}g · C {pt['carbs']}g · F {pt['fat']}g</div>
    </div>
    <div>
      <div style="font-size:.72em;color:var(--text-muted);margin-bottom:4px">🛋️ Rest day</div>
      <div style="font-size:.9em;font-weight:600">{pr['calories']} kcal</div>
      <div style="font-size:.78em;color:var(--text-muted)">P {pr['protein']}g · C {pr['carbs']}g · F {pr['fat']}g</div>
    </div>
  </div>
  <div style="font-size:.75em;color:var(--text-muted);margin-top:8px;padding-top:8px;border-top:1px solid var(--border)">TDEE ≈ {pt['tdee']} kcal/day</div>
</div>
""", unsafe_allow_html=True)

    if st.button("💾 Save Profile", key=f"{prefix}_save", use_container_width=True, type="primary"):
        if not name.strip():
            st.error("Name is required.")
            return None
        return {
            "id": d.get("id"),
            "name": name.strip(),
            "gender": gender,
            "weight_kg": weight,
            "height_cm": height,
            "age": age,
            "training_days": training_days,
            "goal": goal,
            "restrictions": restrictions,
            "created_at": d.get("created_at"),
        }
    return None


with tab_list:
    profiles = get_all_profiles()
    if not profiles:
        st.markdown(
            '<div class="card" style="text-align:center;padding:30px;color:var(--text-muted);font-size:.85em">'
            'No profiles yet. Create one in the <b>Create New</b> tab.</div>',
            unsafe_allow_html=True,
        )
    else:
        for p in profiles:
            is_active = active_profile and p["id"] == active_profile.get("id")
            t = get_macro_targets(p, "training")
            r = get_macro_targets(p, "rest")
            active_badge = (
                '<span style="display:inline-block;padding:2px 8px;background:rgba(76,175,80,.15);'
                'color:#4CAF50;border-radius:20px;font-size:.72em;font-weight:700;margin-left:8px">Active</span>'
                if is_active else ""
            )
            name_html = (
                f'<span style="font-size:1em;font-weight:700">{p["name"]}</span>'
                f'{active_badge}'
            )
            demographics = (
                f'{p.get("gender","").capitalize()} · {p.get("weight_kg")}kg'
                f' · {p.get("height_cm")}cm · Age {p.get("age")}'
            )
            border_color = "#4CAF50" if is_active else "var(--border)"
            card_html = (
                f'<div style="padding:14px 16px;background:var(--surface-2);border-radius:10px;'
                f'border:1px solid {border_color};margin-bottom:10px">'
                f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">'
                f'<div>{name_html}</div>'
                f'<div style="font-size:.75em;color:var(--text-muted)">{demographics}</div>'
                f'</div>'
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">'
                f'<div style="font-size:.78em;color:var(--text-muted)">🏋️ Training: '
                f'<span style="color:var(--text);font-weight:600">{t["calories"]} kcal</span>'
                f' · P {t["protein"]}g · C {t["carbs"]}g · F {t["fat"]}g</div>'
                f'<div style="font-size:.78em;color:var(--text-muted)">🛋️ Rest: '
                f'<span style="color:var(--text);font-weight:600">{r["calories"]} kcal</span>'
                f' · P {r["protein"]}g · C {r["carbs"]}g · F {r["fat"]}g</div>'
                f'</div></div>'
            )
            if is_active:
                st.markdown(card_html, unsafe_allow_html=True)
            else:
                info_col, btn_col = st.columns([11, 1])
                info_col.markdown(card_html, unsafe_allow_html=True)
                btn_col.markdown("<br>", unsafe_allow_html=True)
                if btn_col.button("🗑️", key=f"del_profile_{p['id']}", help=f"Delete {p['name']}", use_container_width=True):
                    if delete_profile(p["id"]):
                        st.toast(f"Deleted profile '{p['name']}'", icon="🗑️")
                        st.rerun()


with tab_create:
    st.markdown('<div style="font-size:.85em;font-weight:600;margin:4px 0 14px">New Profile</div>', unsafe_allow_html=True)
    new_profile = _profile_form("create")
    if new_profile:
        if save_profile(new_profile):
            st.toast(f"Profile '{new_profile['name']}' created! Select it in the sidebar.", icon="✅")
            st.rerun()
        else:
            st.error("Failed to save — check Google Sheets connection.")


with tab_edit:
    if active_profile is None:
        st.markdown(
            '<div class="card" style="text-align:center;padding:30px;color:var(--text-muted);font-size:.85em">'
            'No active profile. Create one first.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f'<div style="font-size:.85em;font-weight:600;margin:4px 0 14px">Editing: {active_profile["name"]}</div>', unsafe_allow_html=True)
        updated = _profile_form("edit", defaults=dict(active_profile))
        if updated:
            if save_profile(updated):
                st.toast("Profile updated!", icon="✅")
                get_all_profiles.clear()
                st.rerun()
            else:
                st.error("Failed to save.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Data management ───────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Data Management</div>', unsafe_allow_html=True)

if active_profile:
    profile_id = active_profile["id"]
    col_export, col_clear = st.columns(2, gap="large")

    with col_export:
        st.markdown("""
<div style="padding:16px;background:var(--surface-2);border-radius:10px;border:1px solid var(--border)">
  <div style="font-size:.8em;font-weight:700;margin-bottom:10px">⬇️ Export Food Log</div>
  <div style="font-size:.78em;color:var(--text-muted);margin-bottom:12px">Download your log as a CSV file for analysis in Excel or similar.</div>
</div>
""", unsafe_allow_html=True)
        exp_days = st.selectbox("Export period", [7, 30, 90, 365],
                                 format_func=lambda x: f"Last {x} days", key="exp_days")
        if st.button("⬇️ Prepare CSV", use_container_width=True, type="primary"):
            end = date.today()
            start = end - timedelta(days=exp_days)
            records = get_log_range(profile_id, start.isoformat(), end.isoformat())
            if records:
                df = pd.DataFrame(records)
                csv_buf = io.StringIO()
                df.to_csv(csv_buf, index=False)
                st.download_button(
                    "Save CSV",
                    data=csv_buf.getvalue(),
                    file_name=f"macrostream_{active_profile['name']}_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.warning("No data in selected period.")

    with col_clear:
        st.markdown("""
<div style="padding:16px;background:var(--surface-2);border-radius:10px;border:1px solid var(--border)">
  <div style="font-size:.8em;font-weight:700;margin-bottom:10px">🗑️ Clear Today's Log</div>
  <div style="font-size:.78em;color:var(--text-muted);margin-bottom:12px">Permanently delete all food entries logged today. This cannot be undone.</div>
</div>
""", unsafe_allow_html=True)
        if st.button("🗑️ Clear Today's Log", use_container_width=True):
            st.session_state["confirm_clear"] = True

        if st.session_state.get("confirm_clear"):
            st.warning("Are you sure? This cannot be undone.")
            c_yes, c_no = st.columns(2)
            if c_yes.button("Delete", type="primary", key="confirm_clear_yes"):
                from sheets.food_log import get_today_log as _gtl, delete_food_entry
                today_log = _gtl(profile_id)
                for entry in today_log:
                    delete_food_entry(profile_id, str(entry.get("id")))
                st.session_state["confirm_clear"] = False
                st.toast("Today's log cleared.", icon="🗑️")
                st.rerun()
            if c_no.button("Cancel", key="confirm_clear_no"):
                st.session_state["confirm_clear"] = False
                st.rerun()
else:
    st.markdown(
        '<div class="card" style="text-align:center;padding:20px;color:var(--text-muted);font-size:.85em">'
        'Select a profile to manage data.</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Alert toggles ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Alert Preferences</div>', unsafe_allow_html=True)
st.markdown('<div style="font-size:.78em;color:var(--text-muted);margin-bottom:12px">Choose which alert types appear on the Dashboard. Saved for this browser session.</div>', unsafe_allow_html=True)

if "alerts_enabled" not in st.session_state:
    st.session_state.alerts_enabled = {"red": True, "yellow": True, "green": True}

col_a, col_b, col_c = st.columns(3)
st.session_state.alerts_enabled["red"]    = col_a.toggle("🔴 Red alerts",      value=st.session_state.alerts_enabled.get("red", True))
st.session_state.alerts_enabled["yellow"] = col_b.toggle("🟡 Yellow alerts",   value=st.session_state.alerts_enabled.get("yellow", True))
st.session_state.alerts_enabled["green"]  = col_c.toggle("🟢 Green indicators", value=st.session_state.alerts_enabled.get("green", True))

st.markdown("<br>", unsafe_allow_html=True)

# ── Free API keys setup ───────────────────────────────────────────────────────
st.markdown('<div class="section-label">Nutrition API Keys</div>', unsafe_allow_html=True)
st.markdown('<div style="font-size:.78em;color:var(--text-muted);margin-bottom:12px">MacroStream uses free APIs for nutrition lookup. Add keys below to enable smarter food search.</div>', unsafe_allow_html=True)

st.markdown("""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
  <div style="padding:14px 16px;background:var(--surface-2);border-radius:10px;border:1px solid var(--border)">
    <div style="font-size:.8em;font-weight:700;margin-bottom:6px">✨ Gemini 2.5 Flash (Recommended)</div>
    <div style="font-size:.75em;color:var(--text-muted);margin-bottom:8px">15 req/min · 1,500 req/day · No credit card needed</div>
    <div style="font-size:.75em;color:var(--text-muted)">Get a free key at <b>aistudio.google.com</b> → Get API Key</div>
    <div style="font-size:.72em;color:var(--text-muted);margin-top:8px;font-family:monospace;background:var(--surface-3);padding:6px 8px;border-radius:6px">GEMINI_API_KEY = "your_key"</div>
  </div>
  <div style="padding:14px 16px;background:var(--surface-2);border-radius:10px;border:1px solid var(--border)">
    <div style="font-size:.8em;font-weight:700;margin-bottom:6px">⚡ Groq (Fallback LLM)</div>
    <div style="font-size:.75em;color:var(--text-muted);margin-bottom:8px">Fast llama-3.1-8b-instant · Generous free tier</div>
    <div style="font-size:.75em;color:var(--text-muted)">Get a free key at <b>console.groq.com</b> → Sign up free</div>
    <div style="font-size:.72em;color:var(--text-muted);margin-top:8px;font-family:monospace;background:var(--surface-3);padding:6px 8px;border-radius:6px">GROQ_API_KEY = "your_key"</div>
  </div>
</div>
<div style="padding:12px 14px;background:var(--surface-2);border-radius:10px;border:1px solid var(--border);margin-bottom:4px">
  <div style="font-size:.78em;font-weight:600;margin-bottom:4px">🔍 DuckDuckGo (always enabled)</div>
  <div style="font-size:.75em;color:var(--text-muted)">No API key required. Used as a fallback when LLM keys are not set.</div>
</div>
""", unsafe_allow_html=True)

with st.expander("How to add keys to .streamlit/secrets.toml"):
    st.code("""
# .streamlit/secrets.toml

GEMINI_API_KEY = "AIzaSy..."
GROQ_API_KEY = "gsk_..."

GOOGLE_SHEET_ID = "your_spreadsheet_id"
[gcp_service_account]
type = "service_account"
# ... rest of service account fields
""", language="toml")
