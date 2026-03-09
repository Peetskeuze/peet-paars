# ============================================================
# P E E T   P A A R S
# app_new.py — STABIELE KERN 1.0
# ============================================================

import streamlit as st
import uuid
from datetime import datetime, date, timedelta

# ============================================================
# OPENAI (OPTIONEEL — VEILIG)
# ============================================================

try:
    from openai import OpenAI
    import os
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# ============================================================
# HOOFDSTUK 0 — PAGE CONFIG (MOET EERST)
# ============================================================

st.set_page_config(page_title="Peet Paars", layout="centered")
st.title("Peet Paars")
st.write("PEET TEST BUILD 2")

st.markdown("""
<style>

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

h1, h2, h3 {
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}

.stMetric {
    padding-top: 0.3rem;
    padding-bottom: 0.3rem;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# HOOFDSTUK 1 — CANON SETTINGS (LEIDEND)
# ============================================================

# ------------------------------------------------------------
# Dagdoel energie (basisinstelling)
# ------------------------------------------------------------

DEFAULT_DAILY_TARGET_KCAL = 1800


# ------------------------------------------------------------
# Weegmoment (0 = maandag)
# ------------------------------------------------------------

WEIGH_DAY = 2   # woensdag


# ------------------------------------------------------------
# Activiteiten energieverbruik
# kcal per minuut (ruwe richtwaarden)
# ------------------------------------------------------------

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
# HOOFDSTUK 1B — FOOD_LIBRARY (AUTO-GENERATED v8, LEIDEND)
# ============================================================

try:
    from food_library_generated_v8_2_fixed import FOOD_LIBRARY
except Exception as e:
    FOOD_LIBRARY = {}
    raise RuntimeError(
        "FOOD_LIBRARY ontbreekt. Zet food_library_generated_v8_2_fixed.py naast app_new.py."
    ) from e


# ============================================================
# FOOD ALIAS INDEX (SNELLE PRODUCT ZOEKER)
# ============================================================

FOOD_ALIAS_INDEX = {}

for key, prod in FOOD_LIBRARY.items():

    # label indexeren
    label = prod.get("label", "").lower().strip()

    if label:
        FOOD_ALIAS_INDEX[label] = key

    # alias indexeren
    for alias in prod.get("alias", []):
        alias_clean = alias.lower().strip()
        FOOD_ALIAS_INDEX[alias_clean] = key


# ------------------------------------------------------------
# Product zoeken op tekst (label of alias)
# ------------------------------------------------------------

def find_product_by_text(text: str):

    if not text:
        return None

    text_clean = text.lower().strip()

    # 1️⃣ exacte match
    key = FOOD_ALIAS_INDEX.get(text_clean)
    if key:
        return key

    # 2️⃣ gedeeltelijke match (bv: "melk" → "volle melk")
    for alias, k in FOOD_ALIAS_INDEX.items():
        if text_clean in alias:
            return k

    return None

# ============================================================
# HOOFDSTUK 2 — HELPERS (PURE FUNCTIES)
# ============================================================

NL_DAY_FULL = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
NL_MONTH_FULL = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december"
]

def format_day_title_nl(selected_dt: date, today_dt: date) -> str:
    delta = (selected_dt - today_dt).days
    if delta == 0:
        return "Vandaag"
    if delta == -1:
        return "Gisteren"
    if delta == 1:
        return "Morgen"
    day_name = NL_DAY_FULL[selected_dt.weekday()]
    month_name = NL_MONTH_FULL[selected_dt.month - 1]
    return f"{day_name} {selected_dt.day} {month_name}"

def calc_food_kcal(product_def: dict, amount: float) -> int:

    unit = product_def.get("unit")

    if unit == "gram":
        kcal100 = product_def.get("kcal_per_100g", 0)
        return int((kcal100 / 100.0) * amount)

    if unit == "ml":
        kcal100 = product_def.get("kcal_per_100ml", 0)
        return int((kcal100 / 100.0) * amount)

    if unit == "cl":
        kcal100 = product_def.get("kcal_per_100ml", 0)
        ml = amount * 10
        return int((kcal100 / 100.0) * ml)

    if unit == "eetlepel":
        return int(product_def.get("kcal_per_tbsp", 0) * amount)

    if unit == "stuk":
        return int(product_def.get("kcal_per_piece", 0) * amount)

    return 0

def ensure_day(iso_date: str):
    if "days" not in st.session_state:
        st.session_state["days"] = {}
    if iso_date not in st.session_state["days"]:
        st.session_state["days"][iso_date] = {
            "food_items": [],
            "activity_items": [],
            "closed": False,
            "program": "Paars",
            "target_kcal": DEFAULT_DAILY_TARGET_KCAL,
        }
    return st.session_state["days"][iso_date]

def sum_food_kcal(day_rec: dict) -> int:
    return int(sum(item.get("kcal", 0) for item in day_rec.get("food_items", [])))

def sum_activity_kcal(day_rec: dict) -> int:
    return int(sum(item.get("kcal", 0) for item in day_rec.get("activity_items", [])))

def coach_line(eaten, burned, net, target):

    if eaten == 0 and burned == 0:
        return "Start rustig. Eiwit eerst, groente als volume."

    if net <= target:
        return "Je zit onder je dagdoel. Prima koers."

    over = net - target
    return f"Je zit {over} kcal boven je dagdoel. Compenseer met beweging of eet lichter."

def make_recipe_stub(meal_type: str, program: str) -> dict:
    # STABIEL: geen LLM. Dit is een tijdelijke, gecontroleerde generator.
    # Later vervangen we dit blok door jouw prompt gebaseerde call.
    if meal_type == "Lunch":
        title = "Bowl: kip, rauwkost, yoghurt dressing"
        kcal = 520
        note = f"{program}: eiwit en volume. Dressing bewust."
    else:
        title = "Traybake: zalm, broccoli, krieltjes (Paars) of extra groente (Blauw)"
        kcal = 720 if program == "Paars" else 640
        note = f"{program}: vet is de knop die je stuurt. Hou olie strak."
    return {
        "id": str(uuid.uuid4()),
        "product": f"{meal_type} recept: {title}",
        "amount": 1,
        "unit": "portie",
        "kcal": int(kcal),
        "timestamp": datetime.now().isoformat(),
        "meta": {"source": "recipe_stub", "program": program, "meal_type": meal_type, "note": note},
    }

# ------------------------------------------------------------
# Slimme kcal suggestie voor vrije invoer
# ------------------------------------------------------------

SMART_KCAL_MAP = {
    # vlees / vis
    "rosbief": 110,
    "biefstuk": 150,
    "kip": 110,
    "kipfilet": 110,
    "zalm": 200,
    "tonijn": 130,
    "gamba": 100,
    "garnalen": 100,

    # zuivel
    "kaas": 350,
    "room": 300,
    "yoghurt": 60,
    "kwark": 60,

    # vet
    "olie": 900,
    "olijfolie": 900,
    "boter": 720,
    "mayonaise": 700,

    # zoet
    "chocolade": 550,
    "koek": 480,
    "cake": 400,
}

def suggest_kcal_per_100(product_name: str) -> int:
    name = product_name.lower()
    for key, kcal in SMART_KCAL_MAP.items():
        if key in name:
            return kcal
    return 0
# ============================================================
# HOOFDSTUK 3 — SESSION STATE INIT (WEEK + SELECTED DAY)
# ============================================================

if "weight_log" not in st.session_state:
    st.session_state["weight_log"] = []

if "last_weight_prompt_week" not in st.session_state:
    st.session_state["last_weight_prompt_week"] = None

if "show_weight_prompt" not in st.session_state:
    st.session_state["show_weight_prompt"] = False

if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = date.today().isoformat()

# ============================================================
# HOOFDSTUK 4 — WEIGHT PROMPT (1x PER WEEK OP WO)
# ============================================================

today_dt = date.today()
current_week = today_dt.isocalendar().week
today_weekday = today_dt.weekday()

if (
    today_weekday == WEIGH_DAY
    and st.session_state["last_weight_prompt_week"] != current_week
    and not st.session_state["show_weight_prompt"]
):
    st.session_state["show_weight_prompt"] = True

if st.session_state["show_weight_prompt"]:
    st.markdown("---")
    st.subheader("Wekelijks weegmoment")
    st.write("Als je wilt, kun je je gewicht vastleggen. Dit is voor trend, niet voor oordeel.")

    weight = st.number_input("Gewicht (kg)", min_value=30.0, max_value=250.0, step=0.1, key="weekly_weight_input")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Opslaan", key="save_weight"):
            st.session_state["weight_log"].append({
                "date": today_dt.isoformat(),
                "week": int(current_week),
                "weight": float(weight),
            })
            st.session_state["last_weight_prompt_week"] = int(current_week)
            st.session_state["show_weight_prompt"] = False
            st.rerun()
    with c2:
        if st.button("Overslaan", key="skip_weight"):
            st.session_state["last_weight_prompt_week"] = int(current_week)
            st.session_state["show_weight_prompt"] = False
            st.rerun()

    st.markdown("---")

# ============================================================
# HOOFDSTUK 5 — DAGSELECTIE + DAYSTORE LOAD
# ============================================================

selected_dt = st.date_input(
    "Dag",
    value=date.fromisoformat(st.session_state["selected_date"]),
    max_value=today_dt,
    key="selected_dt",
    label_visibility="collapsed",
)

st.session_state["selected_date"] = selected_dt.isoformat()
day_rec = ensure_day(st.session_state["selected_date"])
day_closed = bool(day_rec.get("closed", False))

# ============================================================
# HOOFDSTUK 6 — CONTEXT STRIP + PROGRAMMA
# ============================================================

title = format_day_title_nl(selected_dt, today_dt)
sub = f"{NL_DAY_FULL[selected_dt.weekday()]} {selected_dt.day} {NL_MONTH_FULL[selected_dt.month - 1]}"

st.markdown(f"### {title}")
st.caption(sub)

c1, c2 = st.columns([1, 1])

with c1:
    target_kcal = st.number_input(
        "Dagdoel kcal",
        min_value=1200,
        max_value=3500,
        step=50,
        value=int(day_rec.get("target_kcal", DEFAULT_DAILY_TARGET_KCAL)),
        disabled=day_closed
    )

day_rec["target_kcal"] = int(target_kcal)

program = day_rec.get("program", "Paars")

# ============================================================
# HOOFDSTUK 7 — DASHBOARD (COMPACT)
# ============================================================

eaten_kcal = sum_food_kcal(day_rec)
burned_kcal = sum_activity_kcal(day_rec)
netto_kcal = int(eaten_kcal - burned_kcal)

balance = netto_kcal - int(target_kcal)

# ------------------------------------------------------------
# Resterend kcal budget voor AI
# ------------------------------------------------------------
# ------------------------------------------------------------
# Resterend kcal budget voor AI
# ------------------------------------------------------------

remaining_kcal = int(target_kcal) - int(eaten_kcal) + int(burned_kcal)

if remaining_kcal < 0:
    remaining_kcal = 0

#---------------------------------------------------------------
# Dagdashboard
#---------------------------------------------------------------

st.markdown("### Dagdashboard")

st.metric("Netto kcal", int(netto_kcal))

col1, col2 = st.columns(2)

with col1:
    st.metric("Gegeten", int(eaten_kcal))

with col2:
    st.metric("Bewogen", int(burned_kcal))

st.metric("Dagdoel", int(target_kcal))
# ------------------------------------------------------------
# Coach feedback
# ------------------------------------------------------------

if balance <= 0:
    st.success(f"{balance:+} kcal t.o.v. dagdoel")
else:
    st.warning(f"{balance:+} kcal boven dagdoel")

st.caption(
    coach_line(
        eaten=eaten_kcal,
        burned=burned_kcal,
        net=netto_kcal,
        target=int(target_kcal),
    )
)

st.caption(f"Dagdoel: {target_kcal} kcal")

# ============================================================
# HOOFDSTUK 7b — WEEK KOERS
# ============================================================

today_dt = date.today()
week_start = today_dt - timedelta(days=today_dt.weekday())

week_balance = 0
days_counted = 0

for iso_day, d in st.session_state.get("days", {}).items():

    d_date = date.fromisoformat(iso_day)

    if d_date >= week_start and d_date <= today_dt:

        eaten = sum_food_kcal(d)
        burned = sum_activity_kcal(d)

        target = int(d.get("target_kcal", DEFAULT_DAILY_TARGET_KCAL))

        net = eaten - burned

        week_balance += net - target
        days_counted += 1


st.markdown("---")
st.markdown("### Week koers")

if days_counted == 0:

    st.caption("Nog geen dagen geregistreerd deze week.")

else:

    if week_balance <= 0:
        st.success(f"{week_balance:+} kcal deze week")
        st.caption("Je week ligt op koers.")

    else:
        st.warning(f"{week_balance:+} kcal deze week")
        st.caption("Een paar lichtere keuzes brengen je weer op koers.")


# ============================================================
# HOOFDSTUK 8 — ACTIES (ETEN + EIGEN PRODUCT + BEWEGING)
# ============================================================
# ------------------------------------------------------------
# 8.0 — SNELLE INVOER (MOBILE FAST ENTRY)
# ------------------------------------------------------------

    st.markdown("### ⚡ Snelle invoer")

    quick_text = st.text_input(
        "Typ bijvoorbeeld: 150 kipfilet",
        key="quick_food_input",
        disabled=day_closed
    )

    if st.button("Toevoegen via tekst", disabled=day_closed):

        if not quick_text:
            st.warning("Voer iets in.")
        
        else:

            parts = quick_text.split(" ", 1)

            if len(parts) != 2:
                st.warning("Gebruik formaat: hoeveelheid product")
            
            else:

                try:
                    amount = float(parts[0])
                except:
                    st.warning("Hoeveelheid moet een getal zijn.")
                    amount = None

                if amount is not None:

                    product_text = parts[1].strip()

                    key = find_product_by_text(product_text)

                    if not key:
                        st.warning("Product niet gevonden. Probeer bv: kipfilet, olie, yoghurt.")
                    
                    else:

                        p = FOOD_LIBRARY[key]

                        kcal = calc_food_kcal(p, amount)

                        day_rec["food_items"].append({
                            "id": str(uuid.uuid4()),
                            "product": p["label"],
                            "amount": amount,
                            "unit": p.get("unit", "gram"),
                            "kcal": kcal,
                            "timestamp": datetime.now().isoformat(),
                        })

                        st.success(f"{p['label']} toegevoegd ({kcal} kcal)")
                        st.rerun()
# ------------------------------------------------------------
# 8.1 — Product uit FOOD_LIBRARY toevoegen (UNIT-PROOF)
# ------------------------------------------------------------

with st.expander("➕ Eten toevoegen", expanded=False):

    if day_closed:
        st.info("Deze dag is afgesloten. Nieuwe invoer is niet meer mogelijk.")

# ------------------------------------------------------------
# Product selectie
# ------------------------------------------------------------

    food_options = {v["label"]: k for k, v in FOOD_LIBRARY.items()}

    if not food_options:
        st.warning("Geen ingrediënten gevonden.")
        st.stop()

    selected_label = st.selectbox(
        "Product",
        sorted(food_options.keys()),
        key="food_select",
        disabled=day_closed
    )

    selected_key = food_options[selected_label]
    p = FOOD_LIBRARY[selected_key]

    unit = str(p.get("unit", "gram")).lower()

# ------------------------------------------------------------
# Snelle porties voor drank
# ------------------------------------------------------------

    quick_amount = None

    if unit == "ml":

        quick_cols = st.columns(3)

        with quick_cols[0]:
            if st.button("🍺 250 ml", disabled=day_closed):
                quick_amount = 250.0

        with quick_cols[1]:
            if st.button("🍺 330 ml", disabled=day_closed):
                quick_amount = 330.0

        with quick_cols[2]:
            if st.button("🍺 500 ml", disabled=day_closed):
                quick_amount = 500.0

        st.caption("Snelle porties voor (drank)")

    # ------------------------------------------------------------
    # Default hoeveelheid
    # ------------------------------------------------------------

    default_amount = 0.0

    if unit == "gram" and p.get("std_portion_g"):
        default_amount = float(p["std_portion_g"])

    elif unit == "ml" and p.get("std_portion_ml"):
        default_amount = float(p["std_portion_ml"])

    elif unit == "cl" and p.get("std_portion_cl"):
        default_amount = float(p["std_portion_cl"])

    # ------------------------------------------------------------
    # Hoeveelheid invoer
    # ------------------------------------------------------------

    if unit == "gram":

        amount = st.number_input(
            "Hoeveelheid (gram)",
            min_value=0.0,
            step=5.0,
            value=default_amount,
            disabled=day_closed
        )

    elif unit == "ml":

        amount = st.number_input(
            "Hoeveelheid (ml)",
            min_value=0.0,
            step=10.0,
            value=default_amount,
            disabled=day_closed
        )

    elif unit == "cl":

        amount = st.number_input(
            "Hoeveelheid (cl)",
            min_value=0.0,
            step=1.0,
            value=default_amount,
            disabled=day_closed
        )

    else:

        amount = st.number_input(
            f"Hoeveelheid ({unit})",
            min_value=0.0,
            step=1.0,
            value=default_amount,
            disabled=day_closed
        )

    # ------------------------------------------------------------
    # Snelle drankknoppen overschrijven hoeveelheid
    # ------------------------------------------------------------

    if quick_amount is not None:
        amount = quick_amount

    # ------------------------------------------------------------
    # Toevoegen
    # ------------------------------------------------------------

    if st.button("Toevoegen", key="add_food", disabled=day_closed):

        if amount <= 0:
            st.warning("Vul een geldige hoeveelheid in.")
            st.stop()

        kcal = calc_food_kcal(p, amount)

        day_rec["food_items"].append({
            "id": str(uuid.uuid4()),
            "product": p["label"],
            "amount": float(amount),
            "unit": unit,
            "kcal": int(kcal),
            "timestamp": datetime.now().isoformat(),
        })

        st.success(f"{p['label']} toegevoegd ({int(kcal)} kcal)")
        st.rerun()
# ------------------------------------------------------------
# 8.3 — Beweging toevoegen
# ------------------------------------------------------------

with st.expander("➕ Beweging toevoegen", expanded=False):

    if day_closed:
        st.info("Deze dag is afgesloten. Nieuwe invoer is niet meer mogelijk.")

    activity = st.selectbox(
        "Activiteit",
        list(ACTIVITY_KCAL_PER_MIN.keys()),
        disabled=day_closed
    )

    duration = st.number_input(
        "Duur (minuten)",
        min_value=0,
        step=5,
        disabled=day_closed
    )

    if st.button("Toevoegen", key="add_activity", disabled=day_closed):

        if duration <= 0:
            st.warning("Vul een geldige duur in.")
        else:
            kcal = int(duration) * int(ACTIVITY_KCAL_PER_MIN[activity])

            day_rec["activity_items"].append({
                "id": str(uuid.uuid4()),
                "activity": str(activity),
                "duration_min": int(duration),
                "kcal": int(kcal),
                "timestamp": datetime.now().isoformat(),
            })

            st.success(f"{activity.capitalize()} toegevoegd ({int(kcal)} kcal)")
            st.rerun()
# ============================================================
# HOOFDSTUK 8b — RECEPT GENERATOR (PROMPT-BASED, STABIEL)
# ============================================================

def generate_recipe_item(meal_type: str, program: str, remaining_kcal: int) -> dict:

    # ---------------------------------------------------------
    # kcal bandbreedte
    # ---------------------------------------------------------

    if meal_type == "Lunch":
        kcal_min = 450
        kcal_max = 650
    else:
        kcal_min = 600
        kcal_max = 850

    # ---------------------------------------------------------
    # PROMPT
    # ---------------------------------------------------------

    prompt = f"""
Je bent Peet Paars.

Je denkt als een chef én voedingscoach.

Je taak is een praktische maaltijd te bedenken
voor een normale thuiskeuken.

MAALTIJD
{meal_type}

PROGRAMMA
{program}

DAGBALANS

Dagdoel kcal: {target_kcal}
Gegeten kcal: {eaten_kcal}
Bewogen kcal: {burned_kcal}
Resterend kcal budget: {remaining_kcal}

STRATEGIE VAN PEET

- eiwit staat centraal
- groente zorgt voor volume
- vet en saus zijn de stuurknoppen
- maximaal 10 ingrediënten
- geschikt voor een doordeweekse keuken

CALORIE DOEL

tussen {kcal_min} en {kcal_max} kcal
maar probeer binnen het resterende kcal budget te blijven.

OUTPUT

Geef alleen JSON in dit formaat:

{{
"title": "naam van het gerecht",
"kcal": integer,
"ingredients": [
"ingrediënt hoeveelheid",
"ingrediënt hoeveelheid"
],
"instructions": [
"korte kookstap",
"korte kookstap"
],
"chef_tip": "korte tip van Peet"
}}
"""

    # ---------------------------------------------------------
    # fallback model
    # ---------------------------------------------------------

    def fake_model_call(_prompt: str) -> dict:

        if meal_type == "Lunch":
            return {
                "title": "Bowl met kipfilet, bonen en yoghurt dressing",
                "kcal": 560,
                "ingredients": [
                    "kipfilet 150 g",
                    "kidneybonen 150 g",
                    "paprika 100 g",
                    "komkommer 100 g",
                    "tomaat 150 g",
                    "magere yoghurt 150 g"
                ],
                "instructions": [
                    "bak de kipfilet goudbruin",
                    "snij de groente grof",
                    "meng yoghurt met citroen en peper",
                    "combineer alles in een kom"
                ],
                "chef_tip": "Gebruik yoghurt in plaats van olie voor een lichtere dressing."
            }

        return {
            "title": "Zalm met broccoli en krieltjes uit de oven",
            "kcal": 720,
            "ingredients": [
                "zalmfilet 180 g",
                "broccoli 350 g",
                "krieltjes 250 g",
                "citroen 1",
                "olijfolie 1 el"
            ],
            "instructions": [
                "verwarm oven op 200 graden",
                "snij broccoli en halveer krieltjes",
                "leg alles op een bakplaat",
                "bak 20 minuten in de oven"
            ],
            "chef_tip": "Hou olie bij één eetlepel. Dat is de belangrijkste kcal knop."
        }

    model_out = None


# ---------------------------------------------------------
# echte OpenAI call
# ---------------------------------------------------------

    model_out = None

    try:

        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )

        raw = getattr(response, "output_text", None)

        import json
        import re

        if raw:

            # markdown codeblokken verwijderen
            cleaned = raw.replace("```json", "").replace("```", "").strip()

            # JSON object zoeken
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)

            if match:

                try:
                    model_out = json.loads(match.group())

                except Exception:
                    st.error("AI gaf JSON terug maar die kon niet worden gelezen.")
                    st.write(cleaned)
                    st.stop()

            else:
                st.error("AI antwoord bevatte geen JSON-object.")
                st.write(cleaned)
                st.stop()

        else:
            st.error("AI gaf geen output_text terug.")
            st.stop()

    except Exception as e:
        st.error(f"OpenAI fout: {e}")
        st.stop()

    # ---------------------------------------------------------
    # GEEN fallback tijdens debug
    # ---------------------------------------------------------

    if not model_out:
        st.error("AI leverde geen bruikbaar resultaat op")
        st.stop()

    title = str(model_out.get("title", f"{meal_type} recept"))
    kcal = int(model_out.get("kcal", 650))
    ingredients = model_out.get("ingredients", [])
    instructions = model_out.get("instructions", [])
    chef_tip = str(model_out.get("chef_tip", ""))

    return {
        "id": str(uuid.uuid4()),
        "product": f"{meal_type} recept: {title}",
        "amount": 1,
        "unit": "portie",
        "kcal": kcal,
        "timestamp": datetime.now().isoformat(),
        "meta": {
            "source": "peet_prompt",
            "program": program,
            "meal_type": meal_type,
            "ingredients": ingredients,
            "instructions": instructions,
            "note": chef_tip,
        },
    }
# ============================================================
# HOOFDSTUK 9 — RECEPT VOORSTEL (BEWUST TOEVOEGEN)
# ============================================================

# Session state voor tijdelijk recept
if "pending_recipe" not in st.session_state:
    st.session_state["pending_recipe"] = None

st.markdown("---")
st.subheader("Recept voorstel")

c1, c2 = st.columns(2)

with c1:
    if st.button("🟣 Genereer lunch", disabled=day_closed):
        st.session_state["pending_recipe"] = generate_recipe_item("Lunch", program, remaining_kcal)
        st.rerun()

with c2:
    if st.button("🟣 Genereer diner", disabled=day_closed):
        st.session_state["pending_recipe"] = generate_recipe_item("Diner", program, remaining_kcal)
        st.rerun()

pending = st.session_state.get("pending_recipe")

if pending:

    st.markdown("---")
    st.write(f"**{pending['product']}**")
    st.write(f"{pending['kcal']} kcal")

    meta = pending.get("meta", {})
    ingredients = meta.get("ingredients", [])
    note = meta.get("note", "")

    if ingredients:
        with st.expander("Ingrediënten"):
            for ing in ingredients:
                st.write(f"• {ing}")

    if note:
        st.caption(note)

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("✅ Voer op als gegeten", disabled=day_closed):
            day_rec["food_items"].append(pending)
            st.session_state["pending_recipe"] = None
            st.success("Recept toegevoegd aan je dag.")
            st.rerun()

    with col_b:
        if st.button("❌ Verwerp", disabled=day_closed):
            st.session_state["pending_recipe"] = None
            st.rerun()

# ============================================================
# HOOFDSTUK 10 — OVERZICHT (ETEN + BEWEGING) MET VERWIJDEREN
# ============================================================

st.markdown("---")
st.subheader("Eten vandaag")

food_items = day_rec.get("food_items", [])
if not food_items:
    st.caption("Nog niets ingevoerd.")
else:
    total_food = 0
    for idx, item in enumerate(food_items):
        cols = st.columns([8, 2])
        with cols[0]:
            st.write(f"• {item['product']}  |  {item['amount']} {item['unit']}  |  {item['kcal']} kcal")
            meta = item.get("meta", {})
            if meta and isinstance(meta, dict) and meta.get("note"):
                st.caption(str(meta["note"]))
        with cols[1]:
            if st.button("Verwijder", key=f"del_food_{item['id']}", disabled=day_closed):
                day_rec["food_items"] = [x for x in day_rec["food_items"] if x.get("id") != item.get("id")]
                st.rerun()
        total_food += int(item.get("kcal", 0))

    st.divider()
    st.write(f"**Totaal gegeten: {int(total_food)} kcal**")

st.markdown("---")
st.subheader("Beweging vandaag")

activity_items = day_rec.get("activity_items", [])
if not activity_items:
    st.caption("Nog geen beweging ingevoerd.")
else:
    total_act = 0
    for item in activity_items:
        cols = st.columns([8, 2])
        with cols[0]:
            st.write(f"• {item['activity']}  |  {item['duration_min']} min  |  {item['kcal']} kcal")
        with cols[1]:
            if st.button("Verwijder", key=f"del_act_{item['id']}", disabled=day_closed):
                day_rec["activity_items"] = [x for x in day_rec["activity_items"] if x.get("id") != item.get("id")]
                st.rerun()
        total_act += int(item.get("kcal", 0))

    st.divider()
    st.write(f"**Totaal verbrand: {int(total_act)} kcal**")

# ============================================================
# HOOFDSTUK 11 — DAG AFRONDEN
# ============================================================

st.markdown("---")
st.subheader("Dag afronden")

if not day_closed:
    if st.button("🟣 Einde van de dag"):
        day_rec["closed"] = True
        st.success("Dag vastgezet.")
        st.rerun()
else:
    st.info("Deze dag is afgesloten. Nieuwe invoer is uitgeschakeld.")

# ============================================================
# HOOFDSTUK 12 — VERLOOP (GEWICHT)
# ============================================================

if len(st.session_state.get("weight_log", [])) >= 1:
    st.markdown("---")
    st.subheader("Verloop")
    st.caption("Gewicht verandert traag. Dit laat het verloop per week zien.")

    weight_data = sorted(st.session_state["weight_log"], key=lambda x: x["date"])
    dates = [w["date"] for w in weight_data]
    weights = [w["weight"] for w in weight_data]

    st.line_chart({"Gewicht (kg)": weights}, x=dates)