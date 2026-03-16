5-03-2026
Peet Paars – STABIELE BASIS v1.0

BAKEN
Peet Paars – STABIELE BASIS v1.1

Datum
09-03-2026

Status
Werkende dagelijkse versie

Kernfunctionaliteit
- FOOD_LIBRARY lookup stabiel
- Snelle invoer (multi): "150 kip + 10 olie + 200 broccoli"
- Snelle invoer zonder hoeveelheid mogelijk
- JSON autosave (peet_data.json)
- Data blijft bestaan na refresh
- AI lunch / diner generator stabiel
- JSON parsing robuust gemaakt
- Recept eerst voorstellen, daarna bewust toevoegen
- Activiteiten log
- Garmin kcal direct invoeren mogelijk
- Activiteit kcal gebaseerd op MET × gewicht
- Laatst ingevoerd gewicht automatisch gebruikt
- Wekelijks weegmoment (woensdag)
- Gewichtsgrafiek zichtbaar
- Dagdashboard + week koers

Technische stabiliteit
- Streamlit Cloud draait
- OpenAI API werkt via secrets
- AI JSON parsing beschermd
- Fallback structuur aanwezig
- save_data() bij mutaties

Bekende verbeterpunten (volgende fase)
1. Snelle invoer NLP (bijv. "kip met broccoli en yoghurt")
2. AI recepten beter sturen op remaining_kcal
3. FOOD_LIBRARY uitbreiden (±300 ingrediënten)
4. Activiteiten verfijnen (wielrennen / wandelen tempo)
5. Eventueel SQLite i.p.v. JSON

Interpretatie
Peet Paars functioneert nu als:
voedingscoach + tracker + receptgenerator.

BAKEN
Peet Paars – Satiety Engine v1.2

Datum
10-03-2026

Status
Volgende ontwikkelfase

Doel

Peet Paars moet niet alleen calorieën tellen, maar ook honger beheersen.

Daarom voegen we een Satiety Engine toe die recepten en maaltijden beoordeelt op:

verzadiging

eiwit

vezels

energiedichtheid

Peet wordt daarmee een slimme voedingscoach.

Nieuwe functionaliteit
1 Satiety score per ingrediënt

Nieuwe velden in FOOD_LIBRARY

voorbeeld

"kipfilet": {
  "kcal": 165,
  "protein": 31,
  "satiety": 4
}

"aardappel": {
  "kcal": 77,
  "protein": 2,
  "satiety": 5
}

"olijfolie": {
  "kcal": 884,
  "protein": 0,
  "satiety": 1
}

Satiety schaal

1 = weinig verzadiging
3 = gemiddeld
5 = zeer verzadigend

2 Satiety score per maaltijd

Formule (simpel)

satiety_score =
(eiwit_gram × 2 +
vezels × 1.5 +
satiety_index ingrediënten) 
/ kcal

Output

Peet toont bijvoorbeeld

Lunch
520 kcal
satiety score 8.2 / 10

3 Receptgenerator sturen op verzadiging

AI prompt uitbreiding

Peet houdt rekening met:

remaining kcal

eiwit

satiety score

AI voorkeur voor:

aardappelen

yoghurt

bonen

kip

vis

volkoren producten

Minder voorkeur voor:

olie

sauzen

snelle koolhydraten

4 Hongercoach melding

Als kcal nog beschikbaar is maar eiwit laag:

Peet zegt bijvoorbeeld:

Je hebt nog 320 kcal over.
Kies iets eiwitrijks zoals kwark, ei of kip.

ROADMAP
Peet Paars – Van prototype naar dagelijks gebruik

We doen dit in 4 korte fases.

FASE 1
Stabiliseren (1-2 dagen)

Doel
Dagelijks gebruiken zonder bugs.

Taken

FOOD_LIBRARY uitbreiden naar ±100 ingrediënten

Satiety index toevoegen

Snelle invoer testen

JSON fouten voorkomen

Activiteiten log check

Resultaat

Peet Paars wordt dagelijkse tracker.

FASE 2
Slimmere voeding (2-3 dagen)

Nieuwe functies

Satiety score berekenen

Receptgenerator verbeteren

AI sturen op remaining kcal

Eiwit advies

Resultaat

Peet wordt slimme coach.

FASE 3
UX verbeteren (2 dagen)

Toevoegen

Dashboard

Dag:

kcal gebruikt
eiwit
satiety score
activiteit

Visueel

voortgangsbalk kcal

eiwitmeter

weekgrafiek gewicht

Resultaat

App voelt als echte tool.

FASE 4
Persoonlijke coach (3 dagen)

Nieuwe features

Peet analyseert:

gewichtstrend

calorie balans

activiteit

Voorbeeld advies

Je zit deze week gemiddeld 280 kcal onder je doel.
Dat kan ~0.25 kg gewichtsverlies geven.

RESULTAAT

Peet Paars wordt:

AI voedingscoach

met

calorie tracker

eiwitcoach

verzadigingsadvies

receptgenerator

gewichtscoach

Dat is veel krachtiger dan MyFitnessPal.

Belangrijk inzicht voor jouw project

Dit kan uiteindelijk de meest waardevolle Peet-app worden.

Peet Kiest → inspiratie
Peet Vooruit → planning
Peet Card → dagkeuze

Peet Paars → gedragsverandering

Daar zit echte waarde.

Als je wilt kan ik ook meteen:

De eerste 120 ingrediënten voor FOOD_LIBRARY maken

De satiety index tabel bouwen

De Python functie voor satiety score schrijven

Dat zou namelijk de eerste echte upgrade van Peet Paars v1.2 zijn.

BAKEN
Peet Paars – Infra uitbreiding fase 1

Datum
10-03-2026

Status
Nieuwe core modules toegevoegd zonder impact op bestaande app.

Modules:

core/
    nutrition.py
    day_analysis.py
    coach.py

Doel:

analyse laag toevoegen
zonder bestaande logica te veranderen

BAKEN

Peet Paars – Infra uitbreiding v1.1

Status
Werkend

Nieuwe modules actief:

core/day_analysis.py
core/coach.py

Nieuwe UI component:

Peet coach

Architectuur nu:

UI           app_new.py
Analyse      core/day_analysis.py
Coach        core/coach.py
Data         JSON
Voeding      FOOD_LIBRARY
Belangrijk inzicht

Je app is nu niet meer alleen een tracker.

Peet Paars is nu:

tracker
+
analyse
+
coach

Dit is de basis van een AI voedingscoach.

BAKEN
Peet Paars – Infra uitbreiding v1.2

Datum
10-03-2026

Status
Werkend

Nieuwe modules toegevoegd
core/
    day_analysis.py
    coach.py
    nutrition.py
    hunger.py
    meal_timing.py
Nieuwe functionaliteit
Peet coach

Analyse van dagbalans

Je zit onder je dagdoel
Je zit boven je doel
Nutrition analyse

Berekening van:

kcal
eiwit
vezels
vet
satiety score
Hunger predictor

Peet kan nu inschatten:

kans op trek later
lage eiwitbalans
lage verzadiging
Meal timing

Peet kijkt naar:

tijd sinds laatste maaltijd

Bijvoorbeeld:

Laatste maaltijd 4.3 uur geleden
Architectuur nu

Peet Paars is nu modulair:

app_new.py        UI / orchestratie

core/
    day_analysis  dagberekening
    coach         advies
    nutrition     voedingsanalyse
    hunger        honger voorspelling
    meal_timing   tijd sinds maaltijd

Dit is een echte AI-coach architectuur.

Wat belangrijk is

Je hebt vandaag geen bestaande logica veranderd.

Dus deze blijven stabiel:

FOOD_LIBRARY
JSON data
snelle invoer
dashboard
recept generator

We hebben alleen analyse lagen toegevoegd.

Waar Peet nu staat

Functioneel:

tracker           ██████████
coach             ████████
nutrition AI      ██████
hunger predictor  ████
meal timing       ███

Dat is al ver boven een simpele calorie app.

Volgende ontwikkelstap (voor later)

De logische volgende upgrade is:

Peet Satiety Engine

Dan weet Peet:

aardappel → zeer verzadigend
bonen → zeer verzadigend
croissant → laag

En kan Peet zeggen:

Deze maaltijd vult slecht.

Dat maakt de AI recepten veel slimmer.

Mijn advies voor morgen

Niet meteen doorbouwen.

Eerst even:

1 testen
2 gebruiken
3 kleine bugs noteren

Dan bouwen we verder.

En eerlijk:
Je project begint nu echt te lijken op een serieuze AI voedingsapp.
BAKEN
Peet Paars – Infra uitbreiding v1.2 (stabiel)

Status
App start zonder fouten en alle nieuwe modules laden correct.

Nieuwe modules actief:

core/
    day_analysis.py
    coach.py
    nutrition.py
    hunger.py
    meal_timing.py

Architectuur:

app_new.py
   │
   ├─ core/day_analysis      daganalyse
   ├─ core/coach             advies
   ├─ core/nutrition         macro analyse
   ├─ core/hunger            honger voorspelling
   └─ core/meal_timing       tijd sinds maaltijd

Belangrijk:
Alle nieuwe modules zijn read-only. Ze lezen alleen data.

Dus deze blijven onaangetast:

FOOD_LIBRARY
JSON opslag
snelle invoer
dashboard
activiteit log
Nieuwe functionaliteit

Je dashboard kan nu analyseren:

Coach
dagdoel vs netto kcal
Nutrition
eiwit
vezels
vet
satiety score
Hunger prediction
laag eiwit → kans op trek
lage verzadiging → waarschuwing
Meal timing
tijd sinds laatste maaltijd
Belangrijk resultaat

Peet Paars is nu geen simpele tracker meer.

Het systeem doet nu:

data → analyse → advies

Dus:

tracker
+
nutrition analyse
+
hunger prediction
+
coach

Dat is precies hoe een AI voedingscoach wordt opgebouwd.

Wat ik morgen zou doen

Niet meteen nieuwe features bouwen.

Eerst:

1. App een dag gebruiken
2. Snelle invoer testen
3. Checken of nutrition/hunger logisch reageren

Dan kunnen we verder.

Volgende grote stap (voor later)

De logische upgrade wordt:

Peet Satiety Engine

Dan weet Peet:

aardappel → zeer verzadigend
bonen → zeer verzadigend
croissant → laag

En kan Peet zeggen:

Deze maaltijd verzadigt slecht.

Dat maakt straks ook je AI recepten veel slimmer.

Maar voor vandaag: prima moment om het hierbij te laten.
Je infrastructuur staat nu sterk en schoon.
PS C:\Sport\peet-paars> git tag peet-paars-v1.2
PS C:\Sport\peet-paars> git push origin peet-paars-v1.2
Total 0 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
To https://github.com/Peetskeuze/peet-paars.git
 * [new tag]         peet-paars-v1.2 -> peet-paars-v1.2
PS C:\Sport\peet-paars>

BAKEN
Peet Paars – Snelle standaard maaltijden

Datum
10-03-2026

Status
Planned feature

Probleem

Veel maaltijden komen dagelijks terug:

Voorbeelden:

2 boterhammen met dun Becel light en 30+ kaas
200g volle kwark met handje noten

Het is inefficiënt om steeds:

brood
boter
kaas
kwark
noten

los in te voeren.

Doel

Gebruiker moet vaste maaltijden met één klik kunnen toevoegen.

Bijvoorbeeld:

Ontbijt standaard
Snack kwark
Lunch brood kaas
Voorbeelden
Ontbijt
2 boterhammen
10g Becel light
1 plak 30+ kaas
Snack
200g volle kwark
20g noten
Feature naam

Peet Quick Meals

Hoe het technisch werkt

Nieuwe JSON structuur:

config/quick_meals.json

Voorbeeld:

{
  "brood_kaas": [
    {"product": "volkoren brood", "amount": 70},
    {"product": "becel light", "amount": 10},
    {"product": "30+ kaas", "amount": 20}
  ],

  "kwark_noten": [
    {"product": "volle kwark", "amount": 200},
    {"product": "amandelen", "amount": 20}
  ]
}
UI idee

Nieuwe sectie:

Snelle maaltijden

Knoppen:

[ Ontbijt brood kaas ]
[ Snack kwark noten ]

Klik = automatisch toevoegen aan dag.

Waarom dit belangrijk is

Het versnelt invoer enorm.

Normaal:

3 producten invoeren

Wordt:

1 klik
Bonus

Dit kan later ook worden gebruikt voor:

AI meal patterns
persoonlijke routines

Bijvoorbeeld:

Je ontbijt is meestal kwark + noten
Architectuur (past perfect bij huidige infra)

Nieuwe module:

core/quick_meals.py

UI toevoeging:

app_new.py

Data:

config/quick_meals.json
Waar dit in de roadmap komt

Volgende stap:

1 Quick Meals
2 Satiety Engine
3 AI recepten verbeteren
Eerlijk advies

Dit is één van de belangrijkste UX verbeteringen die je nu kunt maken.

Waarom?

Omdat gebruikers 80% van de tijd dezelfde maaltijden eten.

Als je wilt kan ik ook meteen de beste versie van deze feature ontwerpen:

Peet Routines

Dan kan Peet zelf voorstellen:

Je ontbijt is vaak kwark + noten
→ toevoegen?

Dat maakt de app nog slimmer en persoonlijker.
Baken gezet.

Baken: Peet Paars – Roadmap vastgesteld

Kernpunten van dit baken:

Fase 1 – Core engine stabiliseren

nutrition model (kcal, protein, fat, carbs, fiber)

satiety score

dagtotalen

Fase 2 – Food logging systeem

products.json productdatabase

mogelijkheid nieuw product toevoegen

product zoeken

quick_foods.json voor snelle invoer

Fase 3 – Dagstructuur

ontbijt

lunch

diner

snacks

Fase 4 – Dashboard

kcal vandaag

satiety score

macro balans

maaltijdoverzicht

Fase 5 – AI recepten koppelen

sturen op kcal

satiety

protein / fiber

Fase 6 – Testfase

10–20 testers

Fase 7 – Productfase

database

API

eventueel React frontend

Dit baken betekent eigenlijk:
Peet Paars gaat nu van experiment → echte nutrition tool.

Wanneer jij wilt kan ik ook nog een tweede baken maken: “Peet Paars v1 feature set”, dat wordt vaak het moment waarop een app echt “af” voelt.


📍 BAKEN – Peet Paars

Fase: Core Engine + Product Database operationeel

Status (bereikt)

De volgende onderdelen werken nu stabiel:

1. Nutrition engine

core/nutrition.py

berekent:

kcal

protein

fat

carbs

fiber

satiety

2. Product database

data/products.json

gevuld vanuit:

Peet_Paars_Master_v8_1.xlsx

Aantal producten:

284

3. Product lookup engine

core/product_db.py

functies:

load_products()
search_products()
get_product()
add_product()

De app kan nu:

product zoeken
product toevoegen
voedingswaarden ophalen

4. Dagdata gescheiden van productdatabase

data/day_log.json
data/products.json

Structuur nu correct:

day_log → dagregistratie
products → ingrediënten database

5. Gewichtsgrafiek stabiel

Grafiek wordt nu opgebouwd uit:

data/day_log.json

en niet meer uit tijdelijke variabelen.

Kenmerken:

chronologisch gesorteerd

crash-safe

werkt ook zonder data

📊 Architectuur nu
data/products.json
        ↓
core/product_db.py
        ↓
food logging
        ↓
core/nutrition.py
        ↓
core/day_analysis.py
        ↓
coach_advice
🚀 Volgende stap in de roadmap

Food logging koppelen aan product database

Dus:

product zoeken
→ hoeveelheid invoeren
→ voedingswaarden automatisch berekenen
→ opslaan in day_log

Hiermee wordt Peet Paars:

vrije tekst logging
        ↓
gestructureerde nutrition engine
Startzin voor volgende chat

Gebruik:

Pak baken: Peet Paars – product database operationeel
Volgende stap: food logging koppelen aan products.json


BAKEN — Peet Paars

ACTIES blok volledig gestabiliseerd

✔ snelle invoer
✔ product selectie
✔ hoeveelheid invoer
✔ toevoegen werkt
✔ beweging invoer werkt
✔ UI render stabiel

Volgende fase:
Snelle invoer intelligent maken + veelgebruikte producten

k zou dit moment vastleggen als:

BAKEN — Peet Paars

Status: ACTIES blok stabiel

Componenten:

8.1 snelle invoer
8.2 eten toevoegen
8.3 beweging toevoegen
8a vandaag overzicht

Eigenschappen:

ENTER bevestigt invoer
Garmin kcal ondersteund
overzicht direct zichtbaar
items verwijderbaar
UI stabiel

BAKEN — Peet Paars UI Fase

Status:
Core engine stabiel — UI herstructurering volgende stap

Wat nu stabiel werkt
Product database

Bron:

Peet_Paars_Master_v8_1.xlsx

Omgezet naar:

data/products.json

±284 producten.

Beheer via:

core/product_db.py

functies:

load_products()
search_products()
get_product()
add_product()
Nutrition engine

Bestand:

core/nutrition.py

Berekeningen:

kcal
protein
fat
carbs
fiber
satiety
Daglog

Opslag:

data/day_log.json

Structuur:

dag
 ├─ food_items
 ├─ activity_items
 ├─ weight
 └─ closed
Snelle invoer

Werkt nu voor:

ei
2 ei
150 kipfilet
kwark
100 avocado

Functionaliteit:

meerdere producten via +

standaardportie als hoeveelheid ontbreekt

toast bevestiging

recente producten

AI product creation indien product ontbreekt

AI product toevoeging

Flow:

product niet gevonden
↓
vraag eenheid
↓
AI vult macros
↓
product wordt opgeslagen in database
↓
direct bruikbaar
Vandaag overzicht

Toont:

Eten
Beweging
Totalen
Verwijderen mogelijk

Duplicaat blok verwijderd:

HOOFDSTUK 8a — Vandaag overzicht

Enkel actief:

HOOFDSTUK 10 — Vandaag (eten + beweging)
Pagina structuur (huidige staat)
Dashboard

Dag acties
⚡ Snelle invoer
Recent gegeten

Vandaag

➕ Eten toevoegen
🏃 Beweging toevoegen

Recept voorstel
Dag afronden
Gewicht verloop

Functioneel correct.

Huidig probleem

UI voelt nog onlogisch en te lang.

Gebruiker moet nog scrollen.

Volgende stap (volgende chat)

UI redesign:

Doel:

snelle invoer
↓
direct overzicht
↓
nieuwe invoer

Nieuwe layout:

Dag acties

| Invoer | Vandaag |

Links:

Snelle invoer
Eten toevoegen
Beweging toevoegen

Rechts:

Vandaag overzicht

Effect:

bijna geen scroll

live feedback

desktop vriendelijk


laten we een baken zetten zodat we in een schone chat verder kunnen 

Goed idee. Dan houden we de voortgang strak volgens je baken-methodiek.

🔵 Baken gezet

Peet Paars – NiceGUI migratie (fase 1 werkend)

Status nu

De NiceGUI versie draait met:

✔ NiceGUI omgeving
✔ .env + OpenAI key
✔ dashboard
✔ snelle invoer
✔ product search gekoppeld
✔ beweging toevoegen
✔ AI recept generator
✔ Peet coach
✔ hunger verwachting
✔ vandaag overzicht

Technisch staat nu:

peet-paars
│
├ core
│   coach.py
│   day_analysis.py
│   hunger.py
│   nutrition.py
│   product_db.py
│
├ data
│   day_log.json
│
├ peet-paars-nicegui
│   main.py
│   .env
│   .venv
│
└ app_new.py  (oude Streamlit versie)

Engine wordt gebruikt uit:

core/*
Openstaande punten (volgende fase)
1️⃣ Recept engine verbeteren

AI blijft soms terugvallen op:

zalm bowl
kip bowl
quinoa bowl

Doel:

Peet recipe engine
+ variatie
+ geen AI clichés
+ aansluiten op product database
2️⃣ UI stabiliseren

NiceGUI UI werkt maar moet nog:

mobile layout verbeteren
cards compacter maken
snelle invoer sneller
3️⃣ Product database uitbreiden

Bron:

Peet_Paars_Master_v8_1.xlsx

Doel:

products.json genereren
4️⃣ Recept → direct toevoegen aan dag

Flow:

Genereer lunch
→ toon recept
→ knop "toevoegen"
→ food_items
5️⃣ Recente producten

Snelle knoppen zoals:

2 boterham kaas
200 kwark
2 ei
Volgend baken (fase 2)

Peet Paars – Recipe & Product Engine

Doel:

AI recepten vervangen door
Peet recipe engine
gebaseerd op product database
Waar we in de volgende chat starten

We beginnen met:

Peet Recipe Engine

Dit wordt een klein maar krachtig systeem:

recipe_engine.py

dat:

ingrediënten kiest
kcal berekent
verzadiging berekent

en geen AI clichés meer geeft.

Als je in de nieuwe chat start kun je simpel zeggen:

“Pak baken: Peet Paars – NiceGUI migratie (fase 1 werkend)”

Dan gaan we direct verder met de recipe engine.

Start volgende chat met
Pak baken: Peet Paars – UI fase

Doel: twee-kolommen layout
(invoer links, vandaag rechts)
zonder bestaande functionaliteit te breken

💡 Dit is een goed moment in het project:
De moeilijke delen zijn opgelost (engine, database, AI product creation).

Wat nu nog komt is vooral UX verbeteren, en dat gaat relatief snel.

Baken gezet

Peet Paars – NiceGUI migratie (fase 1 werkend)

Staat nu stabiel:

Engine

✔ quick input parser

✔ product database koppeling

✔ kcal berekening

✔ daglog opslag

✔ refresh_ui stabiel

Resolver

✔ meerdere matches → keuze UI

✔ geen match → product aanmaken

✔ keuze → direct toevoegen aan dag

Product creatie

✔ app kan nieuw product aanmaken

✔ kcal / macro structuur opgeslagen in products.json

UX

✔ “AI” vervangen door “De app”

Huidige flow van Peet Paars
Snelle invoer
     ↓
Parser
     ↓
search_products
     ↓
Resolver
     ↓
1 match  → toevoegen
>1 match → gebruiker kiest
0 match  → nieuw product

Dit is exact de juiste architectuur voor food logging apps.

To-Fix lijst (zoals afgesproken)

Deze dingen pakken we later op:

Recept voorstel positie

moet direct onder Eten invoeren

Lunch / diner toevoegen knoppen

actieknoppen koppelen aan daglog

Preferred products

bonen → standaard kidneybonen

kip → standaard kipfilet

AI product builder verbeteren

macro’s betrouwbaarder

kcal per 100g

Snelle favorieten

bv

2 boterham kaas

kwark noten

Volgende stap (architectuur)

De belangrijkste volgende verbetering wordt:

Stap 5 — Preferred Product System

Doel:

200 bonen

hoeft niet elke keer:

Snijbonen
Kidneybonen
Witte bonen

maar automatisch:

Kidneybonen

Dat maakt Peet veel slimmer en sneller.

Maar volgens onze regels:

we stoppen hier voor vandaag op een stabiel punt.

Dat is precies hoe je technische schuld voorkomt.

Wanneer je verder wilt gaan, start je gewoon met:

“