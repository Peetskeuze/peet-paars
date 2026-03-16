import json
from pathlib import Path

FILE = Path("data/products.json")

with open(FILE, "r", encoding="utf-8") as f:
    products = json.load(f)

for p in products:

    if "unit" not in p:
        p["unit"] = "gram"

    if "grams_per_unit" not in p:
        p["grams_per_unit"] = 1

with open(FILE, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print(f"{len(products)} producten geüpdatet.")
print("Database nu klaar voor unit support.")