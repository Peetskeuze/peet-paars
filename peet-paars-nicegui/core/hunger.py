# ==========================================================
# PEET PAARS — HUNGER PREDICTOR
# ==========================================================

def predict_hunger(nutrition):

    protein = nutrition.get("protein", 0)
    satiety = nutrition.get("satiety", 0)

    if protein < 40:
        return "Eiwit vandaag is laag. Kans op trek later."

    if satiety < 5:
        return "Verzadiging vandaag is laag. Kies eiwit of vezels."

    if protein > 80:
        return "Eiwitniveau is goed. Honger later minder waarschijnlijk."

    return "Voedingsbalans lijkt stabiel."