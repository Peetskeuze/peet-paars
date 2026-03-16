# ==========================================================
# PEET PAARS — DAY ANALYSIS
# ==========================================================

def analyze_day(day_rec):

    eaten = sum(i.get("kcal", 0) for i in day_rec.get("food_items", []))
    burned = sum(i.get("kcal", 0) for i in day_rec.get("activity_items", []))

    net = eaten - burned

    return {
        "eaten": eaten,
        "burned": burned,
        "net": net
    }