# ============================================================
# P E E T   P A A R S
# app_new.py — STABIELE KERN 1.0
# ============================================================

import streamlit as st
import uuid
import pandas as pd
import json


from core.day_analysis import analyze_day
from core.coach import coach_advice
from datetime import datetime, date, timedelta
from pathlib import Path
from core.nutrition import analyze_nutrition
from core.hunger import predict_hunger
from core.meal_timing import hours_since_last_meal
from core.product_db import search_products, get_product, load_products, add_product

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
USER_WEIGHT_KG = 110

# ------------------------------------------------------------
# Activiteiten energieverbruik
# kcal per minuut (ruwe richtwaarden)
# ------------------------------------------------------------

ACTIVITY_MET = {
    "wandelen": 3.5,
    "fietsen rustig": 6,
    "fietsen tempo": 8,
    "wielrennen": 10,
    "spinnen": 9,
    "krachttraining": 5,
    "zwemmen": 8,
}


# ============================================================
# HOOFDSTUK 1B — FOOD_LIBRARY (AUTO-GENERATED v8, LEIDEND)
# ============================================================

# ============================================================
# HOOFDSTUK 1B — PRODUCT DATABASE (LEIDEND)
# ============================================================

from core.product_db import load_products

try:
    PRODUCTS = load_products()

except Exception as e:
    PRODUCTS = []
    raise RuntimeError(
        "products.json ontbreekt of kan niet geladen worden."
    ) from e
# ============================================================
# FOOD ALIAS INDEX (SNELLE PRODUCT ZOEKER)
# ============================================================

FOOD_ALIAS_INDEX = {}

from core.product_db import load_products

products = load_products()

for prod in products:

    # label indexeren
    label = prod.get("label", "").lower().strip()

    if label:
        FOOD_ALIAS_INDEX[label] = key

    # alias indexeren
    for alias in prod.get("alias", []):
        alias_clean = alias.lower().strip()
        FOOD_ALIAS_INDEX[alias_clean] = prod["id"]


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
    save_data()
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
# Huidig gewicht ophalen uit weight_log
# ------------------------------------------------------------

def get_current_weight():

    log = st.session_state.get("weight_log", [])

    if not log:
        return 100  # fallback gewicht

    latest = sorted(log, key=lambda x: x["date"])[-1]

    return float(latest["weight"])

# ============================================================
# DATA OPSLAG (JSON)
# ============================================================

DATA_FILE = Path("peet_data.json")


def load_data():

    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

    return {}


def save_data():

    try:
        with open(DATA_FILE, "w") as f:
            json.dump(st.session_state.get("days", {}), f)

    except:
        pass
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

if "days" not in st.session_state:
    st.session_state["days"] = load_data()

# ============================================================
# 3.1 DATA OPSLAG (AUTOSAVE JSON)
# ============================================================

import json
from pathlib import Path

DATA_FILE = Path("peet_data.json")

def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(st.session_state.get("days", {}), f)
    except:
        pass

# bij start laden
if "days" not in st.session_state:
    st.session_state["days"] = load_data()

# ============================================================
# DAGDATA LADEN
# ============================================================

DAY_LOG_FILE = Path("data/day_log.json")

if DAY_LOG_FILE.exists():
    with open(DAY_LOG_FILE, "r", encoding="utf-8") as f:
        day_log = json.load(f)
else:
    day_log = {}

today_key = date.today().isoformat()

if today_key not in day_log:
    day_log[today_key] = {
        "food_items": [],
        "weight": None
    }

day_data = day_log[today_key]

# ============================================================
# DAGDATA OPSLAAN
# ============================================================

def save_day_log():
    with open(DAY_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(day_log, f, indent=2, ensure_ascii=False)


# ============================================================
# HOOFDSTUK 4 — WEIGHT PROMPT (1x PER WEEK OP WO)
# ============================================================

today_dt = date.today()

iso = today_dt.isocalendar()
current_week = iso.week
current_year = iso.year

today_weekday = today_dt.weekday()

week_key = f"{current_year}-{current_week}"

# ------------------------------------------------------------
# Trigger weegmoment
# ------------------------------------------------------------

if (
    today_weekday == WEIGH_DAY
    and st.session_state.get("last_weight_prompt_week") != week_key
    and not st.session_state.get("show_weight_prompt", False)
):
    st.session_state["show_weight_prompt"] = True


# ------------------------------------------------------------
# Weegmoment UI
# ------------------------------------------------------------

if st.session_state.get("show_weight_prompt", False):

    st.markdown("---")
    st.subheader("Wekelijks weegmoment")

    st.write(
        "Als je wilt kun je je gewicht vastleggen. "
        "Dit is voor trend, niet voor oordeel."
    )

    weight = st.number_input(
        "Gewicht (kg)",
        value=float(day_data.get("weight") or 0.0)
    )

    if weight != day_data.get("weight"):
        day_data["weight"] = weight
        save_day_log()

    c1, c2 = st.columns(2)

    with c1:

        if st.button("Opslaan", key="save_weight"):

            st.session_state["weight_log"].append({
                "date": today_dt.isoformat(),
                "week": week_key,
                "weight": float(weight),
            })

            st.session_state["last_weight_prompt_week"] = week_key
            st.session_state["show_weight_prompt"] = False

            save_data()
            st.rerun()

    with c2:

        if st.button("Overslaan", key="skip_weight"):

            st.session_state["last_weight_prompt_week"] = week_key
            st.session_state["show_weight_prompt"] = False

            save_data()
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

# ------------------------------------------------------------
# Basis berekeningen
# ------------------------------------------------------------

target_kcal = int(day_rec.get("target_kcal", DEFAULT_DAILY_TARGET_KCAL))

eaten_kcal = sum_food_kcal(day_rec)
burned_kcal = sum_activity_kcal(day_rec)

netto_kcal = eaten_kcal - burned_kcal
balance = netto_kcal - target_kcal


# ------------------------------------------------------------
# Analyse + Peet coach
# ------------------------------------------------------------

analysis = analyze_day(day_rec)

coach_text = coach_advice(
    analysis["net"],
    target_kcal
)


# ------------------------------------------------------------
# Resterend kcal budget voor AI recepten
# ------------------------------------------------------------

remaining_kcal = target_kcal - eaten_kcal + burned_kcal

if remaining_kcal < 0:
    remaining_kcal = 0


# ------------------------------------------------------------
# Dagdashboard UI
# ------------------------------------------------------------

st.markdown("### Dagdashboard")

st.metric("Netto kcal", netto_kcal)

col1, col2 = st.columns(2)

with col1:
    st.metric("Gegeten", eaten_kcal)

with col2:
    st.metric("Bewogen", burned_kcal)

st.metric("Dagdoel", target_kcal)


# ------------------------------------------------------------
# Bestaande coach feedback
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
        target=target_kcal,
    )
)


# ------------------------------------------------------------
# Nieuwe Peet coach
# ------------------------------------------------------------

st.markdown("### Peet coach")
st.info(coach_text)

st.caption(f"Dagdoel: {target_kcal} kcal")

# ------------------------------------------------------------
# Nutrition analyse + Hunger predictor
# ------------------------------------------------------------

nutrition = analyze_nutrition(day_rec.get("food_items", []))
hunger_prediction = predict_hunger(nutrition)
hours_since_meal = hours_since_last_meal(day_rec.get("food_items", []))

st.markdown("### Honger verwachting")
st.info(hunger_prediction)

if hours_since_meal is not None:

    if hours_since_meal > 4:
        st.warning(f"Laatste maaltijd {hours_since_meal} uur geleden.")

    else:
        st.caption(f"Laatste maaltijd {hours_since_meal} uur geleden.")

# ============================================================
# HOOFDSTUK 7b — WEEK KOERS
# ============================================================

today_dt = date.today()
week_start = today_dt - timedelta(days=today_dt.weekday())

week_balance = 0
days_counted = 0


for iso_day, d in st.session_state.get("days", {}).items():

    d_date = date.fromisoformat(iso_day)

    if week_start <= d_date <= today_dt:

        eaten = sum_food_kcal(d)
        burned = sum_activity_kcal(d)

        target = int(d.get("target_kcal", DEFAULT_DAILY_TARGET_KCAL))

        net = eaten - burned

        week_balance += net - target
        days_counted += 1


# ------------------------------------------------------------
# Week dashboard UI
# ------------------------------------------------------------

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
# HOOFDSTUK 8 — ACTIES (ETEN + BEWEGING)
# ============================================================

st.divider()
st.header("Dag acties")

# ------------------------------------------------------------
# Safety: zorg dat lijsten bestaan
# ------------------------------------------------------------

if "food_items" not in day_rec:
    day_rec["food_items"] = []

if "activity_items" not in day_rec:
    day_rec["activity_items"] = []


# ============================================================
# HELPER — kcal berekenen
# ============================================================

def calculate_kcal(product, amount):

    unit = str(product.get("unit", "gram")).lower()

    if unit == "stuk":
        return product["kcal"] * amount

    return (product["kcal"] / 100) * amount


# ------------------------------------------------------------
# 8.1 - SNELLE INVOER
# ------------------------------------------------------------

st.markdown("### ⚡ Snelle invoer")

if "pending_new_product" not in st.session_state:
    st.session_state.pending_new_product = None


# ------------------------------------------------------------
# helper - food item toevoegen aan dag
# ------------------------------------------------------------

def add_food_item_to_day(product, amount):

    kcal = calculate_kcal(product, amount)

    day_rec["food_items"].append({
        "id": str(uuid.uuid4()),
        "product_id": product.get("id"),
        "product": product["name"],
        "amount": float(amount),
        "unit": product.get("unit", "gram"),
        "kcal": int(kcal),
        "timestamp": datetime.now().isoformat(),
    })


# ------------------------------------------------------------
# helper - AI vult nieuw product in
# ------------------------------------------------------------

def ai_build_product(product_name, unit_choice):

    if unit_choice == "per stuk":
        unit = "stuk"
        std_portion = 1
        prompt_unit = "per 1 stuk"

    elif unit_choice == "per 250 ml":
        unit = "ml"
        std_portion = 250
        prompt_unit = "per 250 ml"

    else:
        unit = "gram"
        std_portion = 100
        prompt_unit = "per 100 gram"

    prompt = f"""
Je bent een nutrition database assistent.

Geef realistische gemiddelde voedingswaarden voor dit product:

PRODUCT: {product_name}
EENHEID: {prompt_unit}

Geef alleen JSON in exact dit formaat:

{{
  "kcal": 0,
  "protein": 0,
  "fat": 0,
  "carbs": 0,
  "fiber": 0
}}

Gebruik alleen cijfers.
Geen uitleg.
"""

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    raw = getattr(response, "output_text", "") or ""
    cleaned = raw.replace("```json", "").replace("```", "").strip()

    import re
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)

    if not match:
        raise ValueError("AI gaf geen geldig JSON object terug.")

    ai_data = json.loads(match.group())

    return {
        "id": product_name.lower().replace(" ", "_"),
        "name": product_name,
        "unit": unit,
        "kcal": float(ai_data.get("kcal", 0)),
        "protein": float(ai_data.get("protein", 0)),
        "fat": float(ai_data.get("fat", 0)),
        "carbs": float(ai_data.get("carbs", 0)),
        "fiber": float(ai_data.get("fiber", 0)),
        "std_portion": std_portion,
        "alias": [product_name],
    }


def process_quick_food_input(text):

    entries = [e.strip() for e in text.split("+") if e.strip()]
    added = 0

    for entry in entries:

        entry = entry.strip()
        parts = entry.split(" ", 1)

        # alleen productnaam
        if len(parts) == 1:
            product_text = parts[0].strip()
            amount = None

        # hoeveelheid + product
        else:
            try:
                amount = float(parts[0])
                product_text = parts[1].strip()
            except:
                product_text = entry
                amount = None

        results = search_products(product_text)

        exact_match = None

        for r in results:
            aliases = [a.lower() for a in r.get("alias", [])]

            if (
                r.get("name", "").lower() == product_text.lower()
                or product_text.lower() in aliases
            ):
                exact_match = r
                break

        if not exact_match:
            st.session_state.pending_new_product = {
                "name": product_text,
                "amount": amount,
            }
    return

    # standaardportie gebruiken als geen hoeveelheid is ingevoerd
    if amount is None:
        amount = exact_match.get("std_portion", 1)

    add_food_item_to_day(exact_match, amount)
    st.toast(f"{exact_match['name']} toegevoegd")
    added += 1

# ------------------------------------------------------------
# quick input form - ENTER werkt hier automatisch
# ------------------------------------------------------------

with st.form("quick_food_form", clear_on_submit=True):

    quick_text = st.text_input(
        "Typ bijvoorbeeld: 150 kipfilet",
        disabled=day_closed,
        placeholder="bijv: 100 avocado"
    )

    quick_submit = st.form_submit_button("Toevoegen via tekst")

    if quick_submit and not day_closed:
        process_quick_food_input(quick_text)


# ------------------------------------------------------------
# pending nieuw product - AI flow
# ------------------------------------------------------------

pending = st.session_state.pending_new_product

if pending:

    st.warning(f"Product '{pending['name']}' staat niet in de database.")

    unit_choice = st.radio(
        "Hoe wil je dit product opslaan?",
        ["per stuk", "per 250 ml", "per 100 gram"],
        horizontal=True,
        key="pending_unit_choice"
    )

    col_ai, col_cancel = st.columns(2)

    with col_ai:
        if st.button(f"AI vult '{pending['name']}' in", key="ai_fill_missing_product"):

            try:
                with st.spinner("AI vult voedingswaarden in..."):

                    new_product = ai_build_product(
                        product_name=pending["name"],
                        unit_choice=unit_choice
                    )

                    ok, result = add_product(new_product)

                    if not ok:
                        st.warning(result)
                    else:
                        saved_product = result

                        add_food_item_to_day(saved_product, pending["amount"])
                        save_data()

                        st.session_state.pending_new_product = None

                        st.success(
                            f"Product '{saved_product['name']}' toegevoegd aan database en daglog."
                        )
                        st.rerun()

            except Exception as e:
                st.error(f"AI kon product niet invullen: {e}")

    with col_cancel:
        if st.button("Annuleren", key="cancel_missing_product"):
            st.session_state.pending_new_product = None
            st.rerun()

# ------------------------------------------------------------
# 8.1b — RECENTE PRODUCTEN (STABIEL)
# ------------------------------------------------------------

st.markdown("**Recent gegeten**")

recent_products = []
seen = set()

# ------------------------------------------------------------
# 1. eerst vandaag (directe state)
# ------------------------------------------------------------

for item in reversed(day_rec.get("food_items", [])):

    name = item.get("product")

    if name and name not in seen:
        recent_products.append(name)
        seen.add(name)

    if len(recent_products) >= 5:
        break


# ------------------------------------------------------------
# 2. daarna historische dagen
# ------------------------------------------------------------

today = date.today()

for i in range(1, 7):

    d = today - timedelta(days=i)
    key = d.isoformat()

    day = day_log.get(key)

    if not day:
        continue

    for item in reversed(day.get("food_items", [])):

        name = item.get("product")

        if name and name not in seen:
            recent_products.append(name)
            seen.add(name)

        if len(recent_products) >= 5:
            break

    if len(recent_products) >= 5:
        break


# ------------------------------------------------------------
# UI
# ------------------------------------------------------------

if not recent_products:

    st.caption("Nog geen recente producten.")

else:

    cols = st.columns(len(recent_products))

    for i, name in enumerate(recent_products):

        if cols[i].button(name, key=f"recent_product_{i}", disabled=day_closed):

            p = next((x for x in PRODUCTS if x["name"] == name), None)

            if p:

                amount = float(
                    p.get("std_portion")
                    or p.get("default_portion_g")
                    or 100
                )

                unit = str(p.get("unit") or "gram")

                kcal = calculate_kcal(p, amount)

                day_rec["food_items"].append({
                    "id": str(uuid.uuid4()),
                    "product_id": p.get("id"),
                    "product": p["name"],
                    "amount": amount,
                    "unit": unit,
                    "kcal": int(kcal),
                    "timestamp": datetime.now().isoformat(),
                })

                save_data()
                st.rerun()
# ============================================================
# HOOFDSTUK 10 — VANDAAG (ETEN + BEWEGING)
# ============================================================

st.markdown("---")
st.subheader("Vandaag")

food_items = day_rec.get("food_items", [])
activity_items = day_rec.get("activity_items", [])

if not food_items and not activity_items:
    st.caption("Nog niets ingevoerd vandaag.")

# ------------------------------------------------------------
# ETEN
# ------------------------------------------------------------

if food_items:

    st.markdown("**Eten**")

    for item in food_items:

        col1, col2 = st.columns([6,1])

        with col1:
            st.write(f"• {item['product']} | {item['amount']} {item['unit']} | {item['kcal']} kcal")

        with col2:
            if st.button("❌", key=f"del_food_{item['id']}", disabled=day_closed):
                day_rec["food_items"] = [x for x in food_items if x["id"] != item["id"]]
                save_data()
                st.rerun()

# ------------------------------------------------------------
# BEWEGING
# ------------------------------------------------------------

if activity_items:

    st.markdown("**Beweging**")

    for item in activity_items:

        col1, col2 = st.columns([6,1])

        with col1:
            st.write(f"• {item['activity']} | {item['duration_min']} min | {item['kcal']} kcal")

        with col2:
            if st.button("❌", key=f"del_act_{item['id']}", disabled=day_closed):
                day_rec["activity_items"] = [x for x in activity_items if x["id"] != item["id"]]
                save_data()
                st.rerun()

# ------------------------------------------------------------
# TOTALEN
# ------------------------------------------------------------

if food_items or activity_items:

    eaten = sum(x["kcal"] for x in food_items)
    burned = sum(x["kcal"] for x in activity_items)

    st.markdown("---")
    st.write(f"**Totaal gegeten:** {int(eaten)} kcal")
    st.write(f"**Totaal bewogen:** {int(burned)} kcal")
# ============================================================
# 8.2 — ETEN TOEVOEGEN
# ============================================================

st.markdown("### ➕ Eten toevoegen")

with st.form("food_add_form"):

    product_names = sorted([p["name"] for p in PRODUCTS])

    selected_label = st.selectbox(
        "Product",
        product_names,
        index=None,
        placeholder="Zoek product..."
    )

    amount = st.number_input(
        "Hoeveelheid",
        min_value=0.0,
        max_value=2000.0,
        value=100.0,
        step=5.0
    )

    submitted = st.form_submit_button("Toevoegen")

    if submitted and selected_label:

        p = next((x for x in PRODUCTS if x["name"] == selected_label), None)

        if p:

            unit = str(p.get("unit") or "gram").lower()

            kcal = calculate_kcal(p, amount)

            day_rec["food_items"].append({
                "id": str(uuid.uuid4()),
                "product_id": p.get("id"),
                "product": p["name"],
                "amount": float(amount),
                "unit": unit,
                "kcal": int(kcal),
                "timestamp": datetime.now().isoformat(),
            })

            save_data()
            st.success(f"{p['name']} toegevoegd ({int(kcal)} kcal)")
            st.rerun()

# ============================================================
# 8.3 — BEWEGING TOEVOEGEN
# ============================================================

st.markdown("### ➕ Beweging toevoegen")

with st.form("activity_add_form"):

    activity = st.selectbox(
        "Activiteit",
        list(ACTIVITY_MET.keys())
    )

    duration = st.number_input(
        "Duur (minuten)",
        min_value=0,
        step=5
    )

    garmin_kcal = st.number_input(
        "Of voer Garmin kcal direct in",
        min_value=0,
        step=10
    )

    submitted = st.form_submit_button("Toevoegen")

    if submitted:

        # Garmin prioriteit
        if garmin_kcal > 0:
            kcal = int(garmin_kcal)

        else:

            if duration <= 0:
                st.warning("Vul een geldige duur in.")
                st.stop()

            weight = get_current_weight()
            met = ACTIVITY_MET[activity]
            hours = duration / 60

            kcal = int(met * weight * hours * 0.8)

        day_rec["activity_items"].append({
            "id": str(uuid.uuid4()),
            "activity": str(activity),
            "duration_min": int(duration),
            "kcal": int(kcal),
            "timestamp": datetime.now().isoformat(),
        })

        save_data()

        st.success(f"{activity} toegevoegd ({kcal} kcal)")
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
        save_data()
        st.rerun()

with c2:
    if st.button("🟣 Genereer diner", disabled=day_closed):
        st.session_state["pending_recipe"] = generate_recipe_item("Diner", program, remaining_kcal)
        save_data()
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
            save_data()
            st.rerun()

    with col_b:
        if st.button("❌ Verwerp", disabled=day_closed):
            st.session_state["pending_recipe"] = None
            save_data()
            st.rerun()


# ============================================================
# HOOFDSTUK 11 — DAG AFRONDEN
# ============================================================

st.markdown("---")
st.subheader("Dag afronden")

if not day_closed:
    if st.button("🟣 Einde van de dag"):
        day_rec["closed"] = True
        st.success("Dag vastgezet.")
        save_data()
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

# =============================================================
# Gewichtsgrafiek
# =============================================================

DAY_LOG_FILE = Path("data/day_log.json")

if DAY_LOG_FILE.exists():

    with open(DAY_LOG_FILE, "r", encoding="utf-8") as f:
        day_log = json.load(f)

    # huidige dag bepalen
    from datetime import date
    today = date.today().isoformat()

    if today not in day_log:
        day_log[today] = {}

    day_data = day_log[today]

    weights = []
    dates = []

    # sorteer de dagen chronologisch
    for d in sorted(day_log.keys()):

        data = day_log[d]

        if "weight" in data:
            dates.append(d)
            weights.append(data["weight"])

    if weights:

        df_weight = pd.DataFrame({
            "date": pd.to_datetime(dates),
            "Gewicht (kg)": weights
        })

        df_weight = df_weight.set_index("date")

        st.line_chart(df_weight)

    else:
        st.info("Nog geen gewichtsdata beschikbaar.")

else:
    st.info("Nog geen dagdata beschikbaar.")

