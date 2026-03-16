# ============================================================
# PEET PAARS
# Product Database
# ============================================================

import json
import re
from pathlib import Path

PRODUCT_FILE = Path("data/products.json")


# ------------------------------------------------------------
# producten laden
# ------------------------------------------------------------

def load_products():

    if not PRODUCT_FILE.exists():
        return []

    with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------
# producten opslaan
# ------------------------------------------------------------

def save_products(products):

    with open(PRODUCT_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)


# ------------------------------------------------------------
# slugify
# ------------------------------------------------------------

def slugify(text):

    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


# ------------------------------------------------------------
# product ophalen
# ------------------------------------------------------------

def get_product(product_id_or_name):

    products = load_products()
    q = str(product_id_or_name).lower().strip()

    for p in products:

        name = p.get("name", "").lower()
        pid = p.get("id", "").lower()
        aliases = [a.lower() for a in p.get("alias", [])]

        if q == pid or q == name or q in aliases:
            return p

    return None


# ------------------------------------------------------------
# product zoeken
# ------------------------------------------------------------

def search_products(query):

    products = load_products()
    q = query.lower().strip()

    exact = []
    starts = []
    contains = []

    for p in products:

        name = p.get("name", "").lower()
        aliases = [a.lower() for a in p.get("alias", [])]
        haystack = [name] + aliases

        if q in haystack:
            exact.append(p)

        elif any(h.startswith(q) for h in haystack):
            starts.append(p)

        elif any(q in h for h in haystack):
            contains.append(p)

    results = exact + starts + contains

    # dubbele producten eruit
    unique = []
    seen_ids = set()

    for p in results:
        pid = p.get("id")
        if pid not in seen_ids:
            unique.append(p)
            seen_ids.add(pid)

    return unique[:5]


# ------------------------------------------------------------
# nieuw product toevoegen
# ------------------------------------------------------------

def add_product(product):

    products = load_products()

    q = product.get("name", "").lower().strip()

    for p in products:
        name = p.get("name", "").lower().strip()
        aliases = [a.lower().strip() for a in p.get("alias", [])]

        if q == name or q in aliases:
            return False, "Product bestaat al."

    if not product.get("id"):
        product["id"] = slugify(product["name"])

    base_id = product["id"]
    counter = 2

    existing_ids = {p.get("id") for p in products}

    while product["id"] in existing_ids:
        product["id"] = f"{base_id}_{counter}"
        counter += 1

    products.append(product)
    save_products(products)

    return True, product