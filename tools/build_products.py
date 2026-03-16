import pandas as pd
import json
from pathlib import Path

EXCEL_FILE = "Peet_Paars_Master_v8_1.xlsx"
OUTPUT_FILE = Path("data/products.json")

df = pd.read_excel(EXCEL_FILE)

products = []

for _, row in df.iterrows():

    product = {
        "name": str(row["naam"]).lower(),
        "category": row.get("categorie", ""),
        "kcal": row.get("kcal_100g", 0),
        "protein": row.get("eiwit_100g", 0),
        "fat": row.get("vet_100g", 0),
        "carbs": row.get("kh_100g", 0),
        "fiber": row.get("vezel_100g", 0)
    }

    products.append(product)

OUTPUT_FILE.parent.mkdir(exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print("Products geschreven:", len(products))