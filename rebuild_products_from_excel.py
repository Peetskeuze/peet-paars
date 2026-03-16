import pandas as pd
import json
from pathlib import Path

EXCEL = Path("Peet_Paars_Master_v8_1.xlsx")
OUTPUT = Path("data/products.json")

df = pd.read_excel(EXCEL)

products = []

for _, row in df.iterrows():

    unit = str(row.get("eenheid", "gram")).lower()

    grams_per_unit = 1

    if unit == "stuk":
        grams_per_unit = row.get("standaard_portie_gram", 1)

    elif unit == "ml":
        grams_per_unit = 1

    elif unit == "cl":
        grams_per_unit = 10

    product = {
        "id": row["product_id"],
        "name": row["naam"],
        "category": row.get("categorie", ""),
        "category_main": row.get("categorie_hoofd", ""),
        "unit": unit,
        "grams_per_unit": grams_per_unit,
        "kcal": float(row.get("kcal_100g", 0)),
        "protein": float(row.get("eiwit_100g", 0)),
        "fat": float(row.get("vet_100g", 0)),
        "carbs": float(row.get("kh_100g", 0)),
        "fiber": float(row.get("vezel_100g", 0)),
        "default_portion_g": row.get("standaard_portie_gram"),
        "default_portion_ml": row.get("standaard_portie_ml"),
        "default_portion_cl": row.get("standaard_portie_cl"),
        "alias": row.get("alias"),
        "search_name": row.get("zoeknaam")
    }

    products.append(product)

OUTPUT.parent.mkdir(exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print(f"{len(products)} producten correct opgebouwd uit Excel")