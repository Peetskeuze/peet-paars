import sys
import json
import os
import re
import uuid
import asyncio
from pathlib import Path
from datetime import datetime, date, timedelta

from nicegui import ui, app
from dotenv import load_dotenv
from fastapi.responses import FileResponse

load_dotenv()

# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"

# ============================================================
# STATIC FILE ROUTES (MOET BOVENAAN STAAN)
# ============================================================

@app.get('/debug-files', include_in_schema=False)
def debug_files():
    return {
        "root": str(ROOT),
        "static_dir": str(STATIC_DIR),
        "exists": STATIC_DIR.exists(),
        "files": os.listdir(STATIC_DIR) if STATIC_DIR.exists() else []
    }

@app.get('/manifest.json', include_in_schema=False)
def manifest():
    return FileResponse(STATIC_DIR / 'manifest.json')

@app.get('/sw.js', include_in_schema=False)
def sw():
    return FileResponse(STATIC_DIR / 'sw.js')

@app.get('/icon-192.png', include_in_schema=False)
def icon_192():
    return FileResponse(STATIC_DIR / 'icon-192.png')

@app.get('/icon-512.png', include_in_schema=False)
def icon_512():
    return FileResponse(STATIC_DIR / 'icon-512.png')

# ============================================================
# APP INIT
# ============================================================

from core.profile_store import init_db, save_profile, load_profile

init_db()
# ============================================================
# NICEGUI UI CONFIG
# ============================================================

ui.add_head_html("""

<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">

<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#6E3BF7">

<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="Peet Coach">

<style>
html, body {
    height: 100%;
    margin: 0;
}

/* Fullscreen container */
.q-page-container {
    height: 100vh !important;
    max-width: 100% !important;
    padding: 8px !important;
    overflow-y: auto;
    overflow-x: hidden;
}

/* Page */
.q-page {
    min-height: 100vh !important;
}

/* App background (splash feel) */
body {
    background-color: #6E3BF7;
}
</style>

<script>
// SERVICE WORKER
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}

// INSTALL PROMPT
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;

  const btn = document.createElement('button');
  btn.innerText = '📲 Installeer Peet Coach';
  btn.style.position = 'fixed';
  btn.style.bottom = '80px';
  btn.style.left = '50%';
  btn.style.transform = 'translateX(-50%)';
  btn.style.padding = '12px 20px';
  btn.style.background = '#6E3BF7';
  btn.style.color = 'white';
  btn.style.border = 'none';
  btn.style.borderRadius = '12px';
  btn.style.zIndex = '9999';

  btn.onclick = async () => {
    btn.remove();
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
  };

  document.body.appendChild(btn);
});
</script>

""")

# ============================================================
# USER PROFILE (persoonlijk dagdoel)
# ============================================================

USER_PROFILE_FILE = ROOT / 'data' / 'user_profile.json'

def load_user_profile():
    if USER_PROFILE_FILE.exists():
        try:
            with open(USER_PROFILE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def calculate_daily_target(profile: dict) -> int:

    sex = profile.get('sex', 'male')
    age = profile.get('age', 63)
    height = profile.get('height', 186)
    weight = profile.get('current_weight', 110)
    target_weight = profile.get('target_weight', 100)
    weeks = profile.get('weeks_to_goal', 12)

    # BMR (Mifflin-St Jeor)
    if sex == 'female':
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5

    tdee = bmr * 1.4

    weight_loss = max(weight - target_weight, 0)
    days = max(weeks * 7, 1)

    deficit_per_day = (weight_loss * 7700) / days

    target = int(max(tdee - deficit_per_day, 1400))

    return target
# ------------------------------------------------------------
# Core imports
# ------------------------------------------------------------
from core.day_analysis import analyze_day
from core.coach import coach_advice
from core.nutrition import analyze_nutrition
from core.hunger import predict_hunger
from core.meal_timing import hours_since_last_meal
from core.product_db import search_products, get_product, load_products, add_product

# ------------------------------------------------------------
# OpenAI optioneel
# ------------------------------------------------------------
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False


#=============================================================
# MOBIEL LAYOUT
#=============================================================

ui.add_css("""

/* algemene achtergrond */
body {
    background:#f6f6f8;
}

/* app breedte */
.nicegui-content {
    max-width:430px;
    margin:auto;
}

/* kaarten */
.q-card {
    border-radius:16px;
    box-shadow:0 4px 14px rgba(0,0,0,0.08);
}

/* grote kcal kaart */
.kcal-big {
    font-size:28px;
    font-weight:700;
    color:#5b21b6;
    background:#ede9fe;
    padding:18px;
    border-radius:16px;
    text-align:center;
}

/* titel */
.app-title {
    font-size:26px;
    font-weight:700;
    margin-bottom:4px;
}

/* datum */
.app-date {
    font-size:14px;
    color:#6b7280;
}

/* bottom navigation */
.bottom-nav {
    font-size:14px;
    font-weight:600;
}

""")

# ============================================================
# CANON SETTINGS
# ============================================================

DEFAULT_DAILY_TARGET_KCAL = 1800
WEIGH_DAY = 2   # woensdag
USER_WEIGHT_KG = 110

ACTIVITY_MET = {
    "wandelen": 3.5,
    "fietsen rustig": 6,
    "fietsen tempo": 8,
    "wielrennen": 10,
    "spinnen": 9,
    "Sportschool": 5,
    "zwemmen": 8,
}

NL_DAY_FULL = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
NL_MONTH_FULL = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december"
]

# ============================================================
# DATA / STATE
# ============================================================

PEET_DATA_FILE = ROOT / 'peet_data.json'
DAY_LOG_FILE = ROOT / 'data' / 'day_log.json'

try:
    PRODUCTS = load_products()
except Exception:
    PRODUCTS = []

app_state = {
    'selected_date': date.today().isoformat(),
    'days': {},
    'weight_log': [],
    'last_weight_prompt_week': None,
    'show_weight_prompt': False,
    'pending_new_product': None,
    'pending_product_choice': None,
    'pending_recipe': None,
    'active_tab': 'today',
}

# element refs
refs = {}

# ============================================================
# HELPERS
# ============================================================

def update_nav_style(active: str):
    for name, btn in refs.get('nav_buttons', {}).items():
        if name == active:
            btn.classes('text-purple-600')
        else:
            btn.classes('text-gray-400')

def safe_notify(message: str, kind: str = 'info') -> None:
    ui.notify(message, type=kind)

def format_day_title_nl(selected_dt: date, today_dt: date) -> str:
    delta = (selected_dt - today_dt).days
    if delta == 0:
        return 'Vandaag'
    if delta == -1:
        return 'Gisteren'
    if delta == 1:
        return 'Morgen'
    day_name = NL_DAY_FULL[selected_dt.weekday()]
    month_name = NL_MONTH_FULL[selected_dt.month - 1]
    return f'{day_name} {selected_dt.day} {month_name}'

def calc_food_kcal(product_def: dict, amount: float) -> int:
    unit = str(product_def.get('unit') or '').lower()

    if unit == 'gram':
        kcal100 = float(product_def.get('kcal_per_100g', product_def.get('kcal', 0)))
        return int((kcal100 / 100.0) * amount)

    if unit == 'ml':
        kcal100 = float(product_def.get('kcal_per_100ml', product_def.get('kcal', 0)))
        return int((kcal100 / 100.0) * amount)

    if unit == 'cl':
        kcal100 = float(product_def.get('kcal_per_100ml', product_def.get('kcal', 0)))
        ml = amount * 10
        return int((kcal100 / 100.0) * ml)

    if unit == 'eetlepel':
        return int(float(product_def.get('kcal_per_tbsp', product_def.get('kcal', 0))) * amount)

    if unit == 'stuk':
        return int(float(product_def.get('kcal_per_piece', product_def.get('kcal', 0))) * amount)

    # fallback naar oud model
    kcal_base = float(product_def.get('kcal', 0))
    if unit in ['portie', 'stuk']:
        return int(kcal_base * amount)
    return int((kcal_base / 100.0) * amount)

def ensure_day(iso_date: str) -> dict:
    if iso_date not in app_state['days']:
        app_state['days'][iso_date] = {
            'food_items': [],
            'activity_items': [],
            'closed': False,
            'program': 'Paars',
            'target_kcal': DEFAULT_DAILY_TARGET_KCAL,
        }
        save_data()
    return app_state['days'][iso_date]

def sum_food_kcal(day_rec: dict) -> int:
    return int(sum(item.get('kcal', 0) for item in day_rec.get('food_items', [])))

def sum_activity_kcal(day_rec: dict) -> int:
    return int(sum(item.get('kcal', 0) for item in day_rec.get('activity_items', [])))

def coach_line(eaten: int, burned: int, net: int, target: int) -> str:
    if eaten == 0 and burned == 0:
        return 'Start rustig. Eiwit eerst, groente als volume.'
    if net <= target:
        return 'Je zit onder je dagdoel. Prima koers.'
    over = net - target
    return f'Je zit {over} kcal boven je dagdoel. Compenseer met beweging of eet lichter.'

def get_current_weight() -> float:
    log = app_state.get('weight_log', [])
    if not log:
        return USER_WEIGHT_KG
    latest = sorted(log, key=lambda x: x['date'])[-1]
    return float(latest['weight'])

def load_data() -> dict:
    if PEET_DATA_FILE.exists():
        try:
            with open(PEET_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data() -> None:
    try:
        with open(PEET_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_state.get('days', {}), f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_day_log() -> dict:
    if DAY_LOG_FILE.exists():
        try:
            with open(DAY_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_day_log(day_log: dict) -> None:
    DAY_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DAY_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(day_log, f, indent=2, ensure_ascii=False)

def calculate_kcal(product: dict, amount: float) -> float:

    if not product:
        return 0

    kcal_value = product.get("kcal", 0)
    grams_per_unit = product.get("grams_per_unit", 1)
    unit = str(product.get("unit", "gram")).lower()

    try:
        amount = float(amount)
    except:
        return 0

    # meeste producten zijn per gram
    if unit == "gram":
        return (kcal_value / 100.0) * amount

    # producten per stuk
    if unit == "stuk":
        return kcal_value * amount

    # fallback
    return (kcal_value / 100.0) * amount

def add_food_item_to_day(day_rec: dict, product: dict, amount: float) -> None:

    # veiligheidscheck: product moet bestaan
    if product is None:
        safe_notify('Product niet gevonden in database.', 'warning')
        return

    # hoeveelheid fallback
    if amount is None or amount == 0:
        amount = float(product.get('std_portion', 1))

    try:
        kcal = calculate_kcal(product, amount)
    except Exception:
        safe_notify(f"Kan kcal niet berekenen voor '{product.get('name', '?')}'.", 'warning')
        return

    day_rec['food_items'].append({
        'id': str(uuid.uuid4()),
        'product_id': product.get('id'),
        'product': product.get('name') or product.get('label') or '?',
        'amount': float(amount),
        'unit': product.get('unit', 'gram'),
        'kcal': int(kcal),
        'timestamp': datetime.now().isoformat(),
    })

def generate_recipe_item(
    meal_type: str,
    program: str,
    remaining_kcal: int,
    target_kcal: int,
    eaten_kcal: int,
    burned_kcal: int,
) -> dict:

    # ---------------------------------------------------------
    # kcal strategie
    # ---------------------------------------------------------

    if meal_type == "Lunch":
        kcal_target = int(remaining_kcal * 0.45)
    else:
        kcal_target = int(remaining_kcal * 0.60)

    kcal_min = int(kcal_target * 0.8)
    kcal_max = int(kcal_target * 1.1)

    # fallback veiligheid
    if kcal_min < 350:
        kcal_min = 350

    if kcal_max > remaining_kcal:
        kcal_max = remaining_kcal

    # ---------------------------------------------------------
    # eiwit rotatie voor variatie
    # ---------------------------------------------------------

    protein_sources = [
        "kip",
        "zalm",
        "tonijn",
        "biefstuk",
        "garnalen",
        "ei",
        "tofu",
        "linzen",
        "bonen",
        "kalkoen",
        "gehakt",
    ]

    # ---------------------------------------------------------
    # AI prompt
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
- vet en saus sturen de kcal
- maximaal 10 ingrediënten
- geschikt voor een doordeweekse keuken
- geen ingewikkelde chef technieken

VARIATIE REGEL

Gebruik verschillende eiwitbronnen.
Niet altijd kip.

Mogelijke eiwitbronnen:

{", ".join(protein_sources)}

Wissel tussen:

vis
vlees
ei
vegetarisch

CALORIE DOEL

Doel kcal: {kcal_target}

Acceptabel bereik:
tussen {kcal_min} en {kcal_max} kcal

Blijf binnen het resterende kcal budget.

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
    # fallback recept (zonder AI)
    # ---------------------------------------------------------

    def fallback() -> dict:

        if meal_type == 'Lunch':

            model_out = {
                "title": "Bowl met kipfilet, bonen en yoghurt dressing",
                "kcal": 560,
                "ingredients": [
                    "kipfilet 150 g",
                    "kidneybonen 150 g",
                    "paprika 100 g",
                    "komkommer 100 g",
                    "tomaat 150 g",
                    "magere yoghurt 150 g",
                ],
                "instructions": [
                    "bak de kipfilet goudbruin",
                    "snij de groente grof",
                    "meng yoghurt met citroen en peper",
                    "combineer alles in een kom",
                ],
                "chef_tip": "Gebruik yoghurt in plaats van olie voor een lichtere dressing.",
            }

        else:

            model_out = {
                "title": "Zalm met broccoli en krieltjes uit de oven",
                "kcal": 720,
                "ingredients": [
                    "zalmfilet 180 g",
                    "broccoli 350 g",
                    "krieltjes 250 g",
                    "citroen 1",
                    "olijfolie 1 el",
                ],
                "instructions": [
                    "verwarm oven op 200 graden",
                    "snij broccoli en halveer krieltjes",
                    "leg alles op een bakplaat",
                    "bak 20 minuten in de oven",
                ],
                "chef_tip": "Hou olie bij één eetlepel. Dat is de belangrijkste kcal knop.",
            }

        return build_recipe(model_out)

    # ---------------------------------------------------------
    # helper om output om te zetten naar app format
    # ---------------------------------------------------------

    def build_recipe(model_out: dict) -> dict:

        return {
            "id": str(uuid.uuid4()),
            "product": f"{meal_type} recept: {model_out.get('title','Recept')}",
            "amount": 1,
            "unit": "portie",
            "kcal": int(model_out.get("kcal", 650)),
            "timestamp": datetime.now().isoformat(),
            "meta": {
                "source": "peet_prompt",
                "program": program,
                "meal_type": meal_type,
                "ingredients": model_out.get("ingredients", []),
                "instructions": model_out.get("instructions", []),
                "note": str(model_out.get("chef_tip", "")),
            },
        }

    # ---------------------------------------------------------
    # AI call
    # ---------------------------------------------------------

    if not OPENAI_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        return fallback()

    try:

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
        )

        raw = getattr(response, "output_text", None)

        if not raw:
            return fallback()

        cleaned = raw.replace("```json", "").replace("```", "").strip()

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)

        if not match:
            return fallback()

        model_out = json.loads(match.group())

        return build_recipe(model_out)

    except Exception:

        return fallback()

def ai_build_product(product_name: str, unit_choice: str) -> dict:
    if unit_choice == 'per stuk':
        unit = 'stuk'
        std_portion = 1
        prompt_unit = 'per 1 stuk'
    elif unit_choice == 'per 250 ml':
        unit = 'ml'
        std_portion = 250
        prompt_unit = 'per 250 ml'
    else:
        unit = 'gram'
        std_portion = 100
        prompt_unit = 'per 100 gram'

    if not OPENAI_AVAILABLE or not os.getenv('OPENAI_API_KEY'):
        raise RuntimeError('OPENAI_API_KEY ontbreekt of OpenAI package niet beschikbaar.')

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
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.responses.create(model='gpt-4o-mini', input=prompt)
    raw = getattr(response, 'output_text', '') or ''
    cleaned = raw.replace('```json', '').replace('```', '').strip()
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if not match:
        raise ValueError('AI gaf geen geldig JSON object terug.')
    ai_data = json.loads(match.group())
    return {
        'id': product_name.lower().replace(' ', '_'),
        'name': product_name,
        'label': product_name,
        'unit': unit,
        'kcal': float(ai_data.get('kcal', 0)),
        'protein': float(ai_data.get('protein', 0)),
        'fat': float(ai_data.get('fat', 0)),
        'carbs': float(ai_data.get('carbs', 0)),
        'fiber': float(ai_data.get('fiber', 0)),
        'std_portion': std_portion,
        'alias': [product_name],
    }

# ============================================================
# UI HELPERS
# ============================================================

# ------------------------------------------------------------
# user profile opslaan
# ------------------------------------------------------------

USER_PROFILE_FILE = ROOT / 'data' / 'user_profile.json'

def save_user_profile(profile: dict):
    try:
        USER_PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USER_PROFILE_FILE, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2)
    except Exception as e:
        print("Error saving profile:", e)


def save_profile_from_ui():

    profile = {
        "sex": refs['profile_sex'].value,
        "age": int(refs['profile_age'].value),
        "height": int(refs['profile_height'].value),
        "current_weight": float(refs['profile_weight'].value),
        "target_weight": float(refs['profile_target'].value),
        "weeks_to_goal": int(refs['profile_weeks'].value),
        "kcal_target": int(refs['profile_kcal_target'].value) if refs['profile_kcal_target'].value else None,
    }

    save_profile(profile)

    safe_notify("Profiel opgeslagen", "positive")

    refresh_ui()
# ------------------------------------------------------------
# veilige ref setter (voorkomt KeyError)
# ------------------------------------------------------------

def set_ref_text(name: str, value: str):
    el = refs.get(name)
    if el:
        el.set_text(value)

def refresh_ui() -> None:

    # products opnieuw laden zodat nieuwe producten zichtbaar worden
    global PRODUCTS
    PRODUCTS = load_products()

    product_names = sorted([
        p.get('name') or p.get('label')
        for p in PRODUCTS
        if p.get('name') or p.get('label')
    ])

    if 'food_select' in refs:
        refs['food_select'].options = product_names

    selected_dt = date.fromisoformat(app_state['selected_date'])
    today_dt = date.today()
    day_rec = ensure_day(app_state['selected_date'])
    day_closed = bool(day_rec.get('closed', False))

    # ------------------------------------------------------------
    # context
    # ------------------------------------------------------------

    if 'date_picker' in refs:
        refs['date_picker'].value = selected_dt

    if 'day_title' in refs:
        refs['day_title'].set_text(format_day_title_nl(selected_dt, today_dt))

    if 'day_sub' in refs:
        refs['day_sub'].set_text(
            f"{NL_DAY_FULL[selected_dt.weekday()]} {selected_dt.day} {NL_MONTH_FULL[selected_dt.month - 1]}"
        )

    if 'target_kcal' in refs:
        refs['target_kcal'].value = int(day_rec.get('target_kcal', DEFAULT_DAILY_TARGET_KCAL))

    if 'quick_input' in refs:
        refs['quick_input'].enabled = not day_closed

    if 'quick_add_btn' in refs:
        refs['quick_add_btn'].enabled = not day_closed

    # ------------------------------------------------------------
    # kcal berekeningen
    # ------------------------------------------------------------

    profile = load_profile()

    if profile and profile.get("kcal_target"):
        target_kcal = int(profile["kcal_target"])

    elif profile:
        target_kcal = calculate_daily_target(profile)

    else:
        target_kcal = int(day_rec.get('target_kcal', DEFAULT_DAILY_TARGET_KCAL))


    eaten_kcal = sum_food_kcal(day_rec)
    burned_kcal = sum_activity_kcal(day_rec)

    netto_kcal = eaten_kcal - burned_kcal
    balance = netto_kcal - target_kcal

    remaining_kcal = max(target_kcal - netto_kcal, 0)


    # dashboard
    refs['remaining_big'].set_text(f'{remaining_kcal} kcal over')

    refs['progress'].set_value(
        min(max(netto_kcal / target_kcal, 0), 1) if target_kcal else 0
    )

    refs['netto_val'].set_text(str(netto_kcal))
    refs['eaten_val'].set_text(str(eaten_kcal))
    refs['burned_val'].set_text(str(burned_kcal))
    refs['target_val'].set_text(str(target_kcal))


    if 'balance_badge' in refs:
        if balance <= 0:
            refs['balance_badge'].set_text(f'{balance:+} kcal t.o.v. dagdoel')
            refs['balance_badge'].classes(
                replace='w-full rounded-xl p-3 bg-green-100 text-green-900 text-sm'
            )
        else:
            refs['balance_badge'].set_text(f'{balance:+} kcal boven dagdoel')
            refs['balance_badge'].classes(
                replace='w-full rounded-xl p-3 bg-orange-100 text-orange-900 text-sm'
            )

    if 'coach_line' in refs:
        refs['coach_line'].set_text(
            coach_line(eaten=eaten_kcal, burned=burned_kcal, net=netto_kcal, target=target_kcal)
        )

    if 'peet_coach' in refs:
        analysis = analyze_day(day_rec)
        refs['peet_coach'].set_text(
            coach_advice(analysis['net'], target_kcal)
        )


    # vandaag
    refs['today_food_col'].clear()
    refs['today_activity_col'].clear()

    food_items = day_rec.get('food_items', [])
    activity_items = day_rec.get('activity_items', [])

    if food_items:
        with refs['today_food_col']:
            ui.label('Eten').classes('text-base font-semibold')

            for item in food_items:
                with ui.row().classes('w-full items-center justify-between gap-2'):

                    ui.label(
                        f"• {item.get('product','?')} | {item.get('amount',0)} {item.get('unit','')} | {item.get('kcal',0)} kcal"
                    ).classes('text-sm')

                    btn = ui.button(
                        '❌',
                        on_click=lambda item_id=item['id']: delete_food(item_id)
                    ).props('flat dense').classes('text-xs')

                    if day_closed:
                        btn.props('disable')

    with refs['today_activity_col']:
        ui.label('Beweging').classes('text-base font-semibold')

        for item in activity_items:
            with ui.row().classes('w-full items-center justify-between gap-2'):

                ui.label(
                    f"{item.get('activity','?')} | {item.get('duration_min',0)} min | {item.get('kcal',0)} kcal"
                ).classes('text-sm')

                ui.button(
                    '❌',
                    on_click=lambda item_id=item['id']: delete_activity(item_id)
                ).props('flat dense').classes('text-xs')

    refs['today_totals'].set_text(
        '' if not (food_items or activity_items)
        else f"Totaal gegeten: {sum_food_kcal(day_rec)} kcal | Totaal bewogen: {sum_activity_kcal(day_rec)} kcal"
    )

    # ------------------------------------------------------------
    # recente producten van vandaag
    # ------------------------------------------------------------

    recent_products = []
    seen = set()

    food_items = day_rec.get('food_items', [])

    for item in reversed(food_items):

        name = item.get('product')

        if not name:
            continue

        if name in seen:
            continue

        recent_products.append(name)
        seen.add(name)

        if len(recent_products) >= 5:
            break

    day_log = load_day_log()

    for i in range(1, 7):
        d = today_dt - timedelta(days=i)
        key = d.isoformat()
        day = day_log.get(key)

        if not day:
            continue

        for item in reversed(day.get('food_items', [])):

            name = item.get('product')

            if name and name not in seen:
                recent_products.append(name)
                seen.add(name)

            if len(recent_products) >= 5:
                break

        if len(recent_products) >= 5:
            break


    refs['recent_row'].clear()


    if not recent_products:

        with refs['recent_row']:
            ui.label('Nog geen recente producten.').classes('text-sm text-gray-500')

    else:

        with refs['recent_row']:

            for name in recent_products:

                btn = ui.button(name).props('outline')

                btn.on_click(lambda e, n=name: add_recent_product(n))

                if day_closed:
                    btn.props('disable')

    # pending product / resolver
    refs['pending_product_box'].clear()

    pending_choice = app_state.get('pending_product_choice')
    pending_new = app_state.get('pending_new_product')

    if pending_choice:
        with refs['pending_product_box']:
            ui.label(
                f"Ik vond meerdere producten voor '{pending_choice['name']}'. Kies de juiste:"
            ).classes('text-sm text-orange-700')

            for option in pending_choice.get('options', []):
                label = option.get('name') or option.get('label') or '?'
                ui.button(
                    label,
                    on_click=lambda product_id=option.get('id'): choose_pending_product(product_id)
                ).props('outline').classes('w-full justify-start')

            with ui.row().classes('gap-2'):
                ui.button(
                    'Nieuw product maken',
                    on_click=create_new_product_from_choice
                ).props('color=primary')

                ui.button(
                    'Annuleren',
                    on_click=cancel_pending_product_choice
                ).props('outline')

    elif pending_new:
        with refs['pending_product_box']:
            ui.label(
                f"Product '{pending_new['name']}' staat niet in de database."
            ).classes('text-sm text-orange-700')

            refs['pending_unit_choice'] = ui.radio(
                ['per stuk', 'per 250 ml', 'per 100 gram'],
                value='per 100 gram'
            ).props('inline')

            with ui.row().classes('gap-2'):
                ui.button(
                    f"De app vult '{pending_new['name']}' in",
                    on_click=fill_pending_product_with_ai
                ).props('color=primary')

                ui.button(
                    'Annuleren',
                    on_click=cancel_pending_product
                ).props('outline')

    # recipe voorstel
    pending_recipe = app_state.get('pending_recipe')

    if 'recipe_box' in refs:

        refs['recipe_box'].clear()

        if pending_recipe:

            with refs['recipe_box']:

                ui.label(pending_recipe['product']).classes('text-base font-semibold')
                ui.label(f"{pending_recipe['kcal']} kcal").classes('text-sm')

                meta = pending_recipe.get('meta', {})
                ingredients = meta.get('ingredients', [])
                instructions = meta.get('instructions', [])
                note = meta.get('note', '')

                # ingrediënten
                if ingredients:
                    with ui.expansion('Ingrediënten'):
                        for ing in ingredients:
                            ui.label(f"• {ing}").classes('text-sm')

                # bereiding
                if instructions:
                    with ui.expansion('Bereiding'):
                        for step in instructions:
                            ui.label(step).classes('text-sm')

                # note
                if note:
                    ui.label(note).classes('text-sm text-gray-600')

                # knoppen
                with ui.row().classes('gap-2'):

                    btn_accept = ui.button(
                        '✅ Voer op als gegeten',
                        on_click=accept_recipe
                    ).props('color=primary')

                    btn_reject = ui.button(
                        '❌ Verwerp',
                        on_click=reject_recipe
                    ).props('outline')

                    if day_closed:
                        btn_accept.props('disable')
                        btn_reject.props('disable')
    # dag status
    if 'day_status' in refs:
        refs['day_status'].set_text(
            'Deze dag is afgesloten. Nieuwe invoer is uitgeschakeld.' if day_closed else ''
        )

    # gewicht
    refresh_weight_chart()


def refresh_weight_chart() -> None:
    refs['weight_box'].clear()
    day_log = load_day_log()
    weights = []
    dates = []

    for d in sorted(day_log.keys()):
        data = day_log[d]
        if 'weight' in data and data['weight'] is not None:
            dates.append(d)
            weights.append(data['weight'])

    with refs['weight_box']:
        if weights:
            for d, w in zip(dates, weights):
                ui.label(f'{d}: {w} kg').classes('text-sm')
        else:
            ui.label('Nog geen gewichtsdata beschikbaar.').classes('text-sm text-gray-500')

# ============================================================
# ACTIONS
# ============================================================
def set_active_tab(name: str) -> None:
    app_state['active_tab'] = name

def on_change_selected_date(e) -> None:
    selected = e.value
    if isinstance(selected, date):
        app_state['selected_date'] = selected.isoformat()
    else:
        app_state['selected_date'] = str(selected)
    ensure_day(app_state['selected_date'])
    refresh_ui()

def on_change_target_kcal(e) -> None:
    day_rec = ensure_day(app_state['selected_date'])
    day_rec['target_kcal'] = int(e.value)
    save_data()
    refresh_ui()

def process_quick_food_input(text: str) -> None:

    day_rec = ensure_day(app_state['selected_date'])

    # ------------------------------------------------------------
    # Stap 1 — invoer normaliseren
    # ------------------------------------------------------------

    text = text.lower().replace(",", "+")
    text = text.replace("  ", " ").strip()

    raw_entries = []

    for part in text.split("+"):
        part = part.strip()
        if not part:
            continue

        matches = re.findall(r'\d+(?:[.,]\d+)?\s+[^\d+]+', part)

        if matches:
            raw_entries.extend(matches)
        else:
            raw_entries.append(part)

    entries = [e.strip() for e in raw_entries if e.strip()]

    # ------------------------------------------------------------
    # Stap 2 — entries verwerken
    # ------------------------------------------------------------

    for entry in entries:

        match = re.match(r'(\d+(?:[.,]\d+)?)\s+(.+)', entry)

        if match:
            amount = float(match.group(1).replace(',', '.'))
            product_text = match.group(2).strip()
        else:
            amount = None
            product_text = entry.strip()

        results = search_products(product_text) or []
        search = product_text.lower()

        exact_match = None

        # 1. exacte naam
        for r in results:
            name = (r.get('name') or '').lower()
            if name == search:
                exact_match = r
                break

        # 2. alias exact
        if not exact_match:
            for r in results:
                raw_aliases = r.get('alias', [])
                if isinstance(raw_aliases, str):
                    raw_aliases = [raw_aliases]
                aliases = [a.lower() for a in raw_aliases]
                if search in aliases:
                    exact_match = r
                    break

        # 3. duidelijke prefix match
        if not exact_match:
            starts_with_matches = []
            for r in results:
                name = (r.get('name') or '').lower()
                if name.startswith(search):
                    starts_with_matches.append(r)

            if len(starts_with_matches) == 1:
                exact_match = starts_with_matches[0]
            elif len(starts_with_matches) > 1:
                app_state['pending_product_choice'] = {
                    'name': product_text,
                    'amount': amount,
                    'options': starts_with_matches[:5],
                }
                refresh_ui()
                return

        # 4. zoekterm zit in naam
        if not exact_match:
            contains_matches = []
            for r in results:
                name = (r.get('name') or '').lower()
                if search in name:
                    contains_matches.append(r)

            if len(contains_matches) == 1:
                exact_match = contains_matches[0]
            elif len(contains_matches) > 1:
                app_state['pending_product_choice'] = {
                    'name': product_text,
                    'amount': amount,
                    'options': contains_matches[:5],
                }
                refresh_ui()
                return

        # 5. geen product gevonden
        if not exact_match:
            app_state['pending_new_product'] = {
                'name': product_text,
                'amount': amount,
            }
            refresh_ui()
            return

        add_food_item_to_day(day_rec, exact_match, amount)

    save_data()
    refs['quick_input'].value = ''
    refresh_ui()
    safe_notify('Product(en) toegevoegd', 'positive')

def accept_recipe() -> None:

    day_rec = ensure_day(app_state['selected_date'])
    pending = app_state.get('pending_recipe')

    if not pending:
        return

    day_rec['food_items'].insert(0, pending)

    app_state['pending_recipe'] = None
    app_state['active_tab'] = 'today'

    save_data()
    refresh_ui()


def reject_recipe() -> None:

    app_state['pending_recipe'] = None
    app_state['active_tab'] = 'input'

    refresh_ui()

def quick_add() -> None:
    text = refs['quick_input'].value or ''
    if not text.strip():
        safe_notify('Voer iets in.')
        return
    process_quick_food_input(text)

def cancel_pending_product() -> None:
    app_state['pending_new_product'] = None
    refresh_ui()

def cancel_pending_product_choice() -> None:
    app_state['pending_product_choice'] = None
    refresh_ui()


def choose_pending_product(product_id: str) -> None:
    pending = app_state.get('pending_product_choice')
    if not pending:
        return

    day_rec = ensure_day(app_state['selected_date'])

    selected_product = None
    for p in pending.get('options', []):
        if str(p.get('id')) == str(product_id):
            selected_product = p
            break

    if not selected_product:
        safe_notify('Gekozen product niet gevonden.', 'warning')
        return

    add_food_item_to_day(day_rec, selected_product, pending.get('amount'))

    app_state['pending_product_choice'] = None

    save_data()
    refresh_ui()
    safe_notify(f"Product '{selected_product.get('name', '?')}' toegevoegd", 'positive')


def create_new_product_from_choice() -> None:
    pending = app_state.get('pending_product_choice')
    if not pending:
        return

    app_state['pending_new_product'] = {
        'name': pending.get('name'),
        'amount': pending.get('amount'),
    }

    app_state['pending_product_choice'] = None
    refresh_ui()

def fill_pending_product_with_ai() -> None:
    pending = app_state.get('pending_new_product')
    if not pending:
        return
    unit_choice = refs['pending_unit_choice'].value or 'per 100 gram'
    try:
        new_product = ai_build_product(product_name=pending['name'], unit_choice=unit_choice)
        ok, result = add_product(new_product)
        if not ok:
            safe_notify(str(result), 'warning')
            return
        saved_product = result
        global PRODUCTS
        PRODUCTS = load_products()

        day_rec = ensure_day(app_state['selected_date'])
        add_food_item_to_day(day_rec, saved_product, pending.get('amount') or saved_product.get('std_portion', 1))
        save_data()
        app_state['pending_new_product'] = None
        safe_notify(f"Product '{saved_product['name']}' toegevoegd aan database en daglog.", 'positive')
        refresh_ui()
    except Exception as e:
        safe_notify(f'De app kon product niet invullen: {e}', 'negative')

def add_recent_product(name: str) -> None:
    day_rec = ensure_day(app_state['selected_date'])
    p = next((x for x in PRODUCTS if x.get('name') == name or x.get('label') == name), None)
    if not p:
        safe_notify('Product niet gevonden', 'warning')
        return
    amount = float(p.get('std_portion') or p.get('default_portion_g') or 100)
    add_food_item_to_day(day_rec, p, amount)
    save_data()
    refresh_ui()

def add_selected_food() -> None:
    day_rec = ensure_day(app_state['selected_date'])
    selected_label = refs['food_select'].value
    amount = float(refs['food_amount'].value or 0)
    if not selected_label:
        safe_notify('Kies eerst een product.')
        return
    p = next((x for x in PRODUCTS if x.get('name') == selected_label or x.get('label') == selected_label), None)
    if not p:
        safe_notify('Product niet gevonden', 'warning')
        return
    add_food_item_to_day(day_rec, p, amount)
    save_data()
    safe_notify(f"{p.get('name', selected_label)} toegevoegd", 'positive')
    refresh_ui()

def add_activity() -> None:
    day_rec = ensure_day(app_state['selected_date'])
    activity = refs['activity_select'].value
    duration = int(refs['activity_duration'].value or 0)
    garmin_kcal = int(refs['activity_garmin'].value or 0)

    if not activity:
        safe_notify('Kies een activiteit.')
        return

    if garmin_kcal > 0:
        kcal = int(garmin_kcal)
    else:
        if duration <= 0:
            safe_notify('Vul een geldige duur in.', 'warning')
            return
        weight = get_current_weight()
        met = ACTIVITY_MET[activity]
        hours = duration / 60
        kcal = int(met * weight * hours * 0.8)

    day_rec['activity_items'].append({
        'id': str(uuid.uuid4()),
        'activity': str(activity),
        'duration_min': int(duration),
        'kcal': int(kcal),
        'timestamp': datetime.now().isoformat(),
    })
    save_data()
    safe_notify(f'{activity} toegevoegd ({kcal} kcal)', 'positive')
    refresh_ui()

def delete_food(item_id: str) -> None:
    day_rec = ensure_day(app_state['selected_date'])
    day_rec['food_items'] = [x for x in day_rec.get('food_items', []) if x.get('id') != item_id]
    save_data()
    refresh_ui()

def delete_activity(item_id: str) -> None:
    day_rec = ensure_day(app_state['selected_date'])
    day_rec['activity_items'] = [x for x in day_rec.get('activity_items', []) if x.get('id') != item_id]
    save_data()
    refresh_ui()

async def generate_recipe(meal_type: str) -> None:

    print("START GENERATE RECIPE")

    day_rec = ensure_day(app_state['selected_date'])
    target_kcal = int(day_rec.get('target_kcal', DEFAULT_DAILY_TARGET_KCAL))

    eaten_kcal = sum_food_kcal(day_rec)
    burned_kcal = sum_activity_kcal(day_rec)

    remaining_kcal = target_kcal - eaten_kcal + burned_kcal
    if remaining_kcal < 0:
        remaining_kcal = 0

    # run blocking code in thread
    recipe = await ui.run.io_bound(
        generate_recipe_item,
        meal_type=meal_type,
        program=day_rec.get('program', 'Paars'),
        remaining_kcal=remaining_kcal,
        target_kcal=target_kcal,
        eaten_kcal=eaten_kcal,
        burned_kcal=burned_kcal,
    )

    print("RECIPE GENERATED:", recipe)

    app_state['pending_recipe'] = recipe
    app_state['active_tab'] = 'input'

    refresh_ui()

async def generate_recipe(meal_type: str) -> None:

    print("START GENERATE RECIPE")

    day_rec = ensure_day(app_state['selected_date'])
    target_kcal = int(day_rec.get('target_kcal', DEFAULT_DAILY_TARGET_KCAL))

    eaten_kcal = sum_food_kcal(day_rec)
    burned_kcal = sum_activity_kcal(day_rec)

    remaining_kcal = target_kcal - eaten_kcal + burned_kcal
    if remaining_kcal < 0:
        remaining_kcal = 0

    # run blocking functie in thread
    recipe = await asyncio.to_thread(
        generate_recipe_item,
        meal_type,
        day_rec.get('program', 'Paars'),
        remaining_kcal,
        target_kcal,
        eaten_kcal,
        burned_kcal
    )

    print("RECIPE GENERATED:", recipe)

    app_state['pending_recipe'] = recipe
    app_state['active_tab'] = 'input'

    refresh_ui()

def reject_recipe() -> None:
    app_state['pending_recipe'] = None
    app_state['active_tab'] = 'input'
    refresh_ui()

def close_day() -> None:
    day_rec = ensure_day(app_state['selected_date'])
    day_rec['closed'] = True
    save_data()
    safe_notify('Dag vastgezet.', 'positive')
    refresh_ui()

def save_weight() -> None:
    value = float(refs['weight_input'].value or 0.0)
    today_dt = date.today()
    week_key = f'{today_dt.isocalendar().year}-{today_dt.isocalendar().week}'
    day_log = load_day_log()
    today_key = today_dt.isoformat()
    if today_key not in day_log:
        day_log[today_key] = {'food_items': [], 'weight': None}
    day_log[today_key]['weight'] = value
    save_day_log(day_log)

    app_state['weight_log'].append({
        'date': today_dt.isoformat(),
        'week': week_key,
        'weight': float(value),
    })
    app_state['last_weight_prompt_week'] = week_key
    safe_notify('Gewicht opgeslagen.', 'positive')
    refresh_ui()

def show_weight_history() -> None:
    refs['weight_dialog'].open()

# ============================================================
# INIT STATE
# ============================================================

app_state['days'] = load_data()
ensure_day(app_state['selected_date'])

# ============================================================
# UI
# ============================================================

ui.page_title('Peet Coach')

with ui.column().classes(
    'w-full p-4 gap-4 min-h-screen overflow-y-auto pb-24'
):

    # ------------------------------------------------------------
    # HEADER
    # ------------------------------------------------------------

    with ui.row().classes('w-full items-center justify-between'):

        ui.label('Peet Coach').classes('text-2xl font-bold')

        ui.button(
            '📅',
            on_click=lambda: refs['date_dialog'].open()
        ).props('flat round')


    with ui.column():

        refs['day_title'] = ui.label('').classes('text-lg font-semibold')
        refs['day_sub'] = ui.label('').classes('text-xs text-gray-500')


    with ui.dialog() as refs['date_dialog'], ui.card():

        refs['date_picker'] = ui.date(
            value=date.fromisoformat(app_state['selected_date']),
            on_change=on_change_selected_date
        ).props('mask="YYYY-MM-DD"')

        ui.button(
            'Sluiten',
            on_click=refs['date_dialog'].close
        )

    # ------------------------------------------------------------
    # TABS
    # ------------------------------------------------------------

    with ui.tabs().classes('w-full hidden') as refs['tabs']:

        refs['tab_today'] = ui.tab('Vandaag')
        refs['tab_input'] = ui.tab('Invoer')
        refs['tab_coach'] = ui.tab('Coach')
        refs['tab_settings'] = ui.tab('Instellingen')


    refs['tabs'].on_value_change(
        lambda e: app_state.update({
            'active_tab':
                'input' if e.value == refs['tab_input']
                else 'coach' if e.value == refs['tab_coach']
                else 'settings' if e.value == refs['tab_settings']
                else 'today'
        })
    )


    # ------------------------------------------------------------
    # TAB PANELS
    # ------------------------------------------------------------

    with ui.tab_panels(refs['tabs'], value=refs['tab_today']).classes('w-full pb-24'):

        # =========================================================
        # TAB 1 — VANDAAG
        # =========================================================
        with ui.tab_panel(refs['tab_today']):

            profile = load_profile() or {}

            calculated_kcal = DEFAULT_DAILY_TARGET_KCAL

            if profile.get("kcal_target"):
                daily_goal = profile["kcal_target"]
            else:
                daily_goal = calculated_kcal

            with ui.card().classes('w-full'):
                ui.label('Vandaag').classes('text-lg font-semibold')

                refs['today_food_col'] = ui.column().classes('w-full gap-2')
                refs['today_activity_col'] = ui.column().classes('w-full gap-2')

                refs['today_totals'] = ui.label('').classes('text-sm font-semibold')

            with ui.card().classes('w-full gap-2'):

                ui.label('Dagprogress').classes('text-lg font-semibold')

                refs['remaining_big'] = ui.label('').classes(
                    'text-2xl font-bold text-purple-900 text-center'
                )

                refs['progress'] = ui.linear_progress(
                    value=0,
                    show_value=False,
                    color='purple'
                ).classes('w-full h-3 rounded')

                refs['progress'] = ui.linear_progress(
                    value=0,
                    show_value=False,
                    color='purple'
                ).classes('w-full h-3 rounded')

                refs['progress_label'] = ui.label('').classes(
                    'text-sm text-gray-600 text-center'
                )

                with ui.grid(columns=2).classes('w-full max-w-[420px] mx-auto gap-y-3 text-base mt-2'):

                    ui.label('Gegeten')
                    refs['eaten_val'] = ui.label('').classes('text-right')

                    ui.label('Bewogen')
                    refs['burned_val'] = ui.label('').classes('text-right')

                    ui.label('Dagdoel')
                    refs['target_val'] = ui.label('').classes('text-right')

                    ui.label('Netto')
                    refs['netto_val'] = ui.label('').classes('text-right')

        # =========================================================
        # TAB 2 — INVOER
        # =========================================================
        with ui.tab_panel(refs['tab_input']):

            # -----------------------------------------------------
            # SNELLE INVOER
            # -----------------------------------------------------
            with ui.card().classes('w-full'):

                ui.label('⚡ Snelle invoer').classes('text-lg font-semibold')

                with ui.row().classes('w-full items-center gap-2'):

                    refs['quick_input'] = ui.input(
                        placeholder='bijv: 150 kip + 200 kwark'
                    ).classes('grow')

                    refs['quick_add_btn'] = ui.button(
                        '+',
                        on_click=quick_add
                    ).props('round color=primary')

                ui.label('Recent gegeten').classes(
                    'text-sm font-semibold text-gray-700'
                )

                refs['recent_row'] = ui.row().classes('w-full gap-2')
                refs['pending_product_box'] = ui.column().classes('w-full gap-2')


            # -----------------------------------------------------
            # ETEN TOEVOEGEN
            # -----------------------------------------------------
            with ui.card().classes('w-full'):

                ui.label('➕ Eten toevoegen').classes('text-lg font-semibold')

                product_names = sorted([
                    p.get('name') or p.get('label')
                    for p in PRODUCTS
                    if p.get('name') or p.get('label')
                ])

                refs['food_select'] = ui.select(
                    options=product_names,
                    with_input=True,
                    label='Product'
                ).classes('w-full')

                refs['food_amount'] = ui.number(
                    label='Hoeveelheid',
                    value=100.0,
                    min=0.0,
                    max=2000.0,
                    step=5.0
                ).classes('w-full')

                refs['food_select_btn'] = ui.button(
                    'Toevoegen',
                    on_click=add_selected_food
                ).props('color=primary')


            # -----------------------------------------------------
            # RECEPT VOORSTEL
            # -----------------------------------------------------
            with ui.card().classes('w-full'):

                ui.label('🍽 Recept voorstel').classes('text-lg font-semibold')

                with ui.row().classes('gap-2'):

                    refs['recipe_lunch_btn'] = ui.button(
                        'Genereer lunch',
                        on_click=lambda e: generate_recipe('Lunch')
                    ).props('color=primary')

                    refs['recipe_dinner_btn'] = ui.button(
                        'Genereer diner',
                        on_click=lambda e: generate_recipe('Diner')
                    ).props('outline')

                refs['recipe_box'] = ui.column().classes('w-full gap-2')


            # -----------------------------------------------------
            # BEWEGING TOEVOEGEN
            # -----------------------------------------------------
            with ui.card().classes('w-full'):

                ui.label('➕ Beweging toevoegen').classes('text-lg font-semibold')

                refs['activity_select'] = ui.select(
                    options=list(ACTIVITY_MET.keys()),
                    label='Activiteit'
                ).classes('w-full')

                refs['activity_duration'] = ui.number(
                    label='Duur (minuten)',
                    value=0,
                    min=0,
                    step=5
                ).classes('w-full')

                refs['activity_garmin'] = ui.number(
                    label='Of voer Garmin kcal direct in',
                    value=0,
                    min=0,
                    step=10
                ).classes('w-full')

                refs['activity_add_btn'] = ui.button(
                    'Toevoegen',
                    on_click=add_activity
                ).props('color=primary')


        # =========================================================
        # TAB 3 — COACH
        # =========================================================
        with ui.tab_panel(refs['tab_coach']):

            with ui.card().classes('w-full'):
                ui.label('Peet coach').classes('text-lg font-semibold')
                refs['peet_coach'] = ui.label('')
                refs['coach_target'] = ui.label('').classes('text-sm text-gray-500')

            with ui.card().classes('w-full'):
                ui.label('Honger verwachting').classes('text-lg font-semibold')
                refs['hunger'] = ui.label('')
                refs['hours_since'] = ui.label('').classes('text-sm text-gray-500')

            with ui.card().classes('w-full'):
                ui.label('Week koers').classes('text-lg font-semibold')
                refs['week_balance'] = ui.label('')
                refs['week_note'] = ui.label('').classes('text-sm text-gray-500')


        # =========================================================
        # TAB 4 — INSTELLINGEN
        # =========================================================
        with ui.tab_panel(refs['tab_settings']):

            profile = load_profile() or {}

            with ui.card().classes('w-full'):

                ui.label('Persoonlijk profiel').classes('text-lg font-semibold')

                refs['profile_sex'] = ui.select(
                    options=['male', 'female'],
                    label='Geslacht',
                    value=profile.get('sex', 'male')
                ).classes('w-full')

                refs['profile_age'] = ui.number(
                    label='Leeftijd',
                    value=profile.get('age', 63)
                ).classes('w-full')

                refs['profile_height'] = ui.number(
                    label='Lengte (cm)',
                    value=profile.get('height', 186)
                ).classes('w-full')

                refs['profile_weight'] = ui.number(
                    label='Huidig gewicht (kg)',
                    value=profile.get('current_weight', 110)
                ).classes('w-full')

                refs['profile_target'] = ui.number(
                    label='Streefgewicht (kg)',
                    value=profile.get('target_weight', 80)
                ).classes('w-full')

                refs['profile_weeks'] = ui.number(
                    label='Aantal weken',
                    value=profile.get('weeks_to_goal', 16)
                ).classes('w-full')

                refs['profile_kcal_target'] = ui.number(
                    label='Dagelijkse calorie doel',
                    value=profile.get('kcal_target', None)
                ).classes('w-full')

                ui.label('Leeg laten = advies van Peet Coach').classes('text-xs text-gray-500')

                ui.button(
                    'Opslaan',
                    on_click=save_profile_from_ui
                ).props('color=primary')


    # ------------------------------------------------------------
    # BOTTOM NAVIGATION
    # ------------------------------------------------------------

    refs['nav_buttons'] = {}

    with ui.row().classes(
        'fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg justify-around items-center p-3'
    ):

        refs['nav_buttons']['today'] = ui.button('🍽️',
            on_click=lambda: [
                refs['tabs'].set_value(refs['tab_today']),
                update_nav_style('today')
            ]
        ).props('flat round').classes('text-2xl')

        refs['nav_buttons']['input'] = ui.button('➕',
            on_click=lambda: [
                refs['tabs'].set_value(refs['tab_input']),
                update_nav_style('input')
            ]
        ).props('flat round').classes('text-2xl')

        refs['nav_buttons']['coach'] = ui.button('🧠',
            on_click=lambda: [
                refs['tabs'].set_value(refs['tab_coach']),
                update_nav_style('coach')
            ]
        ).props('flat round').classes('text-2xl')

        refs['nav_buttons']['settings'] = ui.button('👤',
            on_click=lambda: [
                refs['tabs'].set_value(refs['tab_settings']),
                update_nav_style('settings')
            ]
        ).props('flat round').classes('text-2xl')
    # ------------------------------------------------------------
    # weight dialog
    # ------------------------------------------------------------

    with ui.dialog() as refs['weight_dialog'], ui.card().classes('w-full w-full'):

        ui.label('Gewichtsverloop').classes('text-lg font-semibold')

        refs['weight_box'] = ui.column().classes('w-full gap-1')

        ui.button(
            'Sluiten',
            on_click=refs['weight_dialog'].close
        ).props('outline')


def safe_refresh():
    try:
        refresh_ui()
    except:
        pass

update_nav_style('today')

ui.timer(0.1, safe_refresh, once=True)

import os
port = int(os.environ.get("PORT", 8080))

ui.run(
    host="0.0.0.0",
    port=port
)