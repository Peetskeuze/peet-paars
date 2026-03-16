import json
from pathlib import Path

# import bestaande library
from food_library_generated_v8_2_fixed import FOOD_LIBRARY

OUTPUT = Path("data/products.json")

products = []

for name, data in FOOD_LIBRARY.items():

    product = {
        "id": name.lower().replace(" ", "_"),
        "name": name,
        "category": data.get("category", "unknown"),
        "kcal": data.get("kcal", 0),
        "protein": data.get("protein", 0),
        "fat": data.get("fat", 0),
        "carbs": data.get("carbs", 0),
        "fiber": data.get("fiber", 0)
    }

    products.append(product)

OUTPUT.parent.mkdir(exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print(f"{len(products)} producten geschreven naar products.json")