"""Macro target calculations.

Formulas used:
- BMR: Mifflin-St Jeor equation (most validated for general population)
- TDEE: Day-specific activity multipliers, not a single weekly average.
  Training days use a higher multiplier (reflects workout energy expenditure).
  Rest days use 1.2 (sedentary NEAT only — no workout calorie burn).
- Deficit: Mild -250 kcal on training days; -350 kcal on rest days.
  This pattern preserves muscle (fuelling workouts) while creating a net
  weekly deficit of ~250-300 kcal/day for lean body recomposition.
- Protein: 2.0 g/kg — within the ISSN-recommended 1.6–2.2 g/kg range for
  muscle preservation during a calorie deficit.
- Fat: 0.84 g/kg → ≈25–30% of calories (cardiovascular and hormonal minimum).
- Carbs: Residual after protein + fat kcal are subtracted from target calories.
- Fibre: 28 g training / 25 g rest (aligned with EFSA ≥25 g and US DGA 28-34 g).
- Sat-fat cap: 20 g/day (≈9% of 2,000 kcal — between AHA <6% and WHO <10%).
- Omega-6 cap: 12 g/day (targets ≈4:1 omega-6:omega-3 ratio at ~2 g omega-3 intake).
"""


def mifflin_st_jeor(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
    """Return BMR (kcal/day) using the Mifflin-St Jeor equation."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if gender.lower() == "male" else base - 161


def _training_day_factor(training_days_per_week: int) -> float:
    """Activity multiplier applied to BMR on actual training days.

    Higher than a weekly average because it must account for the workout
    energy expenditure on that specific day (~300–600 kcal above baseline).
    """
    if training_days_per_week <= 2:
        return 1.40   # light training: ~200–300 kcal workout burn
    elif training_days_per_week <= 4:
        return 1.55   # moderate training: ~400–500 kcal workout burn
    return 1.65       # high-frequency training: ~500–700 kcal workout burn


_REST_DAY_FACTOR = 1.2  # sedentary NEAT only — no workout calories


def calculate_tdee(gender: str, weight_kg: float, height_cm: float,
                   age: int, training_days: int = 3) -> float:
    """Return the estimated weekly-average TDEE (kcal/day).

    Computed as a weighted average of training-day and rest-day TDEEs,
    which is more accurate than applying a single weekly multiplier to both
    day types when carb/calorie cycling is in use.
    """
    bmr = mifflin_st_jeor(gender, weight_kg, height_cm, age)
    rest_days = max(7 - training_days, 1)
    training_day_tdee = bmr * _training_day_factor(training_days)
    rest_day_tdee = bmr * _REST_DAY_FACTOR
    weekly_avg = (training_day_tdee * training_days + rest_day_tdee * rest_days) / 7
    return round(weekly_avg)


def get_macro_targets(profile: dict, day_type: str = "training") -> dict:
    """Compute daily macro targets from profile fields.

    Protein = 2 g/kg (fixed — ISSN upper-optimal for recomposition).
    Fat     = 0.84 g/kg (fixed — hormonal floor + cardiovascular minimum).
    Carbs   = lever: fills remaining calories after protein + fat are accounted for.
    Fibre   = 28 g training / 25 g rest (EFSA + US DGA aligned).
    """
    weight        = float(profile.get("weight_kg")     or 80)
    gender        = str(profile.get("gender")           or "male")
    height        = float(profile.get("height_cm")      or 175)
    age           = int(profile.get("age")               or 30)
    training_days = int(profile.get("training_days")     or 3)

    bmr = mifflin_st_jeor(gender, weight, height, age)

    # ── Day-specific TDEE and deficit ────────────────────────────────────────
    if day_type == "training":
        day_tdee = bmr * _training_day_factor(training_days)
        calories = round(day_tdee - 250)   # mild deficit; need fuel for workout
        fibre    = 28
    else:
        day_tdee = bmr * _REST_DAY_FACTOR
        calories = round(day_tdee - 350)   # moderate deficit from lower base
        fibre    = 25

    # ── Macronutrient allocation ─────────────────────────────────────────────
    protein_g = round(2.0 * weight)          # 2 g/kg
    fat_g     = round(0.84 * weight)         # ~25–30% of calories
    remaining = calories - (protein_g * 4) - (fat_g * 9)
    carbs_g   = max(80, round(remaining / 4))  # floor at 80 g (brain + muscle minimum)

    # ── Weekly-average TDEE (for surplus/deficit chart on Progress page) ─────
    weekly_tdee = calculate_tdee(gender, weight, height, age, training_days)

    return {
        "calories":    calories,
        "protein":     protein_g,
        "carbs":       carbs_g,
        "fat":         fat_g,
        "fibre":       fibre,
        "sat_fat_cap": 20,    # g/day — hard cap (≈9% of 2,000 kcal)
        "omega6_cap":  12,    # g/day — soft cap (targets ≈4:1 omega-6:omega-3)
        "tdee":        weekly_tdee,
        "day_type":    day_type,
    }


def get_weighted_gi(food_log: list) -> float | None:
    """Return calorie-weighted average GI for the day.

    Only entries with >5 g carbs and a known GI value are included.
    Weighting by carb grams gives a more accurate picture of the total
    glycaemic load than a simple average.
    """
    carb_entries = [
        e for e in food_log
        if float(e.get("carbs", 0) or 0) > 5 and e.get("gi")
    ]
    total_carbs = sum(float(e.get("carbs", 0)) for e in carb_entries)
    if not carb_entries or total_carbs == 0:
        return None
    return sum(
        float(e["gi"]) * float(e.get("carbs", 0)) for e in carb_entries
    ) / total_carbs
