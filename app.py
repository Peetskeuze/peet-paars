import streamlit as st


import streamlit as st
from core.engine import start_day


# ============================================================
# BLOK A — State init (canon)
# ============================================================

if "food_items" not in st.session_state:
    st.session_state["food_items"] = []

if "activity_items" not in st.session_state:
    st.session_state["activity_items"] = []


# ============================================================
# app.py — DAGSTART (ENIGE INSTANTIE)
#=============================================================

if "day" not in st.session_state:
    day_type = "rust"

    st.session_state["day"] = start_day(day_type)

# ------------------------------------------------------------
# DAG ALS HANDIGE AFKORTING
# ------------------------------------------------------------
day = st.session_state["day"]

# ------------------------------------------------------------
# TIJDELIJK DAGPLAN (OPTIE 1 – STABIEL)
# ------------------------------------------------------------
if "data" not in st.session_state or st.session_state.data is None:
    st.session_state.data = {
        "peet_message": "Vandaag rustig aan. Eet normaal, beweeg licht.",
        "coach_message": "Dit is een testdagplan om de app weer te laten lopen.",
        "meals": [
            {
                "moment": "Ontbijt",
                "dish_name": "Kwark met fruit",
                "macros": {
                    "kcal": 300,
                    "protein_g": 25,
                    "carbs_g": 30,
                    "fat_g": 5,
                },
                "ingredients": [
                    "250 g magere kwark",
                    "handje blauwe bessen",
                ],
                "preparation": [
                    "Doe de kwark in een kom.",
                    "Voeg het fruit toe.",
                ],
            },
            {
                "moment": "Lunch",
                "dish_name": "Boterham met ei",
                "macros": {
                    "kcal": 400,
                    "protein_g": 22,
                    "carbs_g": 35,
                    "fat_g": 14,
                },
                "ingredients": [
                    "2 volkoren boterhammen",
                    "2 eieren",
                ],
                "preparation": [
                    "Bak de eieren.",
                    "Beleg de boterhammen.",
                ],
            },
        ],
    }

# ------------------------------------------------------------
# TIJDELIJKE DAGSTATUS (STAP A STABILITEIT)
# ------------------------------------------------------------
if "day_closed" not in st.session_state:
    st.session_state["day_closed"] = False

# ------------------------------------------------------------
# TIJDELIJK DAGBUDGET (STAP A STABILITEIT)
# ------------------------------------------------------------
daily_budget = 1800


# ============================================================
# BLOK 2 — Invoer alleen bij open dag
# ============================================================

if not st.session_state["day_closed"]:
    # ⬇️ HIER KOMEN JE BESTAANDE BLOKKEN:
    # - Wat heb je gegeten / gedronken
    # - Wat heb je bewogen
    pass
else:
    st.info("Deze dag is afgesloten. Start een nieuwe dag om verder te gaan.")

# ============================================================
# v1.1 — BLOK 2.1a
# Datamodel voor eet-items (parallel, geen vervanging)
# ============================================================

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class FoodItem:
    id: str
    product: str          # bijv. "boterham", "kaas", "bier"
    amount: float         # hoeveelheid (numeriek)
    unit: str             # "stuk", "gram", "ml"
    kcal: int             # berekende kcal voor dit item
    timestamp: str        # ISO-timestamp

from dataclasses import dataclass

@dataclass
class ActivityItem:
    activity: str
    duration: int
    burned_kcal: int

# ============================================================
# v1.3 — Vrij kcal-item (MODEL)
# ============================================================

class FreeKcalItem:
    def __init__(self, name: str, kcal: int):
        self.id = f"free_{name}_{kcal}"
        self.product = name
        self.amount = 1
        self.unit = "vrij"
        self.kcal = int(kcal)
        self.timestamp = datetime.now().isoformat()

# ============================================================
# v1.1 — BLOK 2.2a
# Activiteitstypes met vaste kcal per minuut
# ============================================================

ACTIVITY_KCAL_PER_MIN = {
    "wandelen": 4,
    "fietsen": 8,
    "hardlopen": 10,
    "krachttraining": 6,
    "zwemmen": 9,
    "spinnen": 9,
    "sport algemeen": 6,
}
# ============================================================
# PRODUCTMODEL v1 — vaste producten en eenheden
# ============================================================

PRODUCTS = {
    # ----------------------------
    # ETEN (gram / stuk)
    # ----------------------------
    "brood": {
        "label": "Brood (volkoren)",
        "category": "food",
        "unit": "gram",
        "kcal_per_100g": 240,
    },
    "kaas": {
        "label": "Kaas (jong belegen)",
        "category": "food",
        "unit": "gram",
        "kcal_per_100g": 356,
    },
    "kipfilet": {
        "label": "Kipfilet",
        "category": "food",
        "unit": "gram",
        "kcal_per_100g": 110,
    },
    "ei": {
        "label": "Ei",
        "category": "food",
        "unit": "stuk",
        "kcal_per_piece": 75,
    },

    # ----------------------------
    # DRANKEN (cl)
    # ----------------------------
    "bier": {
        "label": "Bier",
        "category": "drink",
        "unit": "cl",
        "kcal_per_100ml": 43,
    },
    "wijn": {
        "label": "Wijn",
        "category": "drink",
        "unit": "cl",
        "kcal_per_100ml": 85,
    },

    # ----------------------------
    # VETTEN / OLIE (eetlepels)
    # ----------------------------
    "olijfolie": {
        "label": "Olijfolie",
        "category": "fat",
        "unit": "eetlepel",
        "kcal_per_tbsp": 90,
    },
}

# ============================================================
# WW PAARS — 0-PUNTEN REFERENTIELIJST v2 (MET KCAL)
# REFERENTIE-ONLY — GEEN REKENLOGICA
# ============================================================

WW_ZERO_FOODS = {
    "kipfilet": {"kcal": 110, "per": "100 g bereid"},
    "kalkoen": {"kcal": 105, "per": "100 g bereid"},
    "mager rundvlees": {"kcal": 120, "per": "100 g bereid"},
    "witvis": {"kcal": 90, "per": "100 g bereid"},
    "zalm": {"kcal": 200, "per": "100 g bereid"},
    "ei": {"kcal": 75, "per": "1 stuk"},
    "tofu": {"kcal": 120, "per": "100 g"},
    "tempeh": {"kcal": 160, "per": "100 g"},
    "linzen": {"kcal": 110, "per": "100 g gekookt"},
    "kikkererwten": {"kcal": 120, "per": "100 g gekookt"},
    "magere kwark": {"kcal": 60, "per": "100 g"},
    "skyr": {"kcal": 65, "per": "100 g"},
    "halfvolle melk": {"kcal": 46, "per": "100 ml"},
    "magere melk": {"kcal": 34, "per": "100 ml"},
    "broccoli": {"kcal": 35, "per": "100 g"},
    "bloemkool": {"kcal": 25, "per": "100 g"},
    "courgette": {"kcal": 20, "per": "100 g"},
    "paprika": {"kcal": 30, "per": "100 g"},
    "spinazie": {"kcal": 20, "per": "100 g"},
    "appel": {"kcal": 55, "per": "1 middelgrote"},
    "peer": {"kcal": 60, "per": "1 middelgrote"},
    "aardbeien": {"kcal": 30, "per": "100 g"},
    "aardappelen": {"kcal": 75, "per": "100 g gekookt"},
    "zoete aardappel": {"kcal": 85, "per": "100 g gekookt"},
    "rode wijn": {"kcal": 85, "per": "100 ml"},
}

# ============================================================
# WW PAARS — PRODUCTVERTALING NAAR PRODUCTS
# ============================================================

PRODUCTS_WW = {}

for name, data in WW_ZERO_FOODS.items():
    key = name.lower().replace(" ", "_")
    per = data["per"]

    if "100 ml" in per:
        PRODUCTS_WW[key] = {
            "label": name.capitalize(),
            "category": "ww_basis",
            "unit": "ml",
            "kcal_per_100ml": data["kcal"],
            "ww_basis": True,
        }

    elif "100 g" in per:
        PRODUCTS_WW[key] = {
            "label": name.capitalize(),
            "category": "ww_basis",
            "unit": "gram",
            "kcal_per_100g": data["kcal"],
            "ww_basis": True,
        }

    elif "1 stuk" in per:
        PRODUCTS_WW[key] = {
            "label": name.capitalize(),
            "category": "ww_basis",
            "unit": "stuk",
            "kcal_per_piece": data["kcal"],
            "ww_basis": True,
        }

# ============================================================
# MERGE — WW-PRODUCTEN TOEVOEGEN AAN PRODUCTS
# ============================================================

PRODUCTS = {
    **PRODUCTS,
    **PRODUCTS_WW,
}

# ------------------------------------------------------------
# Kcal-berekening — PRODUCTMODEL v1
# ------------------------------------------------------------
def calculate_food_kcal(product, amount, unit=None):
    if product["unit"] == "gram":
        return int((product["kcal_per_100g"] / 100) * amount)

    if product["unit"] == "cl":
        ml = amount * 10
        return int((product["kcal_per_100ml"] / 100) * ml)

    if product["unit"] == "ml":
        return int((product["kcal_per_100ml"] / 100) * amount)

    if product["unit"] == "eetlepel":
        return int(product["kcal_per_tbsp"] * amount)

    if product["unit"] == "stuk":
        return int(product["kcal_per_piece"] * amount)

    return 0

# ------------------------------------------------------------
# Page config
# ------------------------------------------------------------
st.set_page_config(
    page_title="Peet Paars",
    layout="centered"
)

st.title("Peet Paars")
st.caption("Dagkeuze voor rust- en sportdagen")

# ------------------------------------------------------------
#CSS
# ------------------------------------------------------------

st.markdown("""
<style>
.peet-scroll {
    max-height: 320px;
    overflow-y: auto;
    padding-right: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# BLOK 1 — PLAN
# Dagtype + engine-aanroep
# ============================================================

# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
if "data" not in st.session_state:
    st.session_state.data = None

# ============================================================
# v1.2-A — Datalaag voorbereiden (PASSIEF)
# ============================================================

if "meal_consumptions" not in st.session_state:
    st.session_state["meal_consumptions"] = []



# ------------------------------------------------------------
# Render resultaat
# ------------------------------------------------------------
data = st.session_state.data

if not data:

# ============================================================
# BLOK 1 — PLAN (voorstel van de dag)
# ============================================================
# ------------------------------------------------------------
# GEEN DAGPLAN? DAN HIER STOPPEN (STABIELE TUSSENFASE)
# ------------------------------------------------------------
    if data is None:
        st.info("Dag gestart. Er is nog geen dagplan.")
        st.stop()
# -------------------------
# Dagboodschap
# -------------------------
st.subheader("Vandaag")

peet_message = data.get("peet_message")
coach_message = data.get("coach_message")

if peet_message:
    st.write(peet_message)

if coach_message:
    st.caption(coach_message)

# -------------------------
# Maaltijden
# -------------------------
for meal in data.get("meals", []):
    moment = meal.get("moment", "").upper()
    dish_name = meal.get("dish_name", "")
    macros = meal.get("macros") or {}
    ingredients = meal.get("ingredients") or []
    preparation = meal.get("preparation") or []

    with st.container(border=True):
        st.markdown(f"### {moment}")

        # START: scrollbare inhoud
        st.markdown("<div class='peet-scroll'>", unsafe_allow_html=True)

        if dish_name:
            st.write(dish_name)

        if macros:
            kcal = macros.get("kcal", 0)
            protein = macros.get("protein_g", 0)
            carbs = macros.get("carbs_g", 0)
            fat = macros.get("fat_g", 0)
            st.caption(
                f"± {kcal} kcal · eiwit {protein} g · kh {carbs} g · vet {fat} g"
            )

        if ingredients:
            st.markdown("**Ingrediënten**")
            for ing in ingredients:
                st.write(f"- {ing}")

        if preparation:
            st.markdown("**Bereiding**")
            for i, step in enumerate(preparation, start=1):
                st.write(f"{i}. {step}")

        # END: scrollbare inhoud
        st.markdown("</div>", unsafe_allow_html=True)

        # ============================================================
        # v1.2-B — PLAN: markeer gepland gerecht als gegeten (UI only)
        # ============================================================

        from datetime import date, datetime

        meal_id = f"{moment.lower()}_{dish_name}"
        meal_label = moment
        planned_kcal = macros.get("kcal", 0)

        st.markdown("**Wat heb je hiervan daadwerkelijk gegeten?**")

        today = date.today().isoformat()

        choice = st.radio(
            "Portie",
            options=[
                "Niet gegeten",
                "Ongeveer de helft",
                "Alles gegeten",
            ],
            index=None,
            horizontal=True,
            label_visibility="collapsed",
            key=f"meal_consumption_choice_{meal_id}"
        )


        if choice is not None:
            portion_map = {
                "Niet gegeten": 0.0,
                "Ongeveer de helft": 0.5,
                "Alles gegeten": 1.0,
            }

            portion_factor = portion_map[choice]

            st.session_state["meal_consumptions"] = [
                mc for mc in st.session_state["meal_consumptions"]
                if not (mc["meal_id"] == meal_id and mc["date"] == today)
            ]

            st.session_state["meal_consumptions"].append({
                "meal_id": meal_id,
                "meal_label": meal_label,
                "planned_kcal": planned_kcal,
                "portion_factor": portion_factor,
                "consumed_kcal": planned_kcal * portion_factor,
                "source": "planned_meal",
                "date": today,
                "timestamp": datetime.now().isoformat(),
            })

    # BLOK 2 — REALITEIT

if False:


    # ============================================================
    # BLOK 2.1 — Vastleggen wat daadwerkelijk gegeten is
    # ============================================================
    import uuid
    from datetime import datetime

    if "eaten" not in st.session_state:
        st.session_state["eaten"] = []

    st.subheader("Wat heb je daadwerkelijk gegeten?")

    label = st.text_input("Wat was het?")
    amount = st.text_input("Hoeveel?")
    kcal = st.number_input(
        "Geschatte kcal (optioneel)",
        min_value=0,
        step=10,
        value=0
    )

    if st.button("Opslaan wat ik heb gegeten"):
        st.session_state["eaten"].append({
            "meal_id": str(uuid.uuid4()),
            "label": label,
            "amount": amount,
            "kcal_estimate": kcal if kcal > 0 else None,
            "timestamp": datetime.now().isoformat()
        })
# ============================================================
# HARD SLOT — geen invoer mogelijk na afsluiten dag
# ============================================================

if st.session_state.get("day_closed", False):
    st.info("Deze dag is afgesloten. Start een nieuwe dag om verder te gaan.")
    st.stop()

# ============================================================
# BLOK 2.1 — Eten / drinken toevoegen (PRODUCTMODEL v1 — CANON)
# ============================================================

import uuid
from datetime import datetime

st.subheader("Wat heb je gegeten of gedronken?")

# labels en keys uit PRODUCTS
_product_keys = list(PRODUCTS.keys())
_product_labels = [PRODUCTS[k]["label"] for k in _product_keys]

# ----------------------------
# Product + hoeveelheid (BUITEN form)
# ----------------------------

selected_label = st.selectbox(
    "Product",
    _product_labels,
    key="food_product_label"
)

selected_key = _product_keys[_product_labels.index(selected_label)]
p = PRODUCTS[selected_key]

unit_fixed = p["unit"]

if unit_fixed in ("gram", "cl", "stuk"):
    amount = st.number_input(
        f"Hoeveelheid ({unit_fixed})",
        min_value=0,
        step=5,
        value=0,
        key="food_amount"
    )
else:
    amount = st.number_input(
        "Hoeveelheid (eetlepel)",
        min_value=0.0,
        step=0.5,
        value=0.0,
        key="food_amount"
    )

st.caption(f"Eenheid vast: {unit_fixed}")

# ----------------------------
# Form — alleen toevoegen
# ----------------------------

with st.form("food_form", clear_on_submit=True):

    submitted = st.form_submit_button("Item toevoegen")

    if submitted:
        if amount <= 0:
            st.warning("Vul een hoeveelheid in groter dan 0.")
        else:
            kcal = calculate_food_kcal(p, amount)

            st.session_state["food_items"].append(
                FoodItem(
                    id=str(uuid.uuid4()),
                    product=p["label"],
                    amount=float(amount),
                    unit=unit_fixed,
                    kcal=int(kcal),
                    timestamp=datetime.now().isoformat(),
                )
            )

            st.success(
                f"Toegevoegd: {p['label']} · {amount:g} {unit_fixed} ({int(kcal)} kcal)"
            )

# ============================================================
# BLOK 2.1b — Vrij kcal-item toevoegen
# ============================================================

st.subheader("Vrij kcal-item")

with st.form("free_kcal_form", clear_on_submit=True):

    free_name = st.text_input("Wat was het?")
    free_kcal = st.number_input(
        "Aantal kcal",
        min_value=0,
        step=5,
        value=0
    )

    submitted_free = st.form_submit_button("Toevoegen")

    if submitted_free:
        if not free_name.strip():
            st.warning("Geef een naam op.")
        elif free_kcal <= 0:
            st.warning("Geef een aantal kcal groter dan 0.")
        else:
            st.session_state["food_items"].append(
                FreeKcalItem(free_name.strip(), free_kcal)
            )
            st.success(f"Toegevoegd: {free_name} ({free_kcal} kcal)")
# ============================================================
# BLOK 2.2 — Beweging (CANON)
# ============================================================

from dataclasses import dataclass
from datetime import datetime

@dataclass
class ActivityItem:
    activity: str
    duration_min: int
    burned_kcal: int
    timestamp: str


st.subheader("Wat heb je daadwerkelijk bewogen?")

with st.form("activity_form", clear_on_submit=True):

    activity = st.selectbox(
        "Activiteit",
        list(ACTIVITY_KCAL_PER_MIN.keys())
    )

    duration = st.number_input(
        "Duur in minuten",
        min_value=0,
        step=5
    )

    submitted = st.form_submit_button("Activiteit toevoegen")

    if submitted and duration > 0:
        burned = duration * ACTIVITY_KCAL_PER_MIN[activity]

        st.session_state["activity_items"].append(
            ActivityItem(
                activity=activity,
                duration_min=duration,
                burned_kcal=burned,
                timestamp=datetime.now().isoformat()
            )
        )

        st.success(f"{activity} ({duration} min) toegevoegd: +{burned} kcal")
# ============================================================
# BLOK 3 — Realiteit & Dagbalans (CANON v2)
# ============================================================

# ----------------------------
# Geplande maaltijden (ontbijt / lunch / diner)
# ----------------------------
planned_consumed_kcal = 0

for mc in st.session_state.get("meal_consumptions", []):
    planned_consumed_kcal += mc.get("consumed_kcal", 0)


# ============================================================
# BLOK 3.x — Overzicht zelf ingevoerd eten (inklapbaar)
# ============================================================

with st.expander("Zelf ingevoerd eten (overzicht)", expanded=False):

    food_items = st.session_state.get("food_items", [])

    if not food_items:
        st.caption("Nog niets ingevoerd.")
    else:
        total = 0
        for fi in food_items:
            st.write(f"• {fi.product} — {fi.kcal} kcal")
            total += fi.kcal

        st.markdown("---")
        st.write(f"**Totaal:** {total} kcal")

# ----------------------------
# Beweging
# ----------------------------
st.subheader("Beweging")

activity_items = st.session_state.get("activity_items", [])

burned_kcal_total = 0

if not activity_items:
    st.caption("Nog geen beweging ingevoerd.")
else:
    for act in activity_items:
        st.write(
            f"• {act.activity} — {act.duration_min} min ({act.burned_kcal} kcal)"
        )
        burned_kcal_total += act.burned_kcal

    st.markdown("---")
    st.write(f"**Totaal verbrand:** {int(burned_kcal_total)} kcal")


# ----------------------------
# DAGBALANS — TOTAAL
# ----------------------------
st.subheader("Dagbalans")

# ============================================================
# A1 — Extra gegeten kcal (altijd veilig)
# ============================================================

extra_eaten_kcal = 0
for fi in st.session_state.get("food_items", []):
    extra_eaten_kcal += fi.kcal

# ============================================================
# A2 — Geplande & verbrande kcal (defensief)
# ============================================================

planned_kcal = planned_consumed_kcal if "planned_consumed_kcal" in locals() else 0
burned_kcal = burned_kcal_total if "burned_kcal_total" in locals() else 0

# ============================================================
# DAGBALANS — BEREKENING
# ============================================================

total_eaten_kcal = planned_kcal + extra_eaten_kcal
netto_kcal = total_eaten_kcal - burned_kcal

st.write(f"Maaltijden (ontbijt/lunch/diner): {int(planned_kcal)} kcal")
st.write(f"Extra gegeten: {int(extra_eaten_kcal)} kcal")
st.divider()
st.write(f"**Totaal gegeten:** {int(total_eaten_kcal)} kcal")
st.write(f"Beweging: −{int(burned_kcal)} kcal")
st.divider()
st.write(f"**Netto dagbalans:** {int(netto_kcal)} kcal")
# ============================================================
# BLOK 3.5 — Weekgeheugen begrenzen (reset bij nieuwe week)
# ============================================================

from datetime import date, timedelta

today = date.today()
current_week_start = today - timedelta(days=today.weekday())

if "week_start" not in st.session_state:
    st.session_state["week_start"] = current_week_start.isoformat()

if st.session_state["week_start"] != current_week_start.isoformat():
    # nieuwe week → reset weekcontext
    st.session_state["week_start"] = current_week_start.isoformat()


# ============================================================
# BLOK 3.4 — Weekimpact (eenvoudige optelsom)
# ============================================================

from datetime import date, timedelta

week_delta = 0
days_count = 0

today = date.today()
week_start = today - timedelta(days=today.weekday())  # maandag

for d in st.session_state.get("dagresultaten", []):
    d_date = date.fromisoformat(d["date"])
    if d_date >= week_start:
        week_delta += d.get("delta_corrected", 0)
        days_count += 1

st.subheader("Weekimpact")
st.write(f"Dagen meegeteld: {days_count}")
st.write(f"Totaal deze week: {week_delta:+} kcal")


# ============================================================
# BLOK 4a — Einde van de dag (CANON)
# ============================================================

st.divider()
st.subheader("Dag afronden")

if not st.session_state["day_closed"]:
    if st.button("🟣 Einde van de dag"):

        from datetime import date

        today = date.today().isoformat()

        # ----------------------------
        # Canon-totalen ophalen
        # ----------------------------

        # geplande maaltijden (ontbijt/lunch/diner)
        planned_consumed_kcal = 0
        for mc in st.session_state.get("meal_consumptions", []):
            planned_consumed_kcal += mc.get("consumed_kcal", 0)

        # extra ingevoerd eten
        extra_eaten_kcal = 0
        for fi in st.session_state.get("food_items", []):
            extra_eaten_kcal += fi.kcal

        # beweging
        burned_kcal_total = 0
        for act in st.session_state.get("activity_items", []):
            burned_kcal_total += act.burned_kcal

        # totaal
        total_eaten_kcal = planned_consumed_kcal + extra_eaten_kcal
        remaining_kcal = daily_budget - total_eaten_kcal
        delta_corrected = remaining_kcal + burned_kcal_total

        # ----------------------------
        # Dag-snapshot (weeklogica)
        # ----------------------------
        dag_snapshot = {
            "date": today,
            "day_type": st.session_state["day"].get("day_type", "onbekend"),
            "planned_meals_kcal": planned_consumed_kcal,
            "extra_eaten_kcal": extra_eaten_kcal,
            "total_eaten_kcal": total_eaten_kcal,
            "burned_kcal": burned_kcal_total,
            "remaining_kcal": remaining_kcal,
            "delta_corrected": delta_corrected,
        }

        bestaande = [
            d for d in st.session_state.get("dagresultaten", [])
            if d["date"] != today
        ]
        bestaande.append(dag_snapshot)
        st.session_state["dagresultaten"] = bestaande

        st.session_state["day_closed"] = True
        st.success("Dag afgesloten. Deze telt nu mee voor je week.")
# ============================================================
# BLOK 4 b — Opgeslagen dagresultaten
# ============================================================

st.subheader("Opgeslagen dagresultaten")

for d in st.session_state.get("dagresultaten", []):
    st.write(
        f"{d.get('date')} · "
        f"{d.get('day_type', '?')} · "
        f"maaltijden {d.get('planned_meals_kcal', 0)} · "
        f"gegeten {d.get('eaten_kcal', 0)} · "
        f"beweging {d.get('burned_kcal', 0)} · "
        f"resterend {d.get('remaining_kcal', 0)}"
    )