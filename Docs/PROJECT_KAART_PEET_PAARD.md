# Peet Paars – Projectkaart

## Project
Peet Paars is een eenvoudige energie-coach app gebouwd in Streamlit.

Het systeem helpt dagelijks inzicht te krijgen in:

- calorie-inname
- energieverbruik
- netto energiebalans
- gewichtsverloop per week

De app vermijdt dieetcomplexiteit en focust op één waarheid:

energie balans = gegeten − bewogen


---

# Architectuur Overzicht

Streamlit UI
│
├── Dagstore (session_state["days"])
│     ├── food_items
│     ├── activity_items
│     ├── target_kcal
│     └── closed
│
├── Energie Engine
│     ├── sum_food_kcal()
│     ├── sum_activity_kcal()
│     └── netto = gegeten − bewogen
│
├── FOOD_LIBRARY
│     ├── food_library_generated_vX.py
│     ├── calc_food_kcal()
│     └── alias matching
│
├── Activiteiten
│     └── ACTIVITY_KCAL_PER_MIN
│
└── Recept Engine
      └── generate_recipe_item()


---

# Dagstore structuur

Alle data staat in:

st.session_state["days"]

Structuur:

date
 └── day_rec
      ├── food_items
      ├── activity_items
      ├── target_kcal
      └── closed


---

# Food Item structuur

{
  id
  product
  amount
  unit
  kcal
  timestamp
}

optioneel:

meta


---

# Activity Item structuur

{
  id
  activity
  duration_min
  kcal
  timestamp
}


---

# Energie berekening

sum_food_kcal()
sum_activity_kcal()

netto_kcal = gegeten − bewogen


---

# FOOD_LIBRARY systeem

Externe database:

food_library_generated_vX.py

Product structuur:

{
  label
  unit
  kcal_per_100g
  kcal_per_100ml
  kcal_per_piece
  kcal_per_tbsp
  std_portion
  alias
}

Ondersteunde units:

- gram
- ml
- cl
- eetlepel
- stuk


---

# Activiteiten systeem

ACTIVITY_KCAL_PER_MIN

Voorbeeld:

wandelen = 4  
fietsen = 8  
hardlopen = 10  
spinnen = 9  


Berekening:

kcal = minuten × factor


---

# Gewicht tracking

Gewicht wordt 1x per week gevraagd.

Instelling:

WEIGH_DAY = woensdag

Opslag:

session_state["weight_log"]

Structuur:

{
  date
  week
  weight
}


---

# Recept Engine

generate_recipe_item()

Output:

food_item

waardoor recepten direct compatibel zijn met het systeem.


---

# UX structuur

Schermen:

1. Dagselectie
2. Hero energiekaart
3. Eten toevoegen
4. Beweging toevoegen
5. Recept voorstellen
6. Dag overzicht
7. Dag afsluiten
8. Gewichtsverloop


---

# Canon instellingen

DEFAULT_DAILY_TARGET_KCAL = 1800

WEIGH_DAY = woensdag


---

# Stabiliteitsregels

Deze onderdelen mogen niet zomaar gewijzigd worden:

- dagstore structuur
- food_item structuur
- activity_item structuur
- kcal berekening
- FOOD_LIBRARY interface


---

# Bouwafspraken

## Rol Peter

Product Owner

- bepaalt UX
- bepaalt functionaliteit
- test dagelijks gebruik


## Rol ChatGPT

Architect / Engineer

- bewaakt systeemstructuur
- bouwt robuuste code
- voorkomt technische schuld
- vertaalt wensen naar veilige implementaties


Acteerregel:

Peter = gebruiker  
ChatGPT = engineer


---

# Baken

Peet Paars – STABIELE BASIS v1.0  
Datum: 5 maart 2026

Stabiele onderdelen:

- energie engine
- food library
- activiteitensysteem
- dag afsluiten
- weekgewicht


---

# Volgende fase

Peet Paars – UX versnelling v1.1

Gepland:

1. Snelle invoer
   voorbeeld:

   250 aardappel  
   150 kip  
   10 olie

2. Slimme productzoeker

3. Excel → FOOD_LIBRARY generator


---

# Projectstructuur

peet-paars
│
├── app_new.py
├── food_library_generated_vX.py
│
├── docs
│   ├── PROJECT_KAART_PEET_PAARS.md
│   └── BAKENS.md
│
└── data
    └── food_library.xlsx