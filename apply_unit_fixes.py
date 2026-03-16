import json
from pathlib import Path

FILE = Path("data/products.json")

with open(FILE, "r", encoding="utf-8") as f:
    products = json.load(f)

fixed = 0

for p in products:

    name = p["name"].lower()

    if "ei" in name:
        p["unit"] = "stuk"
        p["grams_per_unit"] = 60
        fixed += 1

    elif "banaan" in name:
        p["unit"] = "stuk"
        p["grams_per_unit"] = 120
        fixed += 1

    elif "appel" in name:
        p["unit"] = "stuk"
        p["grams_per_unit"] = 180
        fixed += 1

    elif "bier" in name:
        p["unit"] = "ml"
        p["grams_per_unit"] = 1
        fixed += 1

    elif "melk" in name:
        p["unit"] = "ml"
        p["grams_per_unit"] = 1
        fixed += 1

    elif "wijn" in name:
        p["unit"] = "ml"
        p["grams_per_unit"] = 1
        fixed += 1

with open(FILE, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print(f"{fixed} producten aangepast")