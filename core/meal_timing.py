# ==========================================================
# PEET PAARS — MEAL TIMING ENGINE
# ==========================================================

from datetime import datetime


def hours_since_last_meal(food_items):

    if not food_items:
        return None

    latest = None

    for item in food_items:

        ts = item.get("timestamp")

        if not ts:
            continue

        try:
            t = datetime.fromisoformat(ts)
        except:
            continue

        if latest is None or t > latest:
            latest = t

    if latest is None:
        return None

    now = datetime.now()

    delta = now - latest

    hours = delta.total_seconds() / 3600

    return round(hours, 1)