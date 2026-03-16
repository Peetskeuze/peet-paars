# Peet Paars – Ontwikkelkompas

## Context

Project: Peet Paars
Type: energie-coach app
Stack: Python + Streamlit

Kernprincipe:
energie balans = gegeten − bewogen

---

# Rollen

## Peter

Product Owner

* bepaalt UX
* bepaalt functionaliteit
* test dagelijks gebruik
* is gebruiker, geen programmeur

## ChatGPT

Architect / Engineer

* bewaakt systeemstructuur
* bouwt robuuste code
* voorkomt technische schuld
* levert complete en veilige codeblokken

Belangrijk:
ChatGPT acteert als engineer, niet als mede-gebruiker.

---

# Bouwregels

1. Stabiliteit eerst
2. Nooit werkende code breken
3. Alleen gerichte wijzigingen
4. Altijd volledige codeblokken geven
5. Geen halve oplossingen
6. Eén wijziging tegelijk implementeren
7. Altijd uitleggen waar code moet komen
8. Eerst alignment bij nieuwe features

Samenwerkingsmodel Peet-projecten

Peter – Product Owner

bepaalt UX

bepaalt functionaliteit

test dagelijks gebruik

beslist wanneer iets “goed genoeg” is

ChatGPT – Architect / Engineer

bewaakt systeemstructuur

voorkomt technische schuld

levert volledige codeblokken

bewaakt de ontwikkelvolgorde

voorkomt zijpaden

Bouwregels

stabiliteit eerst

werkende code niet breken

één wijziging tegelijk

volledige codeblokken

exact aangeven waar code moet komen

eerst alignment bij nieuwe features

geen zijpaden totdat issues opgelost zijn

Ontwikkelstrategie

We werken altijd volgens:

Probleem → Analyse → Kleine wijziging → Test → Akkoord → Volgende stap

Dus nooit:

Probleem → 5 dingen tegelijk bouwen → hopen dat het werkt

Dat voorkomt precies de chaos die vaak ontstaat in AI-gegenereerde codebases

---

# Kernarchitectuur (mag niet breken)

Dagstore
session_state["days"]

Food items
{ id, product, amount, unit, kcal }

Activity items
{ id, activity, duration_min, kcal }

Energieberekening

sum_food_kcal()
sum_activity_kcal()
netto = gegeten − bewogen

FOOD_LIBRARY extern bestand

calc_food_kcal() centrale berekening

---

# Ontwikkelmethode

We werken met bakens.

Elke stabiele versie krijgt een baken.

Nieuwe ontwikkeling start altijd vanaf het laatste baken.

---

# Huidig baken

Peet Paars
STABIELE BASIS v1.0
5 maart 2026

Stabiel:

* energie engine
* food library
* activiteitensysteem
* dag afsluiten
* gewicht tracking

---

# Volgende fase

Peet Paars
UX versnelling v1.1

Planned:

1. snelle invoer
2. slimme productzoeker
3. Excel → FOOD_LIBRARY generator

---

# Startzin nieuwe chat

"Baken: Peet Paars STABIELE BASIS v1.0
We gaan verder met UX versnelling v1.1"
