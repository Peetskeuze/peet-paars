import json
from pathlib import Path

FILE = Path("data/products.json")

with open(FILE, "r", encoding="utf-8") as f:
    products = json.load(f)

print("Aantal producten:", len(products))
print("\nEerste 30 labels:\n")

for p in products[:30]:
    print("-", p.get("label"))