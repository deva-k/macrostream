"""Progress — charts and weekly summaries."""

import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="Progress · MacroStream", page_icon="📈", layout="wide")

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from utils.styles import inject_css
from utils.sidebar import render_sidebar
from utils.macros import get_macro_targets, calculate_tdee
from utils.skin_score import calculate_skin_score, score_color
from sheets.food_log import get_log_range

inject_css()
active_profile, day_type = render_sidebar()

st.markdown(
    '<h1 style="margin:0 0 4px;font-size:1.6em;font-weight:800;letter-spacing:-.02em">Progress</h1>'
    '<p style="color:var(--text-muted);font-size:.82em;margin-bottom:20px">Trends, averages and weekly breakdown</p>',
    unsafe_allow_html=True,
)

if active_profile is None:
    st.stop()

profile_id = active_profile["id"]

# ── Period selector ───────────────────────────────────────────────────────────
col_period, _ = st.columns([2, 5])
with col_period:
    days_back = st.selectbox(
        "Period", [7, 14, 30, 60, 90], index=2,
        format_func=lambda x: f"Last {x} days",
        label_visibility="collapsed",
    )

end_date   = date.today()
start_date = end_date - timedelta(days=days_back - 1)
records    = get_log_range(profile_id, start_date.isoformat(), end_date.isoformat())

if not records:
    st.markdown(
        '<div class="card" style="text-align:center;padding:40px;color:var(--text-muted)">'
        f'No data for the last {days_back} days. Start logging food on the Dashboard.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Build daily aggregates ────────────────────────────────────────────────────
targets_training = get_macro_targets(active_profile, "training")
targets_rest     = get_macro_targets(active_profile, "rest")

daily: dict[str, dict] = {}
for entry in records:
    d = str(entry.get("date", ""))
    if not d:
        continue
    if d not in daily:
        daily[d] = {
            "date": d, "calories": 0, "protein": 0, "carbs": 0,
            "fat": 0, "fibre": 0, "sat_fat": 0, "omega6": 0,
            "day_type": entry.get("day_type", "training"), "entries": [],
        }
    for m in ["calories", "protein", "carbs", "fat", "fibre", "sat_fat", "omega6"]:
        daily[d][m] += float(entry.get(m, 0) or 0)
    daily[d]["entries"].append(entry)

df_rows = sorted(daily.values(), key=lambda x: x["date"])
for row in df_rows:
    t = targets_training if row["day_type"] == "training" else targets_rest
    t["day_type"] = row["day_type"]
    row["skin_score"]     = calculate_skin_score(row["entries"], t)
    row["cal_target"]     = t["calories"]
    row["protein_target"] = t["protein"]
    row["carbs_target"]   = t["carbs"]

df = pd.DataFrame(df_rows)
df["date_dt"] = pd.to_datetime(df["date"])

# ── Chart theme helper ────────────────────────────────────────────────────────
_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#9CA3AF", size=11),
    margin=dict(l=0, r=0, t=8, b=0),
    height=260,
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    xaxis=dict(showgrid=False, linecolor="rgba(255,255,255,0.06)", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.06)", tickfont=dict(size=10)),
)


def _fig(**kwargs):
    fig = go.Figure()
    layout = {**_LAYOUT, **kwargs}
    fig.update_layout(**layout)
    return fig


# ── Summary metrics ───────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Summary</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="chip-grid" style="grid-template-columns:repeat(5,1fr)">
  <div class="chip">
    <div class="chip-label">Avg Calories</div>
    <div class="chip-value">{df['calories'].mean():.0f}</div>
    <div class="chip-sub">kcal / day</div>
  </div>
  <div class="chip">
    <div class="chip-label">Avg Protein</div>
    <div class="chip-value" style="color:#93C5FD">{df['protein'].mean():.1f}g</div>
    <div class="chip-sub">per day</div>
  </div>
  <div class="chip">
    <div class="chip-label">Avg Carbs</div>
    <div class="chip-value" style="color:#FCD34D">{df['carbs'].mean():.1f}g</div>
    <div class="chip-sub">per day</div>
  </div>
  <div class="chip">
    <div class="chip-label">Avg Fat</div>
    <div class="chip-value" style="color:#C4B5FD">{df['fat'].mean():.1f}g</div>
    <div class="chip-sub">per day</div>
  </div>
  <div class="chip">
    <div class="chip-label">Avg Skin Score</div>
    <div class="chip-value" style="color:#A78BFA">{df['skin_score'].mean():.1f}</div>
    <div class="chip-sub">out of 10</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts row 1 ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Daily Breakdown</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2, gap="medium")

with c1:
    fig = _fig()
    fig.add_trace(go.Bar(x=df["date_dt"], y=df["calories"], name="Calories",
                         marker_color="#4CAF50", opacity=0.75, marker_line_width=0))
    fig.add_trace(go.Scatter(x=df["date_dt"], y=df["cal_target"], mode="lines", name="Target",
                             line=dict(color="#F59E0B", dash="dot", width=1.5)))
    fig.update_layout(title=dict(text="Calories vs Target", font=dict(size=12, color="#F0F0F8"), x=0))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    prot_colors = ["#4CAF50" if p >= t else "#EF4444"
                   for p, t in zip(df["protein"], df["protein_target"])]
    fig2 = _fig()
    fig2.add_trace(go.Bar(x=df["date_dt"], y=df["protein"], name="Protein",
                          marker_color=prot_colors, opacity=0.85, marker_line_width=0))
    fig2.add_trace(go.Scatter(x=df["date_dt"], y=df["protein_target"], mode="lines", name="Target",
                              line=dict(color="#F59E0B", dash="dot", width=1.5)))
    fig2.update_layout(title=dict(text="Protein vs Target", font=dict(size=12, color="#F0F0F8"), x=0))
    st.plotly_chart(fig2, use_container_width=True)

c3, c4 = st.columns(2, gap="medium")

with c3:
    skin_colors = [score_color(s) for s in df["skin_score"]]
    fig3 = _fig(yaxis=dict(range=[0, 10], **_LAYOUT["yaxis"]))
    fig3.add_hrect(y0=8, y1=10, fillcolor="rgba(76,175,80,.06)", line_width=0)
    fig3.add_hrect(y0=5,  y1=8,  fillcolor="rgba(245,158,11,.04)", line_width=0)
    fig3.add_trace(go.Scatter(
        x=df["date_dt"], y=df["skin_score"],
        mode="lines+markers", name="Skin Score",
        line=dict(color="#A78BFA", width=2),
        marker=dict(color=skin_colors, size=7, line=dict(width=1.5, color="var(--bg)")),
    ))
    fig3.add_hline(y=8, line_dash="dot", line_color="rgba(76,175,80,.5)",
                   annotation_text="Excellent", annotation_font_size=10,
                   annotation_font_color="#4CAF50")
    fig3.add_hline(y=5, line_dash="dot", line_color="rgba(245,158,11,.5)",
                   annotation_text="Good", annotation_font_size=10,
                   annotation_font_color="#F59E0B")
    fig3.update_layout(title=dict(text="Daily Skin Score", font=dict(size=12, color="#F0F0F8"), x=0))
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    carb_colors = ["#FCD34D" if c >= t else "#6B7280"
                   for c, t in zip(df["carbs"], df["carbs_target"])]
    fig4 = _fig()
    fig4.add_trace(go.Bar(x=df["date_dt"], y=df["carbs"], name="Carbs",
                          marker_color=carb_colors, opacity=0.85, marker_line_width=0))
    fig4.add_trace(go.Scatter(x=df["date_dt"], y=df["carbs_target"], mode="lines", name="Target",
                              line=dict(color="#F59E0B", dash="dot", width=1.5)))
    fig4.update_layout(title=dict(text="Carbs vs Target", font=dict(size=12, color="#F0F0F8"), x=0))
    st.plotly_chart(fig4, use_container_width=True)

# ── Training vs Rest ─────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Training Day vs Rest Day</div>', unsafe_allow_html=True)
if "day_type" in df.columns and df["day_type"].nunique() > 1:
    grouped = df.groupby("day_type")[["calories", "protein", "carbs", "fat"]].mean().reset_index()
    fig5 = px.bar(
        grouped.melt(id_vars="day_type", var_name="Macro", value_name="Avg"),
        x="Macro", y="Avg", color="day_type", barmode="group",
        color_discrete_map={"training": "#4CAF50", "rest": "#60A5FA"},
    )
    fig5.update_traces(marker_line_width=0, opacity=0.85)
    fig5.update_layout(**{**_LAYOUT,
        "title": dict(text="Average by Day Type", font=dict(size=12, color="#F0F0F8"), x=0)})
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.markdown(
        '<div class="card" style="text-align:center;padding:16px;color:var(--text-muted);font-size:.85em">'
        'Log both training and rest days to see comparison.</div>',
        unsafe_allow_html=True,
    )

# ── Weekly deficit / surplus ──────────────────────────────────────────────────
st.markdown('<div class="section-label">Weekly Surplus / Deficit vs TDEE</div>', unsafe_allow_html=True)
tdee = calculate_tdee(
    str(active_profile.get("gender", "male")),
    float(active_profile.get("weight_kg", 80)),
    float(active_profile.get("height_cm", 175)),
    int(active_profile.get("age", 30)),
    int(active_profile.get("training_days", 3)),
)
df["surplus"] = df["calories"] - tdee
df["week"] = df["date_dt"].dt.isocalendar().week.astype(str)
weekly = df.groupby("week")["surplus"].sum().reset_index()
weekly["color"] = weekly["surplus"].apply(lambda x: "#EF4444" if x > 0 else "#4CAF50")

fig6 = _fig(yaxis=dict(title="kcal surplus (+) / deficit (−)", **_LAYOUT["yaxis"]))
fig6.add_trace(go.Bar(x=weekly["week"], y=weekly["surplus"],
                      marker_color=weekly["color"], opacity=0.85, marker_line_width=0,
                      name="Weekly balance"))
fig6.add_hline(y=0, line_color="rgba(255,255,255,0.2)", line_width=1)
fig6.update_layout(
    title=dict(text=f"vs TDEE ≈ {tdee} kcal/day", font=dict(size=12, color="#F0F0F8"), x=0),
    xaxis_title="Week number",
)
st.plotly_chart(fig6, use_container_width=True)

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander("📋 Raw daily data"):
    display_cols = ["date", "calories", "protein", "carbs", "fat", "fibre", "sat_fat", "omega6", "skin_score", "day_type"]
    st.dataframe(
        df[[c for c in display_cols if c in df.columns]].sort_values("date", ascending=False),
        use_container_width=True,
    )
