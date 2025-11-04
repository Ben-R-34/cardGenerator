import sys
import json
import re
from pathlib import Path
import frontmatter

RESOURCE_ABBR = {
    'mana': 'Ma',
    'metals': 'Me',
    'stone': 'St',
    'food': 'Fo'
}

DEFAULT_IMAGE = "assets/frame.png"

CARD_ROOT = "Cards"

def convert_cost(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip()

    m = re.search(r'\((\d+)\)\s*(\d+)\s*([A-Za-z]+)', s)
    if m:
        paren, n, res = m.groups()
        abbr = RESOURCE_ABBR.get(res.lower(), res[:2].capitalize())
        return f"{paren}{''.join([abbr for _ in range(int(n))])}"

    m2 = re.search(r'(\d+)\s*([A-Za-z]+)', s)
    if m2:
        n, res = m2.groups()
        abbr = RESOURCE_ABBR.get(res.lower(), res[:2].capitalize())
        return ''.join([abbr for _ in range(int(n))])

    return s.replace(" ", "")

def ensure_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [str(x)]

def process_card(md_path: Path):
    post = frontmatter.load(md_path)
    meta = post.metadata

    t_raw = meta.get("Type")
    types = t_raw if isinstance(t_raw, list) else [str(t_raw)] if t_raw else []
    types_norm = [t.lower() for t in types]

    card = {
        "name": meta.get("CardName", md_path.stem),
        "aspect": meta.get("Aspect", ""),
        "rarity": meta.get("Rarity", ""),
        "type": types,
        "image": DEFAULT_IMAGE
    }

    # Orientation rules
    if "leader" in types_norm:
        card["orientation"] = "portrait"
    elif "citadel" in types_norm or "territory" in types_norm:
        card["orientation"] = "landscape"
    else:
        card["orientation"] = "portrait"

    # Leaders (double-sided, cost only on the back)
    if "leader" in types_norm:
        card["text"] = meta.get("Front-Side_Oracle", "")
        card["bName"] = meta.get("Back-Side_Name", "")
        card["btext"] = meta.get("Back-Side_Oracle", "")
        card["cost"]  = convert_cost(meta.get("Back-Side_Prod_Cost", ""))  # back only
        card["power"] = None
        card["toughness"] = None
        card["has_back"] = True

    else:
        # Single-sided cards
        card["text"] = meta.get("Oracle", "")
        card["has_back"] = False

        # Extra fields by category
        if "citadel" in types_norm:
            card["health"] = meta.get("Health", None)
            card["shield"] = meta.get("Shield", None)
            card["ca"]     = meta.get("Counter-Attack", None)
            card["cost"]   = ""  # Citadels don't have a cost

        elif "territory" in types_norm:
            card["is"]   = meta.get("ImprovementSlots", None)
            card["cost"] = ""  # Territories don't have a cost

        elif "production" in types_norm:
            mat = meta.get("Material", None)
            card["mat"]    = mat if isinstance(mat, list) else ([mat] if mat else None)
            card["exhaust"] = meta.get("Exhaust", None)
            card["expend"]  = meta.get("Expend", None)
            card["cost"]    = convert_cost(meta.get("ProductionCost", ""))

        else:
            # General cost rules:
            # - Territory Improvements DO have a cost (kept as portrait cards)
            # - Other non-terr/non-citadel types keep their cost if provided
            card["cost"] = convert_cost(meta.get("ProductionCost", ""))

            if "unit" in types_norm:
                card["power"] = meta.get("Power", None)
                card["toughness"] = meta.get("Toughness", None)
            else:
                card["power"] = None
                card["toughness"] = None

        # Clean “Empty”
        if str(card["text"]).strip().lower() == "empty":
            card["text"] = ""

    return card



def scan(vault_path: Path):
    result = []
    cards_dir = vault_path / CARD_ROOT

    for md in cards_dir.rglob("*.md"):
        card = process_card(md)
        result.append(card)

    return result


def main():
    if len(sys.argv) != 3:
        print("Usage: python extract_obsidian_cards.py <vault_path> <output_json>")
        return

    vault_path = Path(sys.argv[1])
    out = Path(sys.argv[2])

    cards = scan(vault_path)

    out.write_text(json.dumps(cards, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Extracted {len(cards)} cards into {out}")


if __name__ == "__main__":
    main()
