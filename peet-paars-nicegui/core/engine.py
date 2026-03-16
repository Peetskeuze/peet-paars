import json
import re
from typing import Dict, Any

from core.prompt import build_prompt
from core.schema import validate_day
from core.utils import clean_text, clean_macros
from core.llm import call_llm
from pathlib import Path
from datetime import datetime
from datetime import date
from typing import Dict, Any


_DEBUG_LOG = Path(__file__).resolve().parent / "_debug_peet_paars.log"

def _dbg(msg: str):
    try:
        _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _DEBUG_LOG.write_text(_DEBUG_LOG.read_text(encoding="utf-8") + f"{ts} | {msg}\n", encoding="utf-8") \
            if _DEBUG_LOG.exists() else _DEBUG_LOG.write_text(f"{ts} | {msg}\n", encoding="utf-8")
    except Exception:
        # debug mag nooit je app laten crashen
        pass


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def start_day(day_type: str) -> Dict[str, Any]:
    """
    Enige geldige start van een Peet Paars-dag.
    UI mag hier NIET van afwijken.
    """
    if day_type not in ("rust", "sport"):
        raise ValueError("day_type moet 'rust' of 'sport' zijn")

    return {
        "meta": {
            "date": date.today().isoformat(),
            "day_type": day_type,
            "status": "open",
        },
        "budget": {
            # vaste startbudgetten – later dynamisch
            "kcal_target": 2000 if day_type == "rust" else 2300,
            "kcal_eaten": 0,
            "kcal_verbrand": 0,
        },
        "food_items": [],
        "activity_items": [],
    }



def sanitize_meal(meal: dict) -> dict:
    return {
        "moment": meal.get("moment"),
        "dish_name": clean_text(meal.get("dish_name", "")),
        "ingredients": [clean_text(i) for i in meal.get("ingredients", [])],
        "preparation": [clean_text(p) for p in meal.get("preparation", [])],
        "macros": clean_macros(meal.get("macros", {})),
    }

# -------------------------------------------------
# Main entry
# -------------------------------------------------

def run_peet_paars(day_type: str) -> dict:
    run_id = datetime.now().strftime("%H%M%S.%f")
    _dbg(f"run_peet_paars() START run_id={run_id} day_type={day_type}")

    # 1. Prompt bouwen
    prompt = build_prompt(day_type)

    # 2. LLM aanroepen
    raw = call_llm(prompt)

    # 3. JSON parsen
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("LLM output is geen geldige JSON")

    # 4. Dagtype afdwingen
    data["day_type"] = day_type

    # 5. VALIDATIE
    validate_day(data)

    # 6. SANITIZE (engine is leidend)
    meals = []
    for m in data.get("meals", []):
        meals.append(sanitize_meal(m))
    data["meals"] = meals

    # 7. Debug bewijs
    data["_debug"] = {
        "run_id": run_id,
        "engine_ts": datetime.now().isoformat(timespec="seconds"),
        "debug_log_path": str(_DEBUG_LOG),
        "engine_file": __file__,
    }

    _dbg(f"run_peet_paars() END run_id={run_id}")
    return data

