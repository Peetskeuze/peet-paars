"""
Peet Paars – JSON schema (definitief)

Dit schema bewaakt:
- dagtype (rust / sport)
- verplichte maaltijden
- coachlaag
- optionele energie-overschrijding + compensatie
"""

from typing import List, Literal, TypedDict, Optional


DayType = Literal["rust", "sport"]
EnergyStatus = Literal["binnen", "boven"]
DinnerPriority = Literal["high"]


class Compensation(TypedDict):
    extra_movement: str


class EnergyCheck(TypedDict):
    estimated_kcal: int
    target_kcal: int
    status: EnergyStatus
    compensation: Optional[Compensation]

class Macros(TypedDict):
    kcal: int
    protein_g: int
    carbs_g: int
    fat_g: int

class Meal(TypedDict):
    moment: Literal["ontbijt", "lunch", "diner"]
    dish_name: str
    ingredients: List[str]
    preparation: List[str]
    macros: Macros


class PeetPaarsDay(TypedDict):
    day_type: DayType
    peet_message: str
    coach_message: str
    meals: List[Meal]
    energy_check: Optional[EnergyCheck]



REQUIRED_MEALS = {"ontbijt", "lunch", "diner"}


def validate_day(data: dict) -> None:
    # ------------------------------------------------------------
    # Basisstructuur
    # ------------------------------------------------------------
    if not isinstance(data, dict):
        raise ValueError("Output is geen dict")

    if data.get("day_type") not in ("rust", "sport"):
        raise ValueError("day_type moet 'rust' of 'sport' zijn")

    for field in ("peet_message", "coach_message"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f"{field} ontbreekt of is leeg")

    # ------------------------------------------------------------
    # Meals
    # ------------------------------------------------------------
    meals = data.get("meals")
    if not isinstance(meals, list):
        raise ValueError("meals moet een lijst zijn")

    REQUIRED_MEALS = {"ontbijt", "lunch", "diner"}
    found = set()

    for meal in meals:
        if not isinstance(meal, dict):
            raise ValueError("meal is geen dict")

        moment = meal.get("moment")
        if moment not in REQUIRED_MEALS:
            raise ValueError(f"Ongeldig moment: {moment}")
        found.add(moment)

        # Naam
        if not isinstance(meal.get("dish_name"), str) or not meal["dish_name"].strip():
            raise ValueError(f"dish_name ontbreekt bij {moment}")

        # Ingrediënten
        if not isinstance(meal.get("ingredients"), list):
            raise ValueError(f"ingredients ongeldig bij {moment}")

        # Bereiding
        preparation = meal.get("preparation")
        if not isinstance(preparation, list) or len(preparation) < 2:
            raise ValueError(f"preparation te kort bij {moment}")

        # --------------------------------------------------------
        # Macro's (verplicht)
        # --------------------------------------------------------
        macros = meal.get("macros")
        if not isinstance(macros, dict):
            raise ValueError(f"macros ontbreken bij {moment}")

        for key in ("kcal", "protein_g", "carbs_g", "fat_g"):
            value = macros.get(key)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"macros.{key} ongeldig bij {moment}")

    if found != REQUIRED_MEALS:
        raise ValueError("Niet alle verplichte maaltijden aanwezig")

    # ------------------------------------------------------------
    # Energy check (optioneel)
    # ------------------------------------------------------------
    energy = data.get("energy_check")
    if energy is not None:
        if not isinstance(energy, dict):
            raise ValueError("energy_check moet een dict zijn")

        if energy.get("status") not in ("binnen", "boven"):
            raise ValueError("energy_check.status ongeldig")

        if not isinstance(energy.get("estimated_kcal"), int):
            raise ValueError("energy_check.estimated_kcal ongeldig")

        if not isinstance(energy.get("target_kcal"), int):
            raise ValueError("energy_check.target_kcal ongeldig")

        compensation = energy.get("compensation")
        if compensation is not None:
            if not isinstance(compensation.get("extra_movement"), str):
                raise ValueError("energy_check.compensation.extra_movement ongeldig")
