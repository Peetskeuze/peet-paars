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