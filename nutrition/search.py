"""Nutrition data lookup pipeline.

Priority:
  1. FoodCache sheet      — exact match on previous lookups (incl. corrected typos)
  2. USDA hardcoded table — instant hit for ~35 common foods + fuzzy normalisation
  3. Gemini Flash API     — free LLM (Google AI Studio, 1500 req/day); handles typos/synonyms
  4. Groq API             — free LLM fallback (llama-3.1-8b-instant)
  5. DuckDuckGo search    — free web search, no API key needed
"""

from __future__ import annotations

import json
import os
import re

import streamlit as st

from nutrition.fallback import lookup as fallback_lookup, scale
from sheets.food_log import get_cached_food, cache_food


# ── Key helpers ────────────────────────────────────────────────────────────────

def _secret(key: str) -> str | None:
    try:
        return st.secrets.get(key) or os.getenv(key)
    except Exception:
        return os.getenv(key)


# ── Shared LLM prompt ──────────────────────────────────────────────────────────

_NUTRITION_PROMPT = """You are a precise nutrition database assistant.

Return nutrition facts per 100g for: "{food_name}"

Rules:
- Correct any spelling mistakes in the food name silently.
- Use standard USDA nutritional database values.
- Estimate omega-6 if not available (acceptable to use 0 for pure protein/carb foods).
- GI (glycaemic index) should be null for foods with negligible carbs.

Respond with ONLY a valid JSON object — no explanation, no markdown:
{{
  "food_name": "<corrected canonical name>",
  "calories": <number kcal>,
  "protein": <number g>,
  "carbs": <number g total carbohydrates>,
  "fat": <number g total fat>,
  "fibre": <number g dietary fibre>,
  "sat_fat": <number g saturated fat>,
  "omega6": <number g omega-6 fatty acids>,
  "gi": <number 0-100 or null>
}}"""


# ── Query parsing ──────────────────────────────────────────────────────────────

def _parse_quantity(query: str) -> tuple[str, float]:
    """Extract (food_name, quantity_g) from a free-text query."""
    query = query.strip()
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(g|kg|ml|l|oz|tbsp|tsp|cup|cups|piece|pieces|slice|slices|scoop|scoops)s?\b",
        query, re.I,
    )
    if match:
        qty_raw = float(match.group(1))
        unit = match.group(2).lower().rstrip("s")
        food_name = (query[: match.start()] + query[match.end():]).strip().strip(",").strip()
        unit_map = {
            "g": 1, "kg": 1000, "ml": 1, "l": 1000,
            "oz": 28.35, "tbsp": 15, "tsp": 5,
            "cup": 240, "piece": 100, "slice": 30, "scoop": 30,
        }
        quantity_g = qty_raw * unit_map.get(unit, 1)
    else:
        food_name = query
        quantity_g = 100.0

    return food_name.lower().strip(), round(quantity_g, 1)


# ── Helper: parse LLM JSON response ───────────────────────────────────────────

def _parse_llm_json(text: str) -> dict | None:
    text = text.strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    try:
        data = json.loads(text)
        return data if "calories" in data else None
    except Exception:
        return None


# ── Source 3: Gemini Flash (free) ─────────────────────────────────────────────

def _lookup_gemini(food_name: str) -> dict | None:
    """Ask Gemini 1.5 Flash for per-100g nutrition facts (free tier via AI Studio)."""
    import sys
    api_key = _secret("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=_NUTRITION_PROMPT.format(food_name=food_name),
        )
        return _parse_llm_json(response.text)
    except Exception as e:
        err = str(e)
        if "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            print(
                f"[macrostream] Gemini quota exhausted. Your API key may have limit=0. "
                f"Get a fresh key at https://aistudio.google.com — click 'Get API key'.",
                file=sys.stderr,
            )
        else:
            print(f"[macrostream] Gemini lookup failed for '{food_name}': {e}", file=sys.stderr)
        return None


# ── Source 4: Groq (free) ─────────────────────────────────────────────────────

def _lookup_groq(food_name: str) -> dict | None:
    """Ask Groq llama-3.1-8b-instant for per-100g nutrition facts (free tier)."""
    import sys
    api_key = _secret("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": _NUTRITION_PROMPT.format(food_name=food_name)}],
            max_tokens=300,
        )
        return _parse_llm_json(chat.choices[0].message.content)
    except Exception as e:
        print(f"[macrostream] Groq lookup failed for '{food_name}': {e}", file=sys.stderr)
        return None


# ── Source 5: DuckDuckGo (free, no API key) ───────────────────────────────────

def _extract_macros_from_text(text: str) -> dict:
    t = text.lower()
    result = {}
    patterns = {
        "calories": r"(?:calories?|energy|kcal)[:\s]*(\d+(?:\.\d+)?)",
        "protein":  r"protein[:\s]*(\d+(?:\.\d+)?)\s*g",
        "carbs":    r"(?:carb(?:ohydrate)?s?)[:\s]*(\d+(?:\.\d+)?)\s*g",
        "fat":      r"(?:total\s+)?fat[:\s]*(\d+(?:\.\d+)?)\s*g",
        "fibre":    r"(?:dietary\s+)?fi(?:b|er)(?:re)?[:\s]*(\d+(?:\.\d+)?)\s*g",
        "sat_fat":  r"saturated\s+fat[:\s]*(\d+(?:\.\d+)?)\s*g",
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, t)
        if m:
            result[key] = float(m.group(1))
    return result if "calories" in result else {}


def _lookup_duckduckgo(food_name: str) -> dict | None:
    """Search DuckDuckGo for nutrition info — no API key required."""
    import sys
    try:
        from duckduckgo_search import DDGS
        query = f"{food_name} per 100g calories protein carbs fat nutritional information"
        results = list(DDGS().text(query, max_results=5))
        for r in results:
            text = f"{r.get('title', '')} {r.get('body', '')}"
            macros = _extract_macros_from_text(text)
            if macros:
                return macros
    except Exception as e:
        print(f"[macrostream] DuckDuckGo lookup failed for '{food_name}': {e}", file=sys.stderr)
    return None


# ── Main entry point ───────────────────────────────────────────────────────────

def get_nutrition(query: str) -> dict | None:
    """Return scaled macros for the requested food+quantity.

    Result keys: food_name, quantity_g, source, calories, protein, carbs, fat,
                 fibre, sat_fat, omega6, gi, plus _per100_* for each macro.
    Returns None only if every source fails.
    """
    food_name, quantity_g = _parse_quantity(query)
    cache_key = re.sub(r"\s+", "_", food_name)

    # ── 1. FoodCache (Sheets) ──────────────────────────────────────────────────
    cached = get_cached_food(cache_key)
    if cached:
        per100 = {
            "calories": float(cached.get("calories_per100") or 0),
            "protein":  float(cached.get("protein_per100")  or 0),
            "carbs":    float(cached.get("carbs_per100")    or 0),
            "fat":      float(cached.get("fat_per100")      or 0),
            "fibre":    float(cached.get("fibre_per100")    or 0),
            "sat_fat":  float(cached.get("sat_fat_per100")  or 0),
            "omega6":   float(cached.get("omega6_per100")   or 0),
            "gi":       cached.get("gi") or None,
        }
        result = scale(per100, quantity_g)
        result.update({"food_name": cached.get("food_name", food_name),
                        "quantity_g": quantity_g, "source": "cache"})
        result.update({f"_per100_{k}": v for k, v in per100.items()})
        return result

    # ── 2. USDA hardcoded table ────────────────────────────────────────────────
    macros = fallback_lookup(food_name)
    source = "usda"

    # ── 3. Gemini Flash (free LLM) ─────────────────────────────────────────────
    if not macros:
        macros = _lookup_gemini(food_name)
        source = "gemini"

    # ── 4. Groq (free LLM fallback) ───────────────────────────────────────────
    if not macros:
        macros = _lookup_groq(food_name)
        source = "groq"

    # ── 5. DuckDuckGo (free web search) ───────────────────────────────────────
    if not macros:
        macros = _lookup_duckduckgo(food_name)
        source = "duckduckgo"

    if not macros:
        return None

    # Use LLM's corrected food name if available
    canonical_name = macros.get("food_name", food_name) if source in ("gemini", "groq") else food_name

    per100 = {
        "calories": float(macros.get("calories") or 0),
        "protein":  float(macros.get("protein")  or 0),
        "carbs":    float(macros.get("carbs")     or 0),
        "fat":      float(macros.get("fat")       or 0),
        "fibre":    float(macros.get("fibre")     or 0),
        "sat_fat":  float(macros.get("sat_fat")   or 0),
        "omega6":   float(macros.get("omega6")    or 0),
        "gi":       macros.get("gi") or None,
    }

    # Store in FoodCache for future lookups
    cache_food(cache_key, {
        "food_name": canonical_name,
        **{f"{k}_per100": v for k, v in per100.items() if k != "gi"},
        "gi": per100["gi"] or "",
    })

    result = scale(per100, quantity_g)
    result.update({"food_name": canonical_name, "quantity_g": quantity_g, "source": source})
    result.update({f"_per100_{k}": v for k, v in per100.items()})
    return result
