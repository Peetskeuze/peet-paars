# ============================================================
# P E E T   P A A R S
# app.py — DEEL 1
# Fundering + Invoer (B1 UX)
# ============================================================

# ============================================================
# HOOFDSTUK 0 — Imports & page config
# ============================================================

import streamlit as st
import uuid
from dataclasses import dataclass
from datetime import datetime, date, timedelta

from core.engine import start_day

# ============================================================
# WEIGHT TRACKING — CONFIG & PAGE SETUP (CANON)
# ============================================================

import streamlit as st
from datetime import date

st.set_page_config(
    page_title="Peet Paars",
    layout="centered"
)

WEIGH_DAY = 2  # 0=ma, 1=di, 2=woensdag, ...

# ============================================================
# WEIGHT TRACKING — STATE (WEEKLIJKS)
# ============================================================

if "weight_log" not in st.session_state:
    st.session_state["weight_log"] = []

if "last_weight_prompt_week" not in st.session_state:
    st.session_state["last_weight_prompt_week"] = None

if "show_weight_prompt" not in st.session_state:
    st.session_state["show_weight_prompt"] = False

# ============================================================
# WEIGHT TRACKING — PROMPT LOGICA (WOENSDAG, 1× PER WEEK)
# ============================================================

today = date.today()
current_week = today.isocalendar().week
today_weekday = today.weekday()

if (
    today_weekday == WEIGH_DAY
    and st.session_state["last_weight_prompt_week"] != current_week
    and not st.session_state["show_weight_prompt"]
):
    st.session_state["show_weight_prompt"] = True

# ============================================================
# WEIGHT TRACKING — WEEKLIJKS WEEGMOMENT (POPUP-STYLE)
# ============================================================

if st.session_state["show_weight_prompt"]:

    st.markdown("---")
    st.subheader("Wekelijks weegmoment")

    st.write(
        "Als je wilt, kun je je gewicht vastleggen.\n\n"
        "Dit helpt om het verloop te zien, niet om vandaag te beoordelen."
    )

    weight = st.number_input(
        "Gewicht (kg)",
        min_value=30.0,
        max_value=250.0,
        step=0.1,
        key="weekly_weight_input"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Opslaan", key="save_weight"):
            st.session_state["weight_log"].append({
                "date": today.isoformat(),
                "week": current_week,
                "weight": float(weight),
            })
            st.session_state["last_weight_prompt_week"] = current_week
            st.session_state["show_weight_prompt"] = False
            st.rerun()

    with col2:
        if st.button("Overslaan", key="skip_weight"):
            st.session_state["last_weight_prompt_week"] = current_week
            st.session_state["show_weight_prompt"] = False
            st.rerun()

    st.markdown("---")
# ============================================================
# MOBILE POLISH — BASE STYLES (STREAMLIT SAFE)
# ============================================================

st.markdown(
    """
    <style>
    /* Basis */
    html, body, [class*="css"]  {
        font-size: 16px;
    }

    /* Koppen compacter op mobiel */
    h1, h2, h3 {
        margin-bottom: 0.25rem;
    }

    /* Caption rustiger */
    .stCaption {
        color: #666;
        margin-top: 0.1rem;
        margin-bottom: 0.6rem;
    }

    /* KPI iets groter, maar niet schreeuwerig */
    .peet-big {
        font-size: 2.1rem;
        font-weight: 700;
        line-height: 1.1;
        margin-top: 0.4rem;
        margin-bottom: 0.1rem;
    }

    /* Divider subtieler */
    hr {
        margin: 0.8rem 0;
        opacity: 0.3;
    }

    /* Buttons mobiel prettiger */
    button {
        padding: 0.6rem 0.8rem !important;
        font-size: 0.95rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# UI helpers — Cards
# ============================================================

st.title("Peet Paars")
st.caption("Dagkeuze voor rust- en sportdagen")
st.markdown(
    '<a href="#verloop" style="font-size:14px; text-decoration:none;">↳ Verloop</a>',
    unsafe_allow_html=True
)

# ============================================================
# NL labels (vaste mapping, geen locale nodig)
# ============================================================

NL_DAY_ABBR = ["MA", "DI", "WO", "DO", "VR", "ZA", "ZO"]
NL_DAY_FULL = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
NL_MONTH_FULL = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december"
]

def format_day_title_nl(selected_dt: date, today: date) -> str:
    delta = (selected_dt - today).days

    if delta == 0:
        return "Vandaag"
    if delta == 1:
        return "Morgen"
    if delta == -1:
        return "Gisteren"

    day_name = NL_DAY_FULL[selected_dt.weekday()]
    month_name = NL_MONTH_FULL[selected_dt.month - 1]
    return f"{day_name} {selected_dt.day} {month_name}"

# ============================================================
# HOOFDSTUK 1 — State init, dagstore & planner (CANON)
# ============================================================

# --- basislijsten (legacy: laten bestaan, maar we koppelen ze aan selected_date)
if "food_items" not in st.session_state:
    st.session_state["food_items"] = []

if "activity_items" not in st.session_state:
    st.session_state["activity_items"] = []

if "meal_consumptions" not in st.session_state:
    st.session_state["meal_consumptions"] = []

if "dagresultaten" not in st.session_state:
    st.session_state["dagresultaten"] = []

# --- NIEUW: dagstore
if "days" not in st.session_state:
    st.session_state["days"] = {}

# --- NIEUW: geselecteerde dag (planner)
if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = date.today().isoformat()

# --- budget (hard target)
daily_budget = 1800

# --- helper: haal dagrecord op of maak hem aan
def _ensure_day(iso_date: str):
    if iso_date not in st.session_state["days"]:
        st.session_state["days"][iso_date] = {
            "day_type": "rust",
            "food_items": [],
            "activity_items": [],
            "closed": False,
        }
    return st.session_state["days"][iso_date]

# --- huidige dag (volgens planner)
selected_iso = st.session_state["selected_date"]
day_rec = _ensure_day(selected_iso)

# --- legacy variabelen koppelen aan geselecteerde dag
# (zo hoeven we verderop minimaal te wijzigen)
st.session_state["food_items"] = day_rec["food_items"]
st.session_state["activity_items"] = day_rec["activity_items"]
st.session_state["day_closed"] = bool(day_rec.get("closed", False))

# --- engine dagtype sync (alleen voor snapshot day_type)
if "day" not in st.session_state:
    st.session_state["day"] = start_day(day_rec["day_type"])

# als user via planner van dag wisselt, moet engine dagtype mee
# (we houden het simpel: alleen day_type waarde gebruiken)
day = st.session_state["day"]


# ============================================================
# HOOFDSTUK 1b — PLANNER (weekstrip) — klikvast + NL labels
# ============================================================

st.markdown("")

def _pick_day(iso: str):
    st.session_state["selected_date"] = iso

today = date.today()
week_start = today - timedelta(days=today.weekday())
week_days = [week_start + timedelta(days=i) for i in range(7)]

cols = st.columns(7)
for i, d in enumerate(week_days):
    iso = d.isoformat()
    rec = _ensure_day(iso)

    # duidelijk verschillende symbolen
    if rec.get("closed"):
        dot = "🟣"       # afgesloten
    elif iso == st.session_state["selected_date"]:
        dot = "⬤"        # geselecteerd
    elif d > today:
        dot = "·"        # toekomst
    else:
        dot = "◯"        # open dag

    label = NL_DAY_ABBR[d.weekday()]  # MA/DI/...

    with cols[i]:
        st.button(
            f"{label} {dot}",
            key=f"daypick_{iso}",
            on_click=_pick_day,
            args=(iso,)
        )

# --- header (Vandaag/Morgen/Gisteren of datum)
selected_dt = date.fromisoformat(st.session_state["selected_date"])
title = format_day_title_nl(selected_dt, today)

# ============================================================
# DASHBOARD — CONTEXT (STRIP)
# ============================================================

day_name = NL_DAY_FULL[selected_dt.weekday()]
month_name = NL_MONTH_FULL[selected_dt.month - 1]
sub = f"{day_name} {selected_dt.day} {month_name}"

st.markdown(f"### {title}")
st.caption(f"{sub} · Dagtype: {day_rec['day_type'].capitalize()}")
st.markdown("---")

# ============================================================
# DAGTYPE KIEZEN (RUST ↔ SPORT)
# ============================================================

day_type_label = "Sportdag" if day_rec["day_type"] == "sport" else "Rustdag"

new_day_type = st.radio(
    "Dagtype",
    options=["rust", "sport"],
    index=0 if day_rec["day_type"] == "rust" else 1,
    horizontal=True,
    format_func=lambda x: "Rustdag" if x == "rust" else "Sportdag"
)

if new_day_type != day_rec["day_type"]:
    day_rec["day_type"] = new_day_type

# ============================================================
# HERO — TUSSENSTAND (PRE-POLISH + MICROCOPY)
# ============================================================

st.markdown("### Tussenstand")

# --- Veilig optellen eten ---
planned_kcal = 0  # Peet Paars kent geen geplande maaltijden

extra_kcal = sum(
    fi.kcal for fi in st.session_state.get("food_items", [])
)

total_eaten_kcal = planned_kcal + extra_kcal

# --- Veilig optellen beweging ---
burned_kcal_total = sum(
    ai.kcal for ai in st.session_state.get("activity_items", [])
)

# --- Netto ---
netto_kcal = total_eaten_kcal - burned_kcal_total

# --- HERO VISUAL ---
st.markdown(
    f"""
    <div style="padding:16px 0;">
        <div style="font-size:42px; font-weight:700;">
            {int(netto_kcal)} kcal
        </div>
        <div style="font-size:14px; opacity:0.7;">
            {int(total_eaten_kcal)} gegeten − {int(burned_kcal_total)} beweging
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- HERO MICROCOPY (DYNAMISCH) ---
has_food = len(st.session_state.get("food_items", [])) > 0
has_activity = len(st.session_state.get("activity_items", [])) > 0

if not has_food and not has_activity:
    st.caption("Dit is het begin van je dag.")
else:
    st.caption("Tussenstand vandaag.")

# ============================================================
# HOOFDSTUK 2 — Modellen & helpers (CANON)
# ============================================================

@dataclass
class FoodItem:
    id: str
    product: str
    amount: float
    unit: str
    kcal: int
    timestamp: str


class FreeKcalItem:
    def __init__(self, name: str, amount: float, unit: str, kcal: int):
        self.id = f"free_{uuid.uuid4()}"
        self.product = name
        self.amount = float(amount)
        self.unit = unit
        self.kcal = int(kcal)
        self.timestamp = datetime.now().isoformat()

def format_day_title_nl(selected_dt: date, today: date) -> str:
    delta = (selected_dt - today).days

    if delta == 0:
        return "Vandaag"
    if delta == 1:
        return "Morgen"
    if delta == -1:
        return "Gisteren"

    day_name = NL_DAY_FULL[selected_dt.weekday()]
    month_name = NL_MONTH_FULL[selected_dt.month - 1]
    return f"{day_name} {selected_dt.day} {month_name}"

@dataclass
class ActivityItem:
    activity: str
    duration_min: int
    burned_kcal: int
    timestamp: str


ACTIVITY_KCAL_PER_MIN = {
    "wandelen": 4,
    "fietsen": 8,
    "hardlopen": 10,
    "krachttraining": 6,
    "zwemmen": 9,
    "spinnen": 9,
    "sport algemeen": 6,
}

ZERO_POINT_KEYWORDS = [
    "kip", "kipfilet", "ei", "groente", "groenten",
    "bloemkool", "broccoli", "spinazie", "sla",
    "vis", "tonijn", "kabeljauw", "zalm",
    "kwark", "yoghurt", "magere"
]

# NL labels (geen locale nodig)
NL_DAY_ABBR = ["MA", "DI", "WO", "DO", "VR", "ZA", "ZO"]
NL_DAY_FULL = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
NL_MONTH_FULL = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december"
]



# ============================================================
# HOOFDSTUK 2a — Vrije ingrediënten (kcal-hints)
# ============================================================

FREE_FOOD_HINTS = {
    "banaan": {"unit": "stuk", "kcal_per_unit": 105},
    "appel": {"unit": "stuk", "kcal_per_unit": 80},
    "ei": {"unit": "stuk", "kcal_per_unit": 75},
    "olijfolie": {"unit": "eetlepel", "kcal_per_unit": 90},
    "boter": {"unit": "gram", "kcal_per_100": 717},
}

GENERIC_KCAL_DEFAULTS = {
    "stuk": 80,     # kcal per stuk (globale schatting)
    "gram": 2,      # kcal per gram (≈ 200 per 100 g)
    "ml": 0.5,      # kcal per ml (≈ 50 per 100 ml)
    "eetlepel": 90, # kcal per eetlepel
}


# ============================================================
# HOOFDSTUK 3 — PRODUCTMODEL (CANON v1)
# ============================================================

PRODUCTS = {
    "brood": {
        "label": "Brood (volkoren)",
        "unit": "gram",
        "kcal_per_100g": 240,
    },
    "kaas": {
        "label": "Kaas (jong belegen)",
        "unit": "gram",
        "kcal_per_100g": 356,
    },
    "kipfilet": {
        "label": "Kipfilet",
        "unit": "gram",
        "kcal_per_100g": 110,
    },
    "ei": {
        "label": "Ei",
        "unit": "stuk",
        "kcal_per_piece": 75,
    },
    "bier": {
        "label": "Bier",
        "unit": "cl",
        "kcal_per_100ml": 43,
    },
    "wijn": {
        "label": "Wijn",
        "unit": "cl",
        "kcal_per_100ml": 85,
    },
    "olijfolie": {
        "label": "Olijfolie",
        "unit": "eetlepel",
        "kcal_per_tbsp": 90,
    },
}


def calculate_food_kcal(product, amount):
    unit = product["unit"]

    if unit == "gram":
        return int((product["kcal_per_100g"] / 100) * amount)

    if unit == "cl":
        ml = amount * 10
        return int((product["kcal_per_100ml"] / 100) * ml)

    if unit == "eetlepel":
        return int(product["kcal_per_tbsp"] * amount)

    if unit == "stuk":
        return int(product["kcal_per_piece"] * amount)

    return 0

# ============================================================
# ZONE 2 — ACTIE
# ============================================================

# ============================================================
# ACTIE — ETEN TOEVOEGEN
# ============================================================

with st.expander("➕ Eten toevoegen", expanded=False):

    dag_afgesloten = st.session_state.get("day_closed", False)

    if dag_afgesloten:
        st.info("Deze dag is afgesloten. Nieuwe invoer is niet meer mogelijk.")

    product_keys = list(PRODUCTS.keys())
    product_labels = [PRODUCTS[k]["label"] for k in product_keys]

    selected_label = st.selectbox(
        "Product",
        product_labels,
        disabled=dag_afgesloten
    )
    selected_key = product_keys[product_labels.index(selected_label)]

    p = PRODUCTS[selected_key]
    unit = p["unit"]

    if unit in ("gram", "cl", "stuk"):
        amount = st.number_input(
            f"Hoeveelheid ({unit})",
            min_value=0,
            step=5,
            disabled=dag_afgesloten
        )
    else:
        amount = st.number_input(
            "Hoeveelheid (eetlepel)",
            min_value=0.0,
            step=0.5,
            disabled=dag_afgesloten
        )

    if st.button("Toevoegen", key="add_food", disabled=dag_afgesloten):
        if amount <= 0:
            st.warning("Vul een geldige hoeveelheid in.")
        else:
            kcal = calculate_food_kcal(p, amount)

            st.session_state["food_items"].append(
                FoodItem(
                    id=str(uuid.uuid4()),
                    product=p["label"],
                    amount=float(amount),
                    unit=unit,
                    kcal=int(kcal),
                    timestamp=datetime.now().isoformat(),
                )
            )

            st.success(f"{p['label']} toegevoegd ({int(kcal)} kcal)")
            st.rerun()

# ============================================================
# ACTIE — BEWEGING TOEVOEGEN
# ============================================================

with st.expander("➕ Beweging toevoegen", expanded=False):

    dag_afgesloten = st.session_state.get("day_closed", False)

    if dag_afgesloten:
        st.info("Deze dag is afgesloten. Nieuwe invoer is niet meer mogelijk.")

    activity = st.selectbox(
        "Activiteit",
        list(ACTIVITY_KCAL_PER_MIN.keys()),
        disabled=dag_afgesloten
    )

    duration = st.number_input(
        "Duur (minuten)",
        min_value=0,
        step=5,
        disabled=dag_afgesloten
    )

    if st.button("Toevoegen", key="add_activity", disabled=dag_afgesloten):
        if duration <= 0:
            st.warning("Vul een geldige duur in.")
        else:
            kcal = duration * ACTIVITY_KCAL_PER_MIN[activity]

            st.session_state["activity_items"].append(
                ActivityItem(
                    activity=activity,
                    duration_min=int(duration),
                    burned_kcal=int(kcal),
                    timestamp=datetime.now().isoformat(),
                )
            )

            st.success(f"{activity.capitalize()} toegevoegd ({int(kcal)} kcal)")
            st.rerun()

# ============================================================
# P E E T   P A A R S
# app.py — DEEL 2
# Overzicht, dagbalans, afsluiten & week
# ============================================================
# ============================================================
# TUSSENSTAND VAN DE DAG (FASE 5.1)
# ============================================================

if not st.session_state.get("day_closed"):

    st.markdown("---")

# ============================================================
# HOOFDSTUK 8 — DAG AFSLUITEN (CANON)
# ============================================================

st.divider()
st.subheader("Dag afronden")

if not st.session_state["day_closed"]:
    if st.button("🟣 Einde van de dag"):

        today = st.session_state["selected_date"]


        dag_snapshot = {
            "date": today,
            "day_type": day.get("day_type", "onbekend"),
            "planned_meals_kcal": planned_kcal,
            "extra_eaten_kcal": extra_eaten_kcal,
            "remaining_kcal": remaining_kcal,
            "delta_corrected": delta_corrected,
        }

        bestaande = [
            d for d in st.session_state["dagresultaten"]
            if d["date"] != today
        ]
        bestaande.append(dag_snapshot)

        st.session_state["dagresultaten"] = bestaande

        # --- NIEUW: dagstore waarheid
        day_rec["closed"] = True
        day_rec["day_type"] = day.get("day_type", day_rec["day_type"])

        # legacy vlag (blijft bestaan, maar hangt aan day_rec)
        st.session_state["day_closed"] = True

        st.success("Dag vastgezet. Dit telt mee in je weekritme.")

# ============================================================
# FASE 5 — VOORUITBLIK (TEKST + KNOP, OPTIONEEL)
# ============================================================

from datetime import timedelta

if st.session_state.get("day_closed"):

    st.markdown("---")
    st.subheader("Vooruitblik")

    today_dt = date.fromisoformat(st.session_state["selected_date"])
    tomorrow_dt = today_dt + timedelta(days=1)
    tomorrow_iso = tomorrow_dt.isoformat()

    tomorrow_rec = _ensure_day(tomorrow_iso)

    # --- tekst (zacht, beschrijvend)
    if day_rec["day_type"] == "rust":
        st.caption(
            "Vandaag was een rustdag. "
            "Morgen zou logisch een sportdag kunnen zijn."
        )
        suggested_type = "sport"
        button_label = "Morgen als sportdag markeren"
    else:
        st.caption(
            "Vandaag was een sportdag. "
            "Morgen is rust waarschijnlijk helpend."
        )
        suggested_type = "rust"
        button_label = "Morgen als rustdag markeren"

    # --- knop (optioneel, één actie)
    if st.button(button_label):
        tomorrow_rec["day_type"] = suggested_type
        st.success(
            f"Morgen staat nu gemarkeerd als "
            f"{'sportdag' if suggested_type == 'sport' else 'rustdag'}."
        )

# ============================================================
# VERLOOP — GEWICHT (WEEKLIJKS, ALTIJD ZICHTBAAR)
# ============================================================

if len(st.session_state.get("weight_log", [])) >= 1:

    st.markdown("---")
    st.markdown('<div id="verloop"></div>', unsafe_allow_html=True)
    st.subheader("Verloop")

    st.caption(
        "Gewicht verandert traag. "
        "Dit laat het verloop per week zien."
    )

    # --- Data voorbereiden ---
    weight_data = sorted(
        st.session_state["weight_log"],
        key=lambda x: x["date"]
    )

    dates = [w["date"] for w in weight_data]
    weights = [w["weight"] for w in weight_data]

    # --- Grafiek ---
    st.line_chart(
        {
            "Gewicht (kg)": weights
        },
        x=dates
    )