import re


import re
import html

def clean_text(value: str) -> str:
    """
    Verwijdert HTML, markup en overtollige whitespace.
    Altijd veilige plain text.
    """
    if not isinstance(value, str):
        return ""

    # 1) Decode HTML entities: &lt;div&gt; -> <div>
    value = html.unescape(value)

    # 2) Strip echte HTML tags
    value = re.sub(r"<[^>]+>", "", value)

    # 3) Soms komt er nog 'div class="..."' als losse tekst mee: ruim dat op
    #    (conservatief: alleen de bekende peet wrappers)
    value = re.sub(r'\bdiv\s+class\s*=\s*"peet-[^"]+"\b', "", value, flags=re.IGNORECASE)
    value = value.replace("/div", "").replace("div", "")  # extra defensief voor rare restjes

    # 4) Whitespace normaliseren
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def clean_macros(macros: dict) -> dict:
    """
    Zorgt dat macros alleen geldige numerieke waarden bevatten.
    """
    if not isinstance(macros, dict):
        return {
            "kcal": 0,
            "protein_g": 0,
            "carbs_g": 0,
            "fat_g": 0,
        }

    def safe_int(v):
        try:
            return int(round(float(v)))
        except Exception:
            return 0

    return {
        "kcal": safe_int(macros.get("kcal")),
        "protein_g": safe_int(macros.get("protein_g")),
        "carbs_g": safe_int(macros.get("carbs_g")),
        "fat_g": safe_int(macros.get("fat_g")),
    }
