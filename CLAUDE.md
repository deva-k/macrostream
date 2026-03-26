# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Streamlit app to track daily calories, macronutrients, and food quality. Supports multiple user profiles with personalised macro targets. Food logs persist to Google Sheets. Full specification is in `claude.md`.

## Running the App

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Dev Commands

```bash
pip install -r requirements.txt
streamlit run app.py --server.runOnSave true
pytest        # run tests (once added)
ruff check .  # lint
```

## Architecture

### Entry Point
- `app.py` — Streamlit entry point; loads active profile from session state; sets up page navigation

### Pages (`pages/`)
- `dashboard.py` — Day type toggle, macro progress rings, skin score, alert feed
- `log_food.py` — Food search + editable confirmation card + quick-add favourites
- `progress.py` — 30-day charts (calories, protein, skin score)
- `meal_planner.py` — Reference meal plan (read-only)
- `settings.py` — Profile manager: create/switch/edit profiles; export data

### Core Modules
- `sheets/client.py` — Google Sheets auth (Service Account via `gspread`) and sheet access helpers
- `sheets/food_log.py` — Read/write food log rows; one sheet tab per profile
- `sheets/profiles.py` — Read/write user profiles from a `Profiles` sheet tab
- `nutrition/search.py` — Serper/SerpAPI web search → HTML parse → extract macros
- `nutrition/fallback.py` — Hardcoded USDA table for ~100 common foods; Nutritionix API fallback
- `nutrition/alerts.py` — Red/yellow/green alert rules engine
- `utils/macros.py` — Mifflin-St Jeor TDEE → training/rest day macro targets per profile
- `utils/skin_score.py` — Daily skin score 0–10

### Google Sheets Structure
One spreadsheet per deployment. Tabs:
- `Profiles` — one row per profile (id, name, gender, weight_kg, height_cm, age, training_days, goal, restrictions)
- `FoodLog_{profile_id}` — one tab per profile; columns: date, meal, food_name, quantity, calories, protein, carbs, fat, fibre, sat_fat, omega6, gi, day_type
- `FoodCache` — shared lookup cache (food_name → macros) to avoid repeat API calls

### Data Flow
1. Profile selected → `utils/macros.py` computes targets using Mifflin-St Jeor
2. User enters food → `nutrition/search.py` checks `FoodCache` sheet first; if miss, hits Serper
3. Parsed macros shown in editable card → confirmed → appended to `FoodLog_{profile_id}` via `gspread`
4. Dashboard aggregates today's rows → `nutrition/alerts.py` fires rules → `utils/skin_score.py` scores
5. `st.session_state` buffers unsaved entries within a session; writes flush to Sheets on confirm

### State Management
- `st.session_state["active_profile"]` — currently selected profile dict
- `st.session_state["today_log"]` — in-session buffer before Sheets write
- All confirmed logs written immediately to Google Sheets (no local DB)

## Multi-Profile Support
- Profiles tab in Settings: create new, switch active, edit fields
- Switching profile recomputes macro targets automatically
- Each profile has its own food log tab in the spreadsheet
- Macro targets derived from profile fields via Mifflin-St Jeor; user can override manually

## Key Business Rules

- **Day type toggle** — Training vs rest day changes carb/calorie targets; user toggles on dashboard
- **Macro targets** (computed per profile): Protein = 2g × weight_kg (fixed). Carbs are the lever.
- **Saturated fat hard cap**: 20g/day. Omega-6 soft cap: 12g/day.
- **Sona Masoori rice** — NOT a red alert; amber only if eaten at lunch
- **Whey protein** — NOT a red alert; amber only if >1 scoop/day
- **Peanuts/peanut butter** — always RED (confirmed skin trigger)
- **GI tracking** — weighted average GI by carb grams; shown on dashboard
- **Breakfast template** — "My overnight oats" one-click add per profile

## Environment / API Keys

Store in `.env` (loaded via `python-dotenv`):
```
GOOGLE_SERVICE_ACCOUNT_JSON=path/to/service_account.json
GOOGLE_SHEET_ID=
SERPER_API_KEY=
NUTRITIONIX_APP_ID=
NUTRITIONIX_APP_KEY=
```

Nutrition lookup priority: FoodCache sheet → Serper web search → Nutritionix API → hardcoded USDA table.

## Python Packages
```
streamlit
gspread
google-auth
requests
beautifulsoup4
plotly
python-dotenv
ruff  # dev
pytest  # dev
```
