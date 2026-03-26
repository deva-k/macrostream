"""Global CSS design system — injected on every page via inject_css()."""

import streamlit as st


_CSS = """
<style>
/* ── Design tokens ─────────────────────────────────────────────────────────── */
:root {
  --bg:         #08080F;
  --surface:    #111119;
  --surface-2:  #17172A;
  --surface-3:  #1F1F35;
  --surface-4:  #272742;
  --border:     rgba(255,255,255,0.07);
  --border-md:  rgba(255,255,255,0.12);
  --border-hi:  rgba(255,255,255,0.20);
  --primary:    #4CAF50;
  --primary-lo: rgba(76,175,80,0.12);
  --primary-md: rgba(76,175,80,0.30);
  --amber:      #F59E0B;
  --amber-lo:   rgba(245,158,11,0.12);
  --red:        #EF4444;
  --red-lo:     rgba(239,68,68,0.12);
  --blue:       #60A5FA;
  --purple:     #A78BFA;
  --teal:       #34D399;
  --text:       #F0F0F8;
  --text-dim:   #9CA3AF;
  --text-muted: #6B7280;
  --radius:     14px;
  --radius-sm:  8px;
  --radius-xs:  6px;
  --shadow:     0 4px 32px rgba(0,0,0,0.5);
  --shadow-sm:  0 2px 12px rgba(0,0,0,0.3);
  --transition: 0.18s ease;
}

/* ── App shell ──────────────────────────────────────────────────────────────── */
.stApp { background: var(--bg) !important; }
.stApp > header { background: transparent !important; }
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
#MainMenu, footer, .stDeployButton { display: none !important; }
.block-container { padding-top: 1.5rem !important; }

/* ── Hide built-in nav (we render custom nav at bottom of sidebar) ───────────── */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavSeparator"] { display: none !important; }

/* ── Custom page-link navigation ────────────────────────────────────────────── */
[data-testid="stPageLink"] {
  margin: 1px 0 !important;
}
[data-testid="stPageLink"] a {
  display: flex !important;
  align-items: center !important;
  padding: 9px 12px !important;
  border-radius: var(--radius-sm) !important;
  text-decoration: none !important;
  transition: background var(--transition), color var(--transition) !important;
  font-size: 0.85em !important;
  font-weight: 500 !important;
  color: var(--text-dim) !important;
  letter-spacing: 0.01em !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="stPageLink"] a:hover {
  background: var(--surface-4) !important;
  color: var(--text) !important;
}
[data-testid="stPageLink"] a[aria-current="page"] {
  background: var(--primary-lo) !important;
  color: var(--primary) !important;
  font-weight: 700 !important;
  border-left: 3px solid var(--primary) !important;
  padding-left: 9px !important;
}
[data-testid="stPageLink"] p {
  font-size: inherit !important;
  font-weight: inherit !important;
  color: inherit !important;
  margin: 0 !important;
}

/* ── Cards ──────────────────────────────────────────────────────────────────── */
.card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 22px;
  margin-bottom: 10px;
  transition: border-color var(--transition), transform var(--transition);
}
.card:hover { border-color: var(--border-md); }
.card-sm {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
}
.card-accent {
  background: linear-gradient(135deg, var(--surface-2) 0%, #1b1b32 100%);
  border: 1px solid var(--border-md);
  border-radius: var(--radius);
  padding: 20px 22px;
}

/* ── Circular progress rings ────────────────────────────────────────────────── */
.ring-card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 12px 14px;
  text-align: center;
  transition: border-color var(--transition), transform var(--transition), box-shadow var(--transition);
  cursor: default;
}
.ring-card:hover {
  border-color: var(--border-md);
  transform: translateY(-3px);
  box-shadow: var(--shadow-sm);
}
.ring-label {
  font-size: .68em;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: var(--text-muted);
  margin-bottom: 10px;
}
.ring-svg { transform: rotate(-90deg); display: block; margin: 0 auto; overflow: visible; }
.ring-bg   { fill: none; stroke: var(--surface-4); stroke-width: 4; }
.ring-fill { fill: none; stroke-width: 4; stroke-linecap: round; transition: stroke-dasharray 0.6s cubic-bezier(.4,0,.2,1); }
.ring-center {
  font-size: .68em;
  font-weight: 700;
  fill: var(--text);
  dominant-baseline: middle;
  text-anchor: middle;
  transform: rotate(90deg);
  transform-origin: 18px 18px;
}
.ring-value { font-size: 1.05em; font-weight: 700; color: var(--text); margin-top: 8px; line-height: 1.1; }
.ring-sub   { font-size: .7em; color: var(--text-muted); margin-top: 3px; }

/* ── Progress bars ──────────────────────────────────────────────────────────── */
.prog-row { margin: 5px 0; }
.prog-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 5px; }
.prog-title { font-size: .8em; font-weight: 600; color: var(--text); }
.prog-nums  { font-size: .75em; color: var(--text-muted); }
.prog-track { background: var(--surface-4); border-radius: 100px; height: 5px; overflow: hidden; }
.prog-fill  { height: 100%; border-radius: 100px; transition: width 0.5s cubic-bezier(.4,0,.2,1); }
.prog-sub   { font-size: .68em; color: var(--text-muted); margin-top: 3px; }

/* ── Stat chips ─────────────────────────────────────────────────────────────── */
.chip-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 12px 0; }
.chip {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  text-align: center;
}
.chip-label { font-size: .65em; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--text-muted); margin-bottom: 5px; }
.chip-value { font-size: 1.1em; font-weight: 700; color: var(--text); }
.chip-sub   { font-size: .68em; color: var(--text-muted); margin-top: 2px; }

/* ── Skin score ─────────────────────────────────────────────────────────────── */
.skin-card {
  background: linear-gradient(160deg, var(--surface-2) 0%, #1a1535 100%);
  border: 1px solid var(--border-md);
  border-radius: var(--radius);
  padding: 28px 16px;
  text-align: center;
  height: 100%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.skin-score { font-size: 3.8em; font-weight: 800; line-height: 1; letter-spacing: -.03em; }
.skin-label { font-size: .9em; font-weight: 600; margin-top: 6px; }
.skin-sub   { font-size: .72em; color: var(--text-muted); margin-top: 5px; }

/* ── Alert pills ────────────────────────────────────────────────────────────── */
.alert-pill {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  margin: 5px 0;
  font-size: .875em;
  line-height: 1.45;
}
.alert-red    { background: var(--red-lo);   border-left: 3px solid var(--red);   }
.alert-yellow { background: var(--amber-lo); border-left: 3px solid var(--amber); }
.alert-green  { background: var(--primary-lo); border-left: 3px solid var(--primary); }

/* ── Macro badges ───────────────────────────────────────────────────────────── */
.badges { display: flex; gap: 6px; flex-wrap: wrap; margin: 10px 0 4px; }
.badge {
  border-radius: 100px;
  padding: 3px 10px;
  font-size: .72em;
  font-weight: 700;
  white-space: nowrap;
}
.badge-kcal { background: rgba(76,175,80,.12);  border: 1px solid rgba(76,175,80,.3);  color: #6FCF6F; }
.badge-prot { background: rgba(96,165,250,.12); border: 1px solid rgba(96,165,250,.3); color: #93C5FD; }
.badge-carb { background: rgba(251,191,36,.12); border: 1px solid rgba(251,191,36,.3); color: #FCD34D; }
.badge-fat  { background: rgba(167,139,250,.12);border: 1px solid rgba(167,139,250,.3);color: #C4B5FD; }
.badge-fib  { background: rgba(52,211,153,.12); border: 1px solid rgba(52,211,153,.3); color: #6EE7B7; }
.badge-src  { background: var(--surface-4);     border: 1px solid var(--border);       color: var(--text-muted); }

/* ── Food log ───────────────────────────────────────────────────────────────── */
.meal-section { margin-top: 18px; }
.meal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 4px 8px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
}
.meal-name { font-size: .72em; font-weight: 800; text-transform: uppercase; letter-spacing: .1em; color: var(--text-muted); }
.meal-kcal { font-size: .72em; color: var(--text-muted); }
.food-item {
  display: grid;
  grid-template-columns: 1fr 60px 44px 44px 44px;
  align-items: center;
  gap: 4px;
  padding: 7px 4px;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  font-size: .83em;
}
.food-item:last-child { border-bottom: none; }
.fi-name  { font-weight: 500; color: var(--text); }
.fi-kcal  { text-align: right; font-weight: 600; color: var(--text); }
.fi-macro { text-align: right; color: var(--text-muted); font-size: .92em; }

/* ── Template cards ─────────────────────────────────────────────────────────── */
.tpl-card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 18px;
  margin-bottom: 8px;
  transition: border-color var(--transition);
}
.tpl-card.followed {
  border-color: var(--primary-md);
  background: linear-gradient(135deg, var(--surface-2), rgba(76,175,80,.05));
}
.tpl-card:hover { border-color: var(--border-md); }
.tpl-name   { font-weight: 700; font-size: 1em; color: var(--text); }
.tpl-badge  {
  display: inline-block;
  background: var(--surface-4);
  border: 1px solid var(--border);
  border-radius: 100px;
  padding: 2px 8px;
  font-size: .68em;
  font-weight: 600;
  color: var(--text-muted);
  margin-left: 8px;
  vertical-align: middle;
}
.tpl-followed { font-size: .75em; color: var(--primary); margin-left: 8px; }
.tpl-item {
  font-size: .8em;
  color: var(--text-dim);
  padding: 2px 0;
}

/* ── Section labels ─────────────────────────────────────────────────────────── */
.section-label {
  font-size: .68em;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--text-muted);
  margin: 20px 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}

/* ── Sidebar brand ──────────────────────────────────────────────────────────── */
.brand-name {
  font-size: 1.35em;
  font-weight: 800;
  background: linear-gradient(90deg, #4CAF50 0%, #2196F3 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -.02em;
}
.brand-tag { font-size: .72em; color: var(--text-muted); margin-top: 1px; }

/* ── Target chips in sidebar ────────────────────────────────────────────────── */
.target-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin: 8px 0 4px; }
.target-chip {
  background: var(--surface-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
  padding: 7px 10px;
  text-align: center;
}
.target-chip .tv { font-size: .95em; font-weight: 700; color: var(--text); }
.target-chip .tl { font-size: .6em; text-transform: uppercase; letter-spacing: .06em; color: var(--text-muted); margin-top: 1px; }

/* ── Day toggle ─────────────────────────────────────────────────────────────── */
.day-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 100px;
  font-size: .8em;
  font-weight: 700;
}
.day-training { background: rgba(76,175,80,.15); color: var(--primary); border: 1px solid rgba(76,175,80,.3); }
.day-rest     { background: rgba(96,165,250,.12); color: var(--blue);    border: 1px solid rgba(96,165,250,.25); }

/* ── Streamlit tweaks ───────────────────────────────────────────────────────── */
div[data-testid="stMetric"] {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  padding: 14px 16px !important;
}
.stButton > button {
  border-radius: var(--radius-xs) !important;
  font-weight: 600 !important;
  transition: all var(--transition) !important;
}
div[data-testid="stExpander"] {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}
</style>
"""


def inject_css() -> None:
    """Inject the global design system CSS. Call once at the top of each page."""
    st.markdown(_CSS, unsafe_allow_html=True)
