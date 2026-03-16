# ==========================================================
# PEET PAARS — NUTRITION ENGINE
# ==========================================================

def analyze_nutrition(food_items):

    totals = {
        "kcal": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0,
        "fiber": 0
    }

    for item in food_items:

        totals["kcal"] += item.get("kcal", 0)
        totals["protein"] += item.get("protein", 0)
        totals["fat"] += item.get("fat", 0)
        totals["carbs"] += item.get("carbs", 0)
        totals["fiber"] += item.get("fiber", 0)

    # satiety score
    satiety_score = 0

    if totals["kcal"] > 0:

        satiety_score = (
            totals["protein"] * 2 +
            totals["fiber"] * 1.5
        ) / totals["kcal"] * 100

    return {
        "kcal": round(totals["kcal"], 1),
        "protein": round(totals["protein"], 1),
        "fat": round(totals["fat"], 1),
        "carbs": round(totals["carbs"], 1),
        "fiber": round(totals["fiber"], 1),
        "satiety": round(satiety_score, 2)
    }