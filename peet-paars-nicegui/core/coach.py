# ==========================================================
# PEET PAARS — COACH ENGINE
# ==========================================================

def coach_advice(net, target):

    if net <= target:
        return "Je zit onder je dagdoel. Prima koers."

    over = net - target

    if over < 300:
        return "Je zit iets boven je doel. Morgen weer scherp."

    return "Je zit duidelijk boven je dagdoel. Kies morgen lichter."