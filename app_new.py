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

# ============================================================
# HOOFDSTUK 1 — CANON SETTINGS (LEIDEND)
# ============================================================

# Richtwaarde uit startcontext
DEFAULT_DAILY_TARGET_KCAL = 2100

# Programma keuze
PROGRAMS = ["Blauw", "Paars"]

# Weegmoment
WEIGH_DAY = 2  # 0=ma, 1=di, 2=wo

# Activiteiten (kcal per minuut, grove schatting)
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
    from food_library_generated_v8_fixed import FOOD_LIBRARY
except Exception as e:
    FOOD_LIBRARY = {}
    raise RuntimeError(
        "FOOD_LIBRARY ontbreekt. Zet food_library_generated_v8_fixed.py naast app_new.py."
    ) from e

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
    unit = product_def["unit"]
    if unit == "gram":
        return int((product_def["kcal_per_100g"] / 100.0) * amount)
    if unit == "cl":
        ml = amount * 10.0
        return int((product_def["kcal_per_100ml"] / 100.0) * ml)
    if unit == "eetlepel":
        return int(product_def["kcal_per_tbsp"] * amount)
    if unit == "stuk":
        return int(product_def["kcal_per_piece"] * amount)
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

def coach_line(program: str, eaten: int, burned: int, net: int, target: int) -> str:
    # Coachend, direct, geen WW marketingtaal
    if eaten == 0 and burned == 0:
        return f"{program}: start rustig. Eiwit eerst, groente als volume. Vet en saus zijn een bewuste keuze."
    if net <= target:
        return f"{program}: netjes. Blijf bij eiwit en volume. Als je nog iets pakt, kies slim en houd vet onder controle."
    over = net - target
    # Sportcompensatie in kcal: +250 kcal -> ~30-40 min extra beweging (vuistregel)
    est_min = int(max(20, min(90, (over / 250.0) * 35)))
    return f"{program}: je zit erover (+{int(over)} kcal). Concreet: schrap 1 vetmoment of compenseer met ±{est_min} min extra beweging."

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
    program = st.selectbox("Programma", PROGRAMS, index=PROGRAMS.index(day_rec.get("program", "Paars")), disabled=day_closed)
with c2:
    target_kcal = st.number_input("Richtwaarde (kcal)", min_value=1200, max_value=3500, step=50, value=int(day_rec.get("target_kcal", DEFAULT_DAILY_TARGET_KCAL)), disabled=day_closed)

day_rec["program"] = program
day_rec["target_kcal"] = int(target_kcal)

st.markdown("---")

# ============================================================
# HOOFDSTUK 7 — HERO (TUSSENSTAND + INDICATIEVE PUNTEN)
# ============================================================

eaten_kcal = sum_food_kcal(day_rec)
burned_kcal = sum_activity_kcal(day_rec)
netto_kcal = int(eaten_kcal - burned_kcal)

# Indicatieve punten (ruwe, transparante schatting)
# 1 punt ≈ 60 kcal (geen officiële WW-formule)
estimated_points = max(0, int(round(netto_kcal / 60.0)))

st.markdown("### Tussenstand")

st.markdown(
    f"""
    <div style="padding:14px 0;">
        <div style="font-size:42px; font-weight:700;">
            {netto_kcal} kcal
        </div>
        <div style="font-size:16px; font-weight:500; margin-top:4px;">
            ≈ {estimated_points} punten (indicatief)
        </div>
        <div style="font-size:14px; opacity:0.7; margin-top:6px;">
            {eaten_kcal} gegeten · {burned_kcal} verbrand
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(
    coach_line(
        program=program,
        eaten=eaten_kcal,
        burned=burned_kcal,
        net=netto_kcal,
        target=int(target_kcal),
    )
)

# ============================================================
# HOOFDSTUK 8 — ACTIES (ETEN + EIGEN PRODUCT + BEWEGING) — FIXED UX
# ============================================================
# ------------------------------------------------------------
# 8.1 — Product uit FOOD_LIBRARY toevoegen (UNIT-PROOF)
# ------------------------------------------------------------

with st.expander("➕ Eten toevoegen", expanded=False):

    if day_closed:
        st.info("Deze dag is afgesloten. Nieuwe invoer is niet meer mogelijk.")

    food_keys = list(FOOD_LIBRARY.keys())
    food_labels = [FOOD_LIBRARY[k]["label"] for k in food_keys]

    selected_label = st.selectbox(
        "Product",
        food_labels,
        disabled=day_closed
    )

    selected_key = food_keys[food_labels.index(selected_label)]
    p = FOOD_LIBRARY[selected_key]
    unit = str(p.get("unit", "gram")).lower()

    st.caption(f"Eenheid: {unit}")

    # Default hoeveelheid op basis van standaardportie (als die bestaat)
    default_amount = 0.0
    if unit == "gram" and p.get("std_portion_g") is not None:
        default_amount = float(p["std_portion_g"])
    elif unit == "ml" and p.get("std_portion_ml") is not None:
        default_amount = float(p["std_portion_ml"])
    elif unit == "cl" and p.get("std_portion_cl") is not None:
        default_amount = float(p["std_portion_cl"])

    # UI input per unit
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
        # Als er toch iets exotisch in de library staat, vangen we dat netjes af
        amount = st.number_input(
            f"Hoeveelheid ({unit})",
            min_value=0.0,
            step=1.0,
            value=default_amount,
            disabled=day_closed
        )

    if st.button("Toevoegen", key="add_food", disabled=day_closed):

        if amount <= 0:
            st.warning("Vul een geldige hoeveelheid in.")
            st.stop()

        # Kcal berekening per unit
        if unit == "gram":
            kcal_per_100g = float(p.get("kcal_per_100g", 0))
            kcal = int(round((kcal_per_100g / 100.0) * amount))

        elif unit == "ml":
            kcal_per_100ml = float(p.get("kcal_per_100ml", 0))
            kcal = int(round((kcal_per_100ml / 100.0) * amount))

        elif unit == "cl":
            kcal_per_100ml = float(p.get("kcal_per_100ml", 0))
            ml = amount * 10.0
            kcal = int(round((kcal_per_100ml / 100.0) * ml))

        else:
            kcal = 0

        day_rec["food_items"].append({
            "id": str(uuid.uuid4()),
            "product": p["label"],
            "amount": float(amount),
            "unit": unit,
            "kcal": int(kcal),
            "timestamp": datetime.now().isoformat(),
            "zero_paars": bool(p.get("zero_paars", False)),
            "zero_blauw": bool(p.get("zero_blauw", False)),
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

def generate_recipe_item(meal_type: str, program: str) -> dict:
    """
    Stabiele prompt-based generator.
    Output is altijd één dict in exact hetzelfde formaat als food_items.

    BELANGRIJK:
    - Nu nog zonder externe API-call (om je kern 1.0 niet te slopen).
    - In Stap 2 vervangen we de "fake_model_call" door jouw echte prompt-call.
    """

    # --- Prompt (leidend op blauw/paars, coachend, kcal spoor)
    prompt = f"""
Je bent Peet Paars. Coachend en direct. Geen WW marketingtaal.
Programma: {program}.
Maaltijd: {meal_type}.

Maak 1 recept dat past bij {program}.
Eiwit eerst. Groente als volume. Vet/saus is een bewuste keuze.
ZeroPoint foods zijn vrij inzetbaar maar niet stapelen alsof het onbeperkt is.

Output ALLEEN als JSON met exact deze keys:
{{
  "title": "string",
  "kcal": integer,
  "ingredients": ["string", "..."],
  "note": "string (1 zin coachend)"
}}

Regels:
- kcal tussen 450 en 850
- ingrediënten max 10 regels
- geen vage termen, concreet (bijv. 'kipfilet 150g', 'broccoli 300g')
"""

    # --- Tijdelijke veilige call: deterministische fallback
    # In stap 2 vervangen we dit door een echte model-call.
    def fake_model_call(_prompt: str) -> dict:
        if meal_type == "Lunch":
            if program == "Paars":
                return {
                    "title": "Bowl: kipfilet, bonen, groenten, yoghurt",
                    "kcal": 560,
                    "ingredients": [
                        "kipfilet 150 g",
                        "kidneybonen 150 g",
                        "komkommer 150 g",
                        "tomaat 150 g",
                        "paprika 100 g",
                        "magere yoghurt 150 g",
                        "citroen, zout, peper",
                    ],
                    "note": "Eiwit en volume staan goed. Houd olie en kaas uit de buurt vandaag.",
                }
            return {
                "title": "Salade: tonijn, ei, veel groente, yoghurt dressing",
                "kcal": 520,
                "ingredients": [
                    "tonijn op water 1 blik",
                    "ei 2 stuks",
                    "sla 150 g",
                    "komkommer 150 g",
                    "tomaat 150 g",
                    "magere yoghurt 150 g",
                    "mosterd 1 tl",
                ],
                "note": "Netjes. Als je nog honger hebt, pak extra groente of kwark, geen snack.",
            }

        # Diner
        if program == "Paars":
            return {
                "title": "Ovenschaal: zalm, broccoli, krieltjes, citroen",
                "kcal": 780,
                "ingredients": [
                    "zalm 180 g",
                    "broccoli 350 g",
                    "krieltjes 250 g",
                    "citroen 1",
                    "knoflook 1 teen",
                    "olijfolie 1 el",
                ],
                "note": "Prima diner. Olie is je hefboom, hou het bij 1 eetlepel.",
            }
        return {
            "title": "Roerbak: kip, wokgroente, bloemkoolrijst, sojasaus",
            "kcal": 650,
            "ingredients": [
                "kipfilet 180 g",
                "wokgroenten 400 g",
                "bloemkoolrijst 300 g",
                "sojasaus 1 el",
                "sesamolie 1 tl",
            ],
            "note": "Sterk. Volume en eiwit staan. Vet hou je klein, dan win je de dag.",
        }

    model_out = None

    # --- Probeer echte OpenAI call ---
    if OPENAI_AVAILABLE:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                client = OpenAI(api_key=api_key)

                response = client.responses.create(
                    model="gpt-4.1-mini",
                    input=prompt,
                )

                raw = response.output_text
                import json
                model_out = json.loads(raw)

            except Exception:
                model_out = None

    # --- Fallback als API niet beschikbaar of fout ---
    if not model_out:
        model_out = fake_model_call(prompt)


    # --- Converteer naar food_item structuur
    title = str(model_out.get("title", f"{meal_type} recept"))
    kcal = int(model_out.get("kcal", 650))
    ingredients = model_out.get("ingredients", [])
    note = str(model_out.get("note", ""))

    return {
        "id": str(uuid.uuid4()),
        "product": f"{meal_type} recept: {title}",
        "amount": 1,
        "unit": "portie",
        "kcal": kcal,
        "timestamp": datetime.now().isoformat(),
        "meta": {
            "source": "prompt_generator_stub",
            "program": program,
            "meal_type": meal_type,
            "note": note,
            "ingredients": ingredients,
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
        st.session_state["pending_recipe"] = generate_recipe_item("Lunch", program)
        st.rerun()

with c2:
    if st.button("🟣 Genereer diner", disabled=day_closed):
        st.session_state["pending_recipe"] = generate_recipe_item("Diner", program)
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