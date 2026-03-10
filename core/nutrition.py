# ==========================================================
# PEET PAARS — NUTRITION ENGINE
# ==========================================================

def analyze_nutrition(food_items):

    total_kcal = 0
    protein = 0
    fiber = 0
    fat = 0

    for item in food_items:

        total_kcal += item.get("kcal", 0)
        protein += item.get("protein", 0)
        fiber += item.get("fiber", 0)
        fat += item.get("fat", 0)

    # eenvoudige verzadiging score
    satiety_score = 0

    if total_kcal > 0:
        satiety_score = (protein * 2 + fiber * 1.5) / total_kcal * 100

    return {
        "kcal": total_kcal,
        "protein": protein,
        "fiber": fiber,
        "fat": fat,
        "satiety": round(satiety_score, 2)
    }