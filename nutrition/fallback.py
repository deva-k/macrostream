"""Hardcoded nutrition data per 100g.

Sources: USDA FoodData Central SR Legacy / Foundation databases.
GI values: University of Sydney GI database (PMC7791047 compendium for non-western foods).
All values are per 100g unless the key specifies a different preparation state
(e.g. "cooked", "raw").

Keys: calories (kcal), protein (g), carbs (g), fat (g), fibre (g),
      sat_fat (g), omega6 (g), gi (glycaemic index, unitless 0–100)
"""

# fmt: off
FALLBACK_DB: dict[str, dict] = {

    # ── Breakfast staples ──────────────────────────────────────────────────────
    "rolled oats":          {"calories": 379, "protein": 13.2, "carbs": 67.7, "fat":  6.9, "fibre": 10.1, "sat_fat": 1.20, "omega6":  2.4, "gi": 55},
    "oats":                 {"calories": 379, "protein": 13.2, "carbs": 67.7, "fat":  6.9, "fibre": 10.1, "sat_fat": 1.20, "omega6":  2.4, "gi": 55},
    "skyr":                 {"calories":  63, "protein": 11.0, "carbs":  4.0, "fat":  0.2, "fibre":  0.0, "sat_fat": 0.10, "omega6":  0.0, "gi": 11},
    "whey protein":         {"calories": 380, "protein": 75.0, "carbs":  7.0, "fat":  5.0, "fibre":  0.0, "sat_fat": 1.50, "omega6":  0.3, "gi": 15},
    "impact whey":          {"calories": 380, "protein": 75.0, "carbs":  7.0, "fat":  5.0, "fibre":  0.0, "sat_fat": 1.50, "omega6":  0.3, "gi": 15},
    "chia seeds":           {"calories": 486, "protein": 16.5, "carbs": 42.1, "fat": 30.7, "fibre": 34.4, "sat_fat": 3.30, "omega6":  5.8, "gi":  1},
    "chia":                 {"calories": 486, "protein": 16.5, "carbs": 42.1, "fat": 30.7, "fibre": 34.4, "sat_fat": 3.30, "omega6":  5.8, "gi":  1},
    "flaxseeds":            {"calories": 534, "protein": 18.3, "carbs": 28.9, "fat": 42.2, "fibre": 27.3, "sat_fat": 3.70, "omega6":  5.9, "gi": 35},
    "flax seeds":           {"calories": 534, "protein": 18.3, "carbs": 28.9, "fat": 42.2, "fibre": 27.3, "sat_fat": 3.70, "omega6":  5.9, "gi": 35},
    "almonds":              {"calories": 579, "protein": 21.2, "carbs": 21.6, "fat": 49.9, "fibre": 12.5, "sat_fat": 3.80, "omega6": 12.3, "gi": 15},

    # ── Protein sources ────────────────────────────────────────────────────────
    "chicken breast":             {"calories": 165, "protein": 31.0, "carbs":  0.0, "fat":  3.6, "fibre": 0.0, "sat_fat": 1.00, "omega6": 0.8, "gi":  0},
    "grilled chicken breast":     {"calories": 165, "protein": 31.0, "carbs":  0.0, "fat":  3.6, "fibre": 0.0, "sat_fat": 1.00, "omega6": 0.8, "gi":  0},
    "turkey breast":              {"calories": 135, "protein": 30.0, "carbs":  0.0, "fat":  1.0, "fibre": 0.0, "sat_fat": 0.30, "omega6": 0.2, "gi":  0},
    "turkey mince":               {"calories": 149, "protein": 19.0, "carbs":  0.0, "fat":  7.0, "fibre": 0.0, "sat_fat": 2.00, "omega6": 1.2, "gi":  0},
    "whole eggs":                 {"calories": 143, "protein": 12.6, "carbs":  0.7, "fat":  9.5, "fibre": 0.0, "sat_fat": 3.10, "omega6": 1.4, "gi":  0},
    "eggs":                       {"calories": 143, "protein": 12.6, "carbs":  0.7, "fat":  9.5, "fibre": 0.0, "sat_fat": 3.10, "omega6": 1.4, "gi":  0},
    "egg":                        {"calories": 143, "protein": 12.6, "carbs":  0.7, "fat":  9.5, "fibre": 0.0, "sat_fat": 3.10, "omega6": 1.4, "gi":  0},
    "boiled egg":                 {"calories": 155, "protein": 13.0, "carbs":  1.1, "fat": 11.0, "fibre": 0.0, "sat_fat": 3.30, "omega6": 1.5, "gi":  0},
    "lentils":                    {"calories": 116, "protein":  9.0, "carbs": 20.1, "fat":  0.4, "fibre": 7.9, "sat_fat": 0.10, "omega6": 0.2, "gi": 32},
    "green lentils":              {"calories": 116, "protein":  9.0, "carbs": 20.1, "fat":  0.4, "fibre": 7.9, "sat_fat": 0.10, "omega6": 0.2, "gi": 32},
    "puy lentils":                {"calories": 116, "protein":  9.0, "carbs": 20.1, "fat":  0.4, "fibre": 7.9, "sat_fat": 0.10, "omega6": 0.2, "gi": 32},
    "chickpeas":                  {"calories": 164, "protein":  8.9, "carbs": 27.4, "fat":  2.6, "fibre": 7.6, "sat_fat": 0.30, "omega6": 1.1, "gi": 28},
    "cottage cheese":             {"calories":  98, "protein": 11.1, "carbs":  3.4, "fat":  4.3, "fibre": 0.0, "sat_fat": 2.70, "omega6": 0.1, "gi": 30},

    # ── Oily fish (omega-3 powerhouses) ───────────────────────────────────────
    "salmon":                     {"calories": 208, "protein": 20.0, "carbs":  0.0, "fat": 13.0, "fibre": 0.0, "sat_fat": 3.10, "omega6": 0.9, "gi":  0},
    "salmon fillet":              {"calories": 208, "protein": 20.0, "carbs":  0.0, "fat": 13.0, "fibre": 0.0, "sat_fat": 3.10, "omega6": 0.9, "gi":  0},
    "mackerel":                   {"calories": 205, "protein": 18.6, "carbs":  0.0, "fat": 13.9, "fibre": 0.0, "sat_fat": 3.26, "omega6": 0.2, "gi":  0},
    "mackerel raw":               {"calories": 205, "protein": 18.6, "carbs":  0.0, "fat": 13.9, "fibre": 0.0, "sat_fat": 3.26, "omega6": 0.2, "gi":  0},
    "sardines":                   {"calories": 135, "protein": 22.0, "carbs":  0.0, "fat":  5.0, "fibre": 0.0, "sat_fat": 1.20, "omega6": 0.1, "gi":  0},
    "sardines canned":            {"calories": 135, "protein": 22.0, "carbs":  0.0, "fat":  5.0, "fibre": 0.0, "sat_fat": 1.20, "omega6": 0.1, "gi":  0},
    "sardines in water":          {"calories": 135, "protein": 22.0, "carbs":  0.0, "fat":  5.0, "fibre": 0.0, "sat_fat": 1.20, "omega6": 0.1, "gi":  0},
    "tuna":                       {"calories": 130, "protein": 29.0, "carbs":  0.0, "fat":  1.0, "fibre": 0.0, "sat_fat": 0.30, "omega6": 0.1, "gi":  0},
    "cod":                        {"calories":  82, "protein": 17.8, "carbs":  0.0, "fat":  0.7, "fibre": 0.0, "sat_fat": 0.10, "omega6": 0.0, "gi":  0},
    "prawns":                     {"calories":  99, "protein": 24.0, "carbs":  0.0, "fat":  0.3, "fibre": 0.0, "sat_fat": 0.10, "omega6": 0.0, "gi":  0},
    "shrimp":                     {"calories":  99, "protein": 24.0, "carbs":  0.0, "fat":  0.3, "fibre": 0.0, "sat_fat": 0.10, "omega6": 0.0, "gi":  0},
    "oysters":                    {"calories":  68, "protein":  7.1, "carbs":  3.9, "fat":  2.5, "fibre": 0.0, "sat_fat": 0.64, "omega6": 0.1, "gi":  0},
    "oysters raw":                {"calories":  68, "protein":  7.1, "carbs":  3.9, "fat":  2.5, "fibre": 0.0, "sat_fat": 0.64, "omega6": 0.1, "gi":  0},

    # ── Carb sources ───────────────────────────────────────────────────────────
    "quinoa":                     {"calories": 120, "protein":  4.4, "carbs": 21.3, "fat":  1.9, "fibre": 2.8, "sat_fat": 0.20, "omega6": 0.9, "gi": 53},
    "sweet potato":               {"calories":  86, "protein":  1.6, "carbs": 20.1, "fat":  0.1, "fibre": 3.0, "sat_fat": 0.00, "omega6": 0.0, "gi": 63},
    "brown rice":                 {"calories": 216, "protein":  4.5, "carbs": 45.0, "fat":  1.8, "fibre": 3.5, "sat_fat": 0.40, "omega6": 0.6, "gi": 55},
    "sona masoori rice":          {"calories": 345, "protein":  7.5, "carbs": 78.0, "fat":  0.5, "fibre": 2.0, "sat_fat": 0.10, "omega6": 0.1, "gi": 55},
    "white rice":                 {"calories": 130, "protein":  2.7, "carbs": 28.7, "fat":  0.3, "fibre": 0.4, "sat_fat": 0.10, "omega6": 0.1, "gi": 73},
    "basmati rice":               {"calories": 130, "protein":  2.7, "carbs": 28.1, "fat":  0.3, "fibre": 0.4, "sat_fat": 0.07, "omega6": 0.1, "gi": 52},
    "basmati rice cooked":        {"calories": 130, "protein":  2.7, "carbs": 28.1, "fat":  0.3, "fibre": 0.4, "sat_fat": 0.07, "omega6": 0.1, "gi": 52},

    # ── Indian pulses / dals ───────────────────────────────────────────────────
    "moong dal":                  {"calories": 105, "protein":  7.0, "carbs": 19.0, "fat":  0.4, "fibre": 4.1, "sat_fat": 0.05, "omega6": 0.2, "gi": 29},
    "moong dal cooked":           {"calories": 105, "protein":  7.0, "carbs": 19.0, "fat":  0.4, "fibre": 4.1, "sat_fat": 0.05, "omega6": 0.2, "gi": 29},
    "yellow lentils":             {"calories": 105, "protein":  7.0, "carbs": 19.0, "fat":  0.4, "fibre": 4.1, "sat_fat": 0.05, "omega6": 0.2, "gi": 29},
    "masoor dal":                 {"calories": 116, "protein":  9.0, "carbs": 20.1, "fat":  0.4, "fibre": 8.0, "sat_fat": 0.05, "omega6": 0.2, "gi": 25},
    "masoor dal cooked":          {"calories": 116, "protein":  9.0, "carbs": 20.1, "fat":  0.4, "fibre": 8.0, "sat_fat": 0.05, "omega6": 0.2, "gi": 25},
    "red lentils":                {"calories": 116, "protein":  9.0, "carbs": 20.1, "fat":  0.4, "fibre": 8.0, "sat_fat": 0.05, "omega6": 0.2, "gi": 25},
    "mung beans":                 {"calories": 105, "protein":  7.1, "carbs": 19.3, "fat":  0.4, "fibre": 7.6, "sat_fat": 0.10, "omega6": 0.2, "gi": 25},
    "mung beans cooked":          {"calories": 105, "protein":  7.1, "carbs": 19.3, "fat":  0.4, "fibre": 7.6, "sat_fat": 0.10, "omega6": 0.2, "gi": 25},

    # ── Legumes / plant protein ────────────────────────────────────────────────
    "soya chunks":                {"calories": 336, "protein": 52.0, "carbs": 33.0, "fat":  0.7, "fibre":13.0, "sat_fat": 0.10, "omega6": 0.3, "gi": 20},
    "soy chunks":                 {"calories": 336, "protein": 52.0, "carbs": 33.0, "fat":  0.7, "fibre":13.0, "sat_fat": 0.10, "omega6": 0.3, "gi": 20},
    "tofu":                       {"calories":  76, "protein":  8.0, "carbs":  1.9, "fat":  4.8, "fibre": 0.3, "sat_fat": 0.70, "omega6": 2.7, "gi": 15},
    "paneer":                     {"calories": 265, "protein": 18.3, "carbs":  1.2, "fat": 20.8, "fibre": 0.0, "sat_fat":13.00, "omega6": 0.4, "gi":  0},
    "black beans":                {"calories": 132, "protein":  8.9, "carbs": 23.7, "fat":  0.5, "fibre": 8.7, "sat_fat": 0.10, "omega6": 0.2, "gi": 30},
    "kidney beans":               {"calories": 127, "protein":  8.7, "carbs": 22.8, "fat":  0.5, "fibre": 6.4, "sat_fat": 0.10, "omega6": 0.2, "gi": 29},
    "edamame":                    {"calories": 121, "protein": 11.9, "carbs":  8.9, "fat":  5.2, "fibre": 5.2, "sat_fat": 0.62, "omega6": 1.8, "gi": 20},
    "edamame cooked":             {"calories": 121, "protein": 11.9, "carbs":  8.9, "fat":  5.2, "fibre": 5.2, "sat_fat": 0.62, "omega6": 1.8, "gi": 20},
    "greek yogurt":               {"calories":  59, "protein": 10.0, "carbs":  3.6, "fat":  0.4, "fibre": 0.0, "sat_fat": 0.10, "omega6": 0.0, "gi": 11},

    # ── Meat ──────────────────────────────────────────────────────────────────
    "mutton":                     {"calories": 122, "protein": 19.7, "carbs":  0.0, "fat":  4.6, "fibre": 0.0, "sat_fat": 1.90, "omega6": 0.4, "gi":  0},
    "mutton raw":                 {"calories": 122, "protein": 19.7, "carbs":  0.0, "fat":  4.6, "fibre": 0.0, "sat_fat": 1.90, "omega6": 0.4, "gi":  0},
    "mutton cooked":              {"calories": 234, "protein": 33.4, "carbs":  0.0, "fat": 11.1, "fibre": 0.0, "sat_fat": 5.10, "omega6": 0.8, "gi":  0},
    "mutton curry":               {"calories": 180, "protein": 20.0, "carbs":  4.0, "fat":  9.0, "fibre": 0.5, "sat_fat": 3.50, "omega6": 0.6, "gi":  5},

    # ── Healthy fats ───────────────────────────────────────────────────────────
    "olive oil":                  {"calories": 884, "protein":  0.0, "carbs":  0.0, "fat":100.0, "fibre": 0.0, "sat_fat":13.80, "omega6": 9.8, "gi":  0},
    "walnuts":                    {"calories": 654, "protein": 15.2, "carbs": 13.7, "fat": 65.2, "fibre": 6.7, "sat_fat": 6.10, "omega6":38.1, "gi": 15},
    "pumpkin seeds":              {"calories": 559, "protein": 30.2, "carbs": 10.7, "fat": 49.1, "fibre": 6.0, "sat_fat": 8.70, "omega6":20.7, "gi": 25},
    "hemp seeds":                 {"calories": 553, "protein": 31.6, "carbs":  8.7, "fat": 48.8, "fibre": 4.0, "sat_fat": 4.60, "omega6":27.4, "gi":  0},
    "hemp seeds hulled":          {"calories": 553, "protein": 31.6, "carbs":  8.7, "fat": 48.8, "fibre": 4.0, "sat_fat": 4.60, "omega6":27.4, "gi":  0},
    "avocado":                    {"calories": 160, "protein":  2.0, "carbs":  8.5, "fat": 14.7, "fibre": 6.7, "sat_fat": 2.10, "omega6": 1.7, "gi": 15},

    # ── Vegetables ────────────────────────────────────────────────────────────
    "broccoli":                   {"calories":  34, "protein":  2.8, "carbs":  6.6, "fat":  0.4, "fibre": 2.6, "sat_fat": 0.00, "omega6": 0.0, "gi": 15},
    "spinach":                    {"calories":  23, "protein":  2.9, "carbs":  3.6, "fat":  0.4, "fibre": 2.2, "sat_fat": 0.10, "omega6": 0.0, "gi": 15},
    "kale":                       {"calories":  49, "protein":  4.3, "carbs":  5.6, "fat":  1.5, "fibre": 4.1, "sat_fat": 0.18, "omega6": 0.2, "gi":  5},
    "kale raw":                   {"calories":  49, "protein":  4.3, "carbs":  5.6, "fat":  1.5, "fibre": 4.1, "sat_fat": 0.18, "omega6": 0.2, "gi":  5},
    "carrot":                     {"calories":  41, "protein":  0.9, "carbs":  9.6, "fat":  0.2, "fibre": 2.8, "sat_fat": 0.03, "omega6": 0.1, "gi": 16},
    "carrot raw":                 {"calories":  41, "protein":  0.9, "carbs":  9.6, "fat":  0.2, "fibre": 2.8, "sat_fat": 0.03, "omega6": 0.1, "gi": 16},
    "carrots":                    {"calories":  41, "protein":  0.9, "carbs":  9.6, "fat":  0.2, "fibre": 2.8, "sat_fat": 0.03, "omega6": 0.1, "gi": 16},
    "red bell pepper":            {"calories":  31, "protein":  1.0, "carbs":  6.0, "fat":  0.3, "fibre": 2.1, "sat_fat": 0.03, "omega6": 0.1, "gi": 15},
    "bell pepper":                {"calories":  31, "protein":  1.0, "carbs":  6.0, "fat":  0.3, "fibre": 2.1, "sat_fat": 0.03, "omega6": 0.1, "gi": 15},
    "red pepper":                 {"calories":  31, "protein":  1.0, "carbs":  6.0, "fat":  0.3, "fibre": 2.1, "sat_fat": 0.03, "omega6": 0.1, "gi": 15},
    "tomato":                     {"calories":  18, "protein":  0.9, "carbs":  3.9, "fat":  0.2, "fibre": 1.2, "sat_fat": 0.03, "omega6": 0.1, "gi": 15},
    "tomato raw":                 {"calories":  18, "protein":  0.9, "carbs":  3.9, "fat":  0.2, "fibre": 1.2, "sat_fat": 0.03, "omega6": 0.1, "gi": 15},
    "tomatoes":                   {"calories":  18, "protein":  0.9, "carbs":  3.9, "fat":  0.2, "fibre": 1.2, "sat_fat": 0.03, "omega6": 0.1, "gi": 15},
    "cauliflower":                {"calories":  25, "protein":  1.9, "carbs":  5.0, "fat":  0.3, "fibre": 2.0, "sat_fat": 0.06, "omega6": 0.0, "gi": 15},
    "cauliflower raw":            {"calories":  25, "protein":  1.9, "carbs":  5.0, "fat":  0.3, "fibre": 2.0, "sat_fat": 0.06, "omega6": 0.0, "gi": 15},
    "cucumber":                   {"calories":  15, "protein":  0.7, "carbs":  3.6, "fat":  0.1, "fibre": 0.5, "sat_fat": 0.04, "omega6": 0.0, "gi": 15},
    "cucumber raw":               {"calories":  15, "protein":  0.7, "carbs":  3.6, "fat":  0.1, "fibre": 0.5, "sat_fat": 0.04, "omega6": 0.0, "gi": 15},

    # ── Fruits ────────────────────────────────────────────────────────────────
    "banana":                     {"calories":  89, "protein":  1.1, "carbs": 23.0, "fat":  0.3, "fibre": 2.6, "sat_fat": 0.10, "omega6": 0.0, "gi": 51},
    "apple":                      {"calories":  52, "protein":  0.3, "carbs": 14.0, "fat":  0.2, "fibre": 2.4, "sat_fat": 0.00, "omega6": 0.0, "gi": 36},
    "blueberries":                {"calories":  57, "protein":  0.7, "carbs": 14.5, "fat":  0.3, "fibre": 2.4, "sat_fat": 0.03, "omega6": 0.1, "gi": 53},
    "blueberry":                  {"calories":  57, "protein":  0.7, "carbs": 14.5, "fat":  0.3, "fibre": 2.4, "sat_fat": 0.03, "omega6": 0.1, "gi": 53},
    "strawberries":               {"calories":  32, "protein":  0.7, "carbs":  7.7, "fat":  0.3, "fibre": 2.0, "sat_fat": 0.02, "omega6": 0.1, "gi": 40},
    "strawberry":                 {"calories":  32, "protein":  0.7, "carbs":  7.7, "fat":  0.3, "fibre": 2.0, "sat_fat": 0.02, "omega6": 0.1, "gi": 40},

    # ── Spices & condiments ────────────────────────────────────────────────────
    "turmeric":                   {"calories": 312, "protein":  9.7, "carbs": 67.1, "fat":  3.3, "fibre":22.7, "sat_fat": 1.84, "omega6": 0.6, "gi":  0},
    "turmeric powder":            {"calories": 312, "protein":  9.7, "carbs": 67.1, "fat":  3.3, "fibre":22.7, "sat_fat": 1.84, "omega6": 0.6, "gi":  0},
    "ginger":                     {"calories":  80, "protein":  1.8, "carbs": 17.8, "fat":  0.8, "fibre": 2.0, "sat_fat": 0.20, "omega6": 0.2, "gi": 15},
    "ginger raw":                 {"calories":  80, "protein":  1.8, "carbs": 17.8, "fat":  0.8, "fibre": 2.0, "sat_fat": 0.20, "omega6": 0.2, "gi": 15},
    "fresh ginger":               {"calories":  80, "protein":  1.8, "carbs": 17.8, "fat":  0.8, "fibre": 2.0, "sat_fat": 0.20, "omega6": 0.2, "gi": 15},

    # ── Polyphenol / antioxidant foods ─────────────────────────────────────────
    "dark chocolate":             {"calories": 598, "protein":  7.8, "carbs": 45.9, "fat": 42.6, "fibre":10.9, "sat_fat":24.50, "omega6": 1.2, "gi": 25},
    "dark chocolate 70":          {"calories": 598, "protein":  7.8, "carbs": 45.9, "fat": 42.6, "fibre":10.9, "sat_fat":24.50, "omega6": 1.2, "gi": 25},
    "dark chocolate 85":          {"calories": 598, "protein":  7.8, "carbs": 45.9, "fat": 42.6, "fibre":10.9, "sat_fat":24.50, "omega6": 1.2, "gi": 20},

    # ── Seeds ─────────────────────────────────────────────────────────────────
    # Note: hemp seeds are high omega-6 (27.4g/100g) — alerts will fire at >44g portion
    # Note: almonds omega-6 = 12.3g/100g — alerts at >97g portion

    # ── Plant milks ───────────────────────────────────────────────────────────
    "almond milk":                {"calories":  15, "protein":  0.6, "carbs":  0.3, "fat":  1.2, "fibre": 0.0, "sat_fat": 0.10, "omega6": 0.3, "gi": 25},
    "almond milk unsweetened":    {"calories":  15, "protein":  0.6, "carbs":  0.3, "fat":  1.2, "fibre": 0.0, "sat_fat": 0.10, "omega6": 0.3, "gi": 25},
    "oat milk":                   {"calories":  48, "protein":  0.8, "carbs":  6.6, "fat":  1.5, "fibre": 0.5, "sat_fat": 0.20, "omega6": 0.4, "gi": 62},
    "oat milk unsweetened":       {"calories":  48, "protein":  0.8, "carbs":  6.6, "fat":  1.5, "fibre": 0.5, "sat_fat": 0.20, "omega6": 0.4, "gi": 62},

    # ── Red-alert foods (included so alerts fire on cached lookups too) ────────
    "peanut butter":              {"calories": 588, "protein": 25.1, "carbs": 20.1, "fat": 50.4, "fibre": 5.4, "sat_fat":10.00, "omega6":15.6, "gi": 14},
    "peanuts":                    {"calories": 567, "protein": 25.8, "carbs": 16.1, "fat": 49.2, "fibre": 8.5, "sat_fat": 6.80, "omega6":15.7, "gi": 14},
}
# fmt: on


_COOKING_PREFIXES = {
    "grilled", "boiled", "raw", "fresh", "cooked", "baked", "steamed",
    "fried", "roasted", "poached", "smoked", "canned", "dried",
    "myprotein", "my protein",
}


def _normalise(name: str) -> str:
    """Strip cooking-method prefixes and brand names to improve DB hit rate."""
    tokens = name.lower().strip().split()
    while tokens and tokens[0] in _COOKING_PREFIXES:
        tokens = tokens[1:]
    return " ".join(tokens)


def lookup(food_name: str) -> dict | None:
    """Return per-100g macros from the hardcoded DB with normalisation + fuzzy fallback."""
    key = food_name.lower().strip()

    # 1. Exact match
    if key in FALLBACK_DB:
        return dict(FALLBACK_DB[key])

    # 2. Normalised match (strip cooking prefixes / brand names)
    norm = _normalise(key)
    if norm and norm in FALLBACK_DB:
        return dict(FALLBACK_DB[norm])

    # 3. Substring match
    for db_key, data in FALLBACK_DB.items():
        if key in db_key or db_key in key:
            return dict(data)

    # 4. Normalised substring match
    if norm:
        for db_key, data in FALLBACK_DB.items():
            if norm in db_key or db_key in norm:
                return dict(data)

    # 5. Token overlap (handles minor typos: "green lentills" → "green lentils")
    key_tokens = set(key.split())
    best_score, best_data = 0, None
    for db_key, data in FALLBACK_DB.items():
        db_tokens = set(db_key.split())
        overlap = len(key_tokens & db_tokens)
        if overlap and overlap == len(db_tokens):   # all DB-key words appear in query
            if overlap > best_score:
                best_score, best_data = overlap, data
    if best_data:
        return dict(best_data)

    return None


def scale(macros_per_100g: dict, quantity_g: float) -> dict:
    """Scale per-100g macros to the given quantity."""
    factor = quantity_g / 100.0
    scaled = {}
    for k, v in macros_per_100g.items():
        if k == "gi":
            scaled[k] = v   # GI is an index, not a quantity — does not scale
        else:
            try:
                scaled[k] = round(float(v) * factor, 1)
            except (TypeError, ValueError):
                scaled[k] = v
    return scaled
