"""Red / Yellow / Green alert rules engine.

Evidence basis for rules:
- Peanuts: high omega-6 (15.7g/100g) + aflatoxin + confirmed skin trigger in acne literature
- Red meat: saturated fat + haem iron → mTORC1 + inflammatory eicosanoids
- Processed meat: nitrites + saturated fat + ultra-processed; stronger IGF-1 elevation than whole meat
- Gluten: user-specific restriction (noted in profile)
- Fried food: acrylamide + oxidised seed oils → inflammatory AGEs
- Full-fat hard cheese: high sat-fat + IGF-1-stimulating leucine; note: skyr/cottage cheese exempted
- Sugary drinks: pure glucose → rapid insulin + IGF-1 → sebum spike
- Processed sauces: hidden HFCS + omega-6 seed oils
- Crisps/chips: acrylamide + refined carbs + omega-6 seed oils (ultra-processed)
- Alcohol: disrupts cortisol + sleep quality → elevated skin inflammation
- White rice: high GI (73) → insulin spike; sona masoori GI ≈ 55 (exempted)
- Candy/sweets: concentrated glucose + fructose → AGE formation + insulin spike
- Seed oils (refined): polyunsaturated fat oxidation → lipid peroxides → pro-inflammatory

Yellow alerts:
- Whey >1 scoop: dose-dependent IGF-1 elevation (>30g = threshold from RCT evidence)
- Dairy >200g: IGF-1 pathway; skyr/greek yogurt have lower risk but still flagged at high volume
- Sat fat >20g: AHA-aligned cap
- Omega-6 >12g: targets ≈4:1 omega-6:omega-3 ratio
- Sona Masoori at lunch: timing alert (better post-workout)
- Rest day carbs >200g / calories >2100: rest-day caps

Green indicators:
- Omega-3 sources: EPA/DHA → anti-inflammatory via COX-2 competition
- Zinc sources: sebum regulation via 5-alpha-reductase inhibition
- Protein target: muscle preservation + collagen synthesis (requires Vit C cofactor)
- Low-GI carbs: stable insulin → reduced sebum
- Fibre ≥25g: gut microbiome → systemic inflammation reduction
- Vitamin A sources: keratinocyte differentiation, skin cell turnover
- Vitamin C sources: collagen biosynthesis cofactor
- Polyphenols: NF-κB inhibition, antioxidant defence
- Anti-inflammatory spices (turmeric/ginger): curcumin + gingerols → cytokine suppression
- Training day carbs on target: muscle glycogen replenishment
"""

from __future__ import annotations


# ── RED alert patterns ─────────────────────────────────────────────────────────
# (trigger_terms, message, exclude_terms)
_RED_RULES: list[tuple[list[str], str, list[str]]] = [
    (["peanut"],
     "Peanuts / peanut butter — confirmed skin trigger, very high omega-6 (15.7g/100g)",
     []),
    (["beef", "lamb", "pork", "bacon", "steak", "red meat", "mince beef"],
     "Red meat — user avoids red meat; high sat-fat + haem iron",
     []),
    (["sausage", "hot dog", "frankfurter", "deli meat", "salami", "pepperoni",
      "chorizo", "ham slice", "lunch meat"],
     "Processed meat — nitrites + ultra-processed; stronger IGF-1 elevation than whole meat",
     []),
    (["wheat", " bread", "pasta ", "pasta,", "barley", "rye", "croissant", "bagel",
      "baguette", "naan", "tortilla", "couscous", "sourdough", "pita", "wraps"],
     "Gluten-containing food — user avoids gluten",
     ["rice bread", "gluten-free", "gf ", "corn tortilla"]),
    (["deep fried", "deep-fried", " fried "],
     "Fried food — oxidised fats + acrylamide → inflammatory AGEs",
     []),
    (["cheddar", "brie", "parmesan", "camembert", "gouda", "full-fat cheese", "hard cheese"],
     "Full-fat hard cheese — high sat-fat + IGF-1 stimulating leucine",
     ["cottage cheese"]),
    ([" cola", "energy drink", "fruit juice", "lemonade", "squash drink", "fizzy drink",
      " soda", "pop drink"],
     "Sugary drink — rapid glucose → insulin + IGF-1 spike",
     []),
    (["ketchup", "bbq sauce", "sweet chilli sauce", "teriyaki", "hoisin",
      "shop-bought dressing", "mayonnaise"],
     "Shop-bought sauce — hidden HFCS + omega-6 seed oils",
     []),
    (["crisps", "potato chips", "corn chips", "cheese puffs", "doritos",
      "pringles", "wotsits"],
     "Processed snack — acrylamide + omega-6 seed oils + refined carbs",
     []),
    (["beer", " wine", "spirits", "vodka", "whisky", "rum", "gin", "cocktail",
      "lager", "prosecco", "champagne", "cider"],
     "Alcohol — disrupts cortisol + skin barrier + sleep / recovery quality",
     []),
    (["white rice"],
     "White rice — GI 73, significant insulin + IGF-1 spike",
     ["sona masoori", "brown rice", "basmati"]),
    (["milk chocolate", "chocolate bar", "candy", "sweets", "gummy", "jelly bean",
      "marshmallow", "fudge", "toffee", "caramel", "pick n mix"],
     "Candy / milk chocolate — concentrated glucose + fructose → AGE formation + insulin spike",
     ["dark chocolate"]),
    (["sunflower oil", "vegetable oil", "corn oil", "soybean oil", "refined oil",
      "seed oil"],
     "Refined seed oil — high omega-6, polyunsaturated fat oxidation → lipid peroxides",
     ["olive oil", "coconut oil", "avocado oil"]),
]


def get_food_alerts(food_name: str) -> list[dict]:
    """Return RED alerts triggered by a single food item."""
    name = f" {food_name.lower().strip()} "
    alerts = []
    for triggers, message, excludes in _RED_RULES:
        if any(t in name for t in triggers) and not any(ex in name for ex in excludes):
            alerts.append({"level": "red", "message": message})
    return alerts


def get_daily_alerts(food_log: list[dict], targets: dict,
                     day_type: str = "training") -> list[dict]:
    """Return YELLOW alerts based on daily totals."""
    alerts = []

    total_cal    = sum(float(e.get("calories", 0) or 0) for e in food_log)
    total_sat_fat = sum(float(e.get("sat_fat", 0) or 0) for e in food_log)
    total_omega6 = sum(float(e.get("omega6", 0) or 0) for e in food_log)
    total_carbs  = sum(float(e.get("carbs", 0) or 0) for e in food_log)

    # ── Whey protein (dose-dependent IGF-1 risk) ─────────────────────────────
    whey_entries = [e for e in food_log if "whey" in str(e.get("food_name", "")).lower()]
    whey_g = sum(float(e.get("quantity_g", 0) or 0) for e in whey_entries)
    whey_sources = list({str(e.get("food_name", "")).title() for e in whey_entries})
    if whey_g > 60:
        alerts.append({"level": "yellow",
                        "message": f"Whey {whey_g:.0f}g (>2 scoops) — significant IGF-1 elevation; monitor skin closely",
                        "sources": whey_sources})
    elif whey_g > 30:
        alerts.append({"level": "yellow",
                        "message": f"Whey {whey_g:.0f}g (>1 scoop) — moderate IGF-1 risk; consider plant protein alternatives",
                        "sources": whey_sources})

    # ── Full-fat dairy (volume threshold) ────────────────────────────────────
    # Skyr and greek yogurt have lower IGF-1 risk due to straining/fermentation.
    # Flag at higher threshold (200g) vs whole milk products.
    high_risk_dairy = ["milk", "cream", "full-fat yogurt", "whole milk"]
    low_risk_dairy  = ["skyr", "greek yogurt", "yoghurt", "cottage cheese"]

    high_dairy_entries = [
        e for e in food_log
        if any(t in str(e.get("food_name", "")).lower() for t in high_risk_dairy)
    ]
    low_dairy_entries = [
        e for e in food_log
        if any(t in str(e.get("food_name", "")).lower() for t in low_risk_dairy)
    ]
    high_dairy_g = sum(float(e.get("quantity_g", 0) or 0) for e in high_dairy_entries)
    low_dairy_g  = sum(float(e.get("quantity_g", 0) or 0) for e in low_dairy_entries)

    if high_dairy_g > 200:
        alerts.append({"level": "yellow",
                        "message": f"High-lactose dairy {high_dairy_g:.0f}g — IGF-1 pathway; prefer skyr or cottage cheese",
                        "sources": list({str(e.get("food_name", "")).title() for e in high_dairy_entries})})
    elif low_dairy_g > 300:
        alerts.append({"level": "yellow",
                        "message": f"Fermented dairy {low_dairy_g:.0f}g > 300g — even low-risk dairy elevates IGF-1 at high volume",
                        "sources": list({str(e.get("food_name", "")).title() for e in low_dairy_entries})})

    # ── Saturated fat cap ────────────────────────────────────────────────────
    if total_sat_fat > targets.get("sat_fat_cap", 20):
        sat_sources = sorted(
            [e for e in food_log if float(e.get("sat_fat", 0) or 0) > 1],
            key=lambda e: float(e.get("sat_fat", 0) or 0), reverse=True
        )
        alerts.append({"level": "yellow",
                        "message": f"Saturated fat {total_sat_fat:.1f}g exceeds 20g cap — mTORC1 activation risk",
                        "sources": [str(e.get("food_name", "")).title() for e in sat_sources[:4]]})

    # ── Omega-6 cap ──────────────────────────────────────────────────────────
    if total_omega6 > targets.get("omega6_cap", 12):
        o6_sources = sorted(
            [e for e in food_log if float(e.get("omega6", 0) or 0) > 0.5],
            key=lambda e: float(e.get("omega6", 0) or 0), reverse=True
        )
        alerts.append({"level": "yellow",
                        "message": f"Omega-6 {total_omega6:.1f}g > 12g — add omega-3 sources to restore 4:1 ratio",
                        "sources": [str(e.get("food_name", "")).title() for e in o6_sources[:4]]})

    # ── Medium GI carbs (whole-day weighted average) ─────────────────────────
    carb_entries = [
        e for e in food_log
        if float(e.get("carbs", 0) or 0) > 5 and e.get("gi")
    ]
    total_carb_g = sum(float(e.get("carbs", 0)) for e in carb_entries)
    if carb_entries and total_carb_g > 0:
        avg_gi = sum(
            float(e["gi"]) * float(e.get("carbs", 0)) for e in carb_entries
        ) / total_carb_g
        high_gi_entries = sorted(
            [e for e in carb_entries if float(e.get("gi", 0)) > 55],
            key=lambda e: float(e.get("gi", 0)), reverse=True
        )
        gi_sources = [str(e.get("food_name", "")).title() for e in high_gi_entries[:4]]
        if avg_gi >= 70:
            alerts.append({"level": "yellow",
                            "message": f"Average GI {avg_gi:.0f} (high ≥70) — significant insulin + IGF-1 spike",
                            "sources": gi_sources})
        elif avg_gi > 55:
            alerts.append({"level": "yellow",
                            "message": f"Average GI {avg_gi:.0f} (medium 56–69) — moderate insulin response, shift to low-GI sources",
                            "sources": gi_sources})

    # ── Oat milk GI note ─────────────────────────────────────────────────────
    if any("oat milk" in str(e.get("food_name", "")).lower() for e in food_log):
        alerts.append({"level": "yellow",
                        "message": "Oat milk has medium GI (≈62) — commercial processing hydrolyses starch; prefer almond milk if GI-sensitive",
                        "sources": ["Oat Milk"]})

    # ── Timing alerts ────────────────────────────────────────────────────────
    if any(
        "sona masoori" in str(e.get("food_name", "")).lower()
        and str(e.get("meal", "")).lower() == "lunch"
        for e in food_log
    ):
        alerts.append({"level": "yellow",
                        "message": "Sona Masoori at lunch — better timed post-workout at dinner for glycogen replenishment",
                        "sources": ["Sona Masoori Rice (Lunch)"]})

    if day_type == "rest" and any(
        "sweet potato" in str(e.get("food_name", "")).lower()
        and str(e.get("meal", "")).lower() == "lunch"
        for e in food_log
    ):
        alerts.append({"level": "yellow",
                        "message": "Sweet potato at lunch on rest day — GI 63; better post-workout timing on training days",
                        "sources": ["Sweet Potato (Lunch)"]})

    # ── Rest-day caps ─────────────────────────────────────────────────────────
    if day_type == "rest":
        if total_carbs > 200:
            carb_sources = sorted(
                [e for e in food_log if float(e.get("carbs", 0) or 0) > 10],
                key=lambda e: float(e.get("carbs", 0) or 0), reverse=True
            )
            alerts.append({"level": "yellow",
                            "message": f"Rest day carbs {total_carbs:.0f}g > 200g — insulin sensitivity is lower; reduce refined carbs",
                            "sources": [str(e.get("food_name", "")).title() for e in carb_sources[:4]]})
        if total_cal > 2100:
            cal_sources = sorted(
                food_log,
                key=lambda e: float(e.get("calories", 0) or 0), reverse=True
            )
            alerts.append({"level": "yellow",
                            "message": f"Rest day calories {total_cal:.0f} > 2,100 — limited activity; risk of caloric surplus",
                            "sources": [str(e.get("food_name", "")).title() for e in cal_sources[:4]]})

    return alerts


def get_green_indicators(food_log: list[dict], targets: dict,
                         day_type: str = "training") -> list[str]:
    """Return positive GREEN messages for the day."""
    greens = []

    total_protein = sum(float(e.get("protein", 0) or 0) for e in food_log)
    total_fibre   = sum(float(e.get("fibre", 0) or 0) for e in food_log)
    total_carbs   = sum(float(e.get("carbs", 0) or 0) for e in food_log)

    def _logged(*terms: str) -> bool:
        return any(
            any(t in str(e.get("food_name", "")).lower() for t in terms)
            for e in food_log
        )

    # ── Omega-3 ──────────────────────────────────────────────────────────────
    if _logged("salmon", "mackerel", "sardine", "herring",
               "walnut", "flaxseed", "flax seed", "flax", "chia", "hemp seed"):
        greens.append("Omega-3 source logged — EPA/DHA reduces skin inflammation via COX-2 competition")

    # ── Zinc ─────────────────────────────────────────────────────────────────
    if _logged("pumpkin seed", "oyster", "hemp seed", "chickpea", "lentil", "egg", "edamame"):
        greens.append("Zinc-rich food logged — inhibits 5-alpha-reductase, supports sebum regulation")

    # ── Vitamin A / beta-carotene ─────────────────────────────────────────────
    if _logged("carrot", "sweet potato", "kale", "spinach", "red pepper", "bell pepper"):
        greens.append("Vitamin A / carotenoid source logged — supports skin cell turnover and follicle health")

    # ── Vitamin C ────────────────────────────────────────────────────────────
    if _logged("bell pepper", "red pepper", "broccoli", "kale", "strawberr",
               "blueberr", "spinach", "cauliflower", "tomato"):
        greens.append("Vitamin C source logged — essential cofactor for collagen biosynthesis")

    # ── Polyphenols (EGCG / anthocyanins) ────────────────────────────────────
    if _logged("blueberr", "strawberr", "raspberry", "blackberr", "dark chocolate"):
        greens.append("Polyphenol-rich food logged — anthocyanins reduce CRP and skin inflammation")

    # ── Anti-inflammatory spices ─────────────────────────────────────────────
    if _logged("green tea", "turmeric", "ginger"):
        greens.append("Anti-inflammatory spice / tea logged — curcumin / gingerols / EGCG suppress cytokine signalling")

    # ── Cruciferous vegetables ────────────────────────────────────────────────
    if _logged("broccoli", "cauliflower", "kale", "brussels", "cabbage"):
        greens.append("Cruciferous vegetable logged — sulforaphane activates Nrf2 antioxidant pathway")

    # ── Protein target ───────────────────────────────────────────────────────
    if total_protein >= targets.get("protein", 160):
        greens.append(f"Protein target met ({total_protein:.0f}g) — muscle preservation + collagen synthesis supported")

    # ── Fibre ────────────────────────────────────────────────────────────────
    if total_fibre >= 30:
        greens.append(f"Excellent fibre intake ({total_fibre:.1f}g) — optimal gut microbiome + systemic inflammation control")
    elif total_fibre >= 25:
        greens.append(f"Fibre target met ({total_fibre:.1f}g) — gut health supported, skin inflammation modulated")

    # ── Low-GI day ───────────────────────────────────────────────────────────
    carb_entries = [
        e for e in food_log
        if float(e.get("carbs", 0) or 0) > 5 and e.get("gi")
    ]
    if carb_entries and all(float(e.get("gi", 100)) <= 55 for e in carb_entries):
        greens.append("Low-GI day — stable insulin throughout the day reduces sebum and inflammation")

    # ── Training day carbs on target ─────────────────────────────────────────
    if day_type == "training":
        carb_target = targets.get("carbs", 220)
        if carb_target * 0.8 <= total_carbs <= carb_target * 1.15:
            greens.append("Training day carbs on target — pre/post-workout muscle glycogen optimised")

    return greens


def get_all_alerts(food_log: list[dict], targets: dict,
                   day_type: str = "training") -> list[dict]:
    """Aggregate all alerts for display on the dashboard."""
    alerts: list[dict] = []

    seen_red: dict[str, list[str]] = {}  # message -> list of food names
    for entry in food_log:
        food_name = entry.get("food_name", "")
        for alert in get_food_alerts(food_name):
            seen_red.setdefault(alert["message"], [])
            title = food_name.title()
            if title not in seen_red[alert["message"]]:
                seen_red[alert["message"]].append(title)
    for message, sources in seen_red.items():
        alerts.append({"level": "red", "message": message, "sources": sources})

    alerts.extend(get_daily_alerts(food_log, targets, day_type))
    alerts.extend(
        {"level": "green", "message": g}
        for g in get_green_indicators(food_log, targets, day_type)
    )

    return alerts
