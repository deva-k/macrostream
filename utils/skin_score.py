"""Daily skin score algorithm (0–10).

Scoring model: Start at 10.0 — deduct for dietary insults, add bonuses
for evidence-backed skin-supportive foods.

Scientific basis:
- High-GI diet → insulin + IGF-1 spike → sebum + comedogenesis (RCT evidence, strong)
- Omega-3 (EPA/DHA) → competes with omega-6 for COX-2 → reduces IL-1β, TNF-α (strong)
- Zinc → inhibits 5-alpha-reductase (DHT/sebum) + antimicrobial vs P. acnes (strong)
- Vitamin A (beta-carotene) → keratinocyte differentiation, follicular keratosis reduction (strong)
- Vitamin C → essential cofactor for collagen biosynthesis (strong)
- Polyphenols (EGCG, anthocyanins) → inhibit NF-κB, reduce CRP, anti-sebum (moderate)
- Cruciferous veg (sulforaphane) → Nrf2 pathway activation, detox support (moderate)
- Saturated fat → activates mTORC1 (same pathway as IGF-1) → sebum (moderate)
- Whey protein → insulinotropic + IGF-1 elevation → acne (moderate, dose-dependent)
- Fibre → gut microbiome → systemic inflammation reduction (strong)
"""

from nutrition.alerts import get_food_alerts, get_daily_alerts


# ── Food term lists ────────────────────────────────────────────────────────────
_OMEGA3_TERMS   = ["salmon", "mackerel", "sardine", "herring", "walnut",
                   "flaxseed", "flax seed", "flax", "chia", "hemp seed"]

_ZINC_TERMS     = ["pumpkin seed", "oyster", "hemp seed", "chickpea",
                   "lentil", "egg", "edamame", "beef"]

_VIT_A_TERMS    = ["carrot", "sweet potato", "kale", "spinach",
                   "red pepper", "bell pepper", "broccoli"]

_VIT_C_TERMS    = ["bell pepper", "red pepper", "broccoli", "kale",
                   "strawberr", "blueberr", "tomato", "spinach", "cauliflower"]

_POLYPHENOL_TERMS = ["blueberr", "strawberr", "green tea", "dark chocolate",
                     "turmeric", "ginger", "raspberry", "blackberr"]

_CRUCIFEROUS_TERMS = ["broccoli", "cauliflower", "kale", "brussels", "cabbage",
                      "bok choy", "rocket", "watercress"]


def _any_match(food_log: list, terms: list[str]) -> bool:
    return any(
        any(t in str(e.get("food_name", "")).lower() for t in terms)
        for e in food_log
    )


def calculate_skin_score(food_log: list, targets: dict) -> float:
    day_type = targets.get("day_type", "training")
    score = 10.0

    # ── Deductions: RED alert foods ─────────────────────────────────────────
    # Each unique RED food message costs -2.0 (capped at 3 triggers = -6.0)
    seen_red: set[str] = set()
    for entry in food_log:
        for alert in get_food_alerts(entry.get("food_name", "")):
            if alert["level"] == "red" and alert["message"] not in seen_red:
                score -= 2.0
                seen_red.add(alert["message"])

    # ── Deductions: YELLOW daily alerts ─────────────────────────────────────
    # -0.5 per unique yellow alert (reduced from -1.0 to avoid excessive piling)
    yellow_alerts = get_daily_alerts(food_log, targets, day_type)
    score -= len(yellow_alerts) * 0.5

    # ── Deductions: Whey protein (dose-dependent) ────────────────────────────
    # Whey elevates IGF-1 more than any other protein source (dose-dependent RCT)
    # 1 scoop (≈30g) = threshold; >2 scoops = elevated risk
    whey_g = sum(
        float(e.get("quantity_g", 0))
        for e in food_log
        if "whey" in str(e.get("food_name", "")).lower()
    )
    if whey_g > 60:
        score -= 1.5   # >2 scoops: definite IGF-1 elevation
    elif whey_g > 30:
        score -= 0.75  # 1-2 scoops: moderate risk
    elif whey_g > 0:
        score -= 0.25  # any whey in acne-prone individuals: mild caution

    # ── Deductions: Saturated fat (graduated) ───────────────────────────────
    # mTORC1 activation is dose-dependent; strong effect above 20 g/day
    total_sat_fat = sum(float(e.get("sat_fat", 0) or 0) for e in food_log)
    if total_sat_fat > 20:
        score -= 1.5
    elif total_sat_fat > 15:
        score -= 0.75

    # ── Deductions: Glycaemic index (graduated, carb-weighted) ──────────────
    # Low GI ≤55: safe. Medium 56–69: moderate insulin response. High ≥70: established risk.
    # University of Sydney GI classification (current 2024)
    carb_entries = [
        e for e in food_log
        if float(e.get("carbs", 0) or 0) > 5 and e.get("gi")
    ]
    total_carb_g = sum(float(e.get("carbs", 0)) for e in carb_entries)
    if carb_entries and total_carb_g > 0:
        avg_gi = sum(
            float(e["gi"]) * float(e.get("carbs", 0)) for e in carb_entries
        ) / total_carb_g
        if avg_gi >= 70:
            score -= 1.5   # high GI: established acne trigger via IGF-1
        elif avg_gi > 55:
            score -= 0.75  # medium GI: moderate caution

    # ── Deductions: Rest-day calorie excess ─────────────────────────────────
    if day_type == "rest":
        total_cal = sum(float(e.get("calories", 0) or 0) for e in food_log)
        if total_cal > 2400:
            score -= 1.0
        elif total_cal > 2100:
            score -= 0.5

    # ── Bonuses: Omega-3 rich foods ─────────────────────────────────────────
    # EPA competes with omega-6 at COX-2 → reduces leukotriene B4 + PGE2 (strong evidence)
    if _any_match(food_log, _OMEGA3_TERMS):
        score += 1.0

    # ── Bonuses: Zinc-rich foods ─────────────────────────────────────────────
    # Inhibits 5-alpha-reductase (sebum reduction) + antimicrobial vs P. acnes
    if _any_match(food_log, _ZINC_TERMS):
        score += 0.5

    # ── Bonuses: Vitamin A / beta-carotene sources ───────────────────────────
    # Regulates keratinocyte differentiation; reduces follicular hyperkeratosis
    if _any_match(food_log, _VIT_A_TERMS):
        score += 0.5

    # ── Bonuses: Vitamin C rich foods ────────────────────────────────────────
    # Essential cofactor for prolyl/lysyl hydroxylase in collagen biosynthesis
    if _any_match(food_log, _VIT_C_TERMS):
        score += 0.5

    # ── Bonuses: Polyphenol / anti-inflammatory foods ─────────────────────────
    # EGCG (green tea) inhibits NF-κB; anthocyanins (berries) reduce CRP and IL-6
    if _any_match(food_log, _POLYPHENOL_TERMS):
        score += 0.5

    # ── Bonuses: Cruciferous vegetables ─────────────────────────────────────
    # Sulforaphane activates Nrf2 pathway → antioxidant enzyme induction + detox support
    if _any_match(food_log, _CRUCIFEROUS_TERMS):
        score += 0.5

    # ── Bonuses: Fibre (graduated) ────────────────────────────────────────────
    # Gut microbiome → systemic inflammation → skin inflammation cascade
    total_fibre = sum(float(e.get("fibre", 0) or 0) for e in food_log)
    if total_fibre >= 30:
        score += 1.0   # optimal gut health territory
    elif total_fibre >= 25:
        score += 0.5   # EFSA minimum met

    # ── Bonuses: Consistently low-GI carb choices ─────────────────────────────
    if carb_entries and all(float(e.get("gi", 100)) <= 55 for e in carb_entries):
        score += 0.5

    # ── Bonuses: Protein target met (collagen synthesis) ─────────────────────
    total_protein = sum(float(e.get("protein", 0) or 0) for e in food_log)
    if total_protein >= targets.get("protein", 160) * 0.9:
        score += 0.5

    return round(max(0.0, min(10.0, score)), 1)


def score_color(score: float) -> str:
    if score >= 8.5:
        return "#4CAF50"   # green — Excellent
    elif score >= 7.0:
        return "#34D399"   # teal — Good
    elif score >= 5.0:
        return "#F59E0B"   # amber — Fair
    return "#EF4444"       # red — Needs work


def score_label(score: float) -> str:
    if score >= 8.5:
        return "Excellent"
    elif score >= 7.0:
        return "Good"
    elif score >= 5.0:
        return "Fair"
    return "Needs work"
