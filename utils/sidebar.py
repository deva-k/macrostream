"""Common sidebar rendered on every page."""

import streamlit as st
from utils.macros import get_macro_targets


def render_sidebar() -> tuple[dict | None, str]:
    """Render profile selector, day-type toggle and targets. Returns (active_profile, day_type)."""
    with st.sidebar:
        # Brand
        st.markdown(
            '<div class="brand-name">MacroStream</div>'
            '<div class="brand-tag">Macro &amp; Skin Health Tracker</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        from sheets.profiles import get_all_profiles
        from sheets.client import is_configured

        if not is_configured():
            st.error("Google Sheets not configured")
            st.page_link("pages/4_Settings.py", label="Go to Settings →")
            return None, "training"

        profiles = get_all_profiles()
        if not profiles:
            st.warning("No profiles yet.")
            st.page_link("pages/4_Settings.py", label="Create a profile →")
            return None, "training"

        # Profile selector
        profile_names = [p["name"] for p in profiles]
        if "active_profile_id" not in st.session_state:
            st.session_state.active_profile_id = profiles[0]["id"]

        current_ids = [p["id"] for p in profiles]
        current_idx = (
            current_ids.index(st.session_state.active_profile_id)
            if st.session_state.active_profile_id in current_ids else 0
        )

        st.markdown('<div style="font-size:.68em;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-muted);margin-bottom:4px">Profile</div>', unsafe_allow_html=True)
        selected_name = st.selectbox("Profile", profile_names, index=current_idx, label_visibility="collapsed")
        active_profile = next(p for p in profiles if p["name"] == selected_name)
        st.session_state.active_profile_id = active_profile["id"]
        st.session_state.active_profile = active_profile

        st.markdown("<br>", unsafe_allow_html=True)

        # Day type toggle
        if "day_type" not in st.session_state:
            st.session_state.day_type = "training"

        st.markdown('<div style="font-size:.68em;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-muted);margin-bottom:4px">Today is a…</div>', unsafe_allow_html=True)
        day_label = st.radio(
            "Today",
            ["🏋️ Training", "🛋️ Rest"],
            index=0 if st.session_state.day_type == "training" else 1,
            horizontal=True,
            label_visibility="collapsed",
        )
        st.session_state.day_type = "training" if "Training" in day_label else "rest"
        day_type = st.session_state.day_type

        # Macro targets grid
        targets = get_macro_targets(active_profile, day_type)
        st.markdown(f"""
        <div style="margin-top:10px">
          <div class="target-grid">
            <div class="target-chip">
              <div class="tv">{targets['calories']}</div>
              <div class="tl">kcal</div>
            </div>
            <div class="target-chip">
              <div class="tv">{targets['protein']}g</div>
              <div class="tl">protein</div>
            </div>
            <div class="target-chip">
              <div class="tv">{targets['carbs']}g</div>
              <div class="tl">carbs</div>
            </div>
            <div class="target-chip">
              <div class="tv">{targets['fat']}g</div>
              <div class="tl">fat</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation (placed last for correct UX order)
        st.markdown(
            '<div style="font-size:.68em;font-weight:700;text-transform:uppercase;'
            'letter-spacing:.08em;color:var(--text-muted);margin:20px 0 6px">Navigate</div>',
            unsafe_allow_html=True,
        )
        st.page_link("app.py",                 label="📊  Dashboard")
        st.page_link("pages/1_Log_Food.py",     label="🍽️  Log Food")
        st.page_link("pages/2_Progress.py",     label="📈  Progress")
        st.page_link("pages/3_Meal_Planner.py", label="📋  Meal Planner")
        st.page_link("pages/4_Settings.py",     label="⚙️  Settings")

        return active_profile, day_type
