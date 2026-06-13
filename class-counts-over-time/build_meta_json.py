import json
from pathlib import Path
from collections import Counter
import math

SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_DIR = SCRIPT_DIR / "season_cache"
OUT_FILE = SCRIPT_DIR / "meta_analysis.json"

SEASONS = range(1, 14)

CLASS_LABELS = {
    "ama": "Amazon",
    "asn": "Assassin",
    "bar": "Barbarian",
    "dru": "Druid",
    "nec": "Necromancer",
    "pal": "Paladin",
    "sor": "Sorceress",
}


def dominance_index(counts):
    total = sum(counts.values())
    if total == 0:
        return 0

    # Herfindahl-style concentration
    return sum((v / total) ** 2 for v in counts.values())

def load(mode, season):
    path = CACHE_DIR / f"{mode}_season_{season}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text())


def count(chars, min_level):
    c = Counter()
    total = 0

    for ch in chars:
        if ch.get("level", 0) >= min_level:
            cls = ch.get("charClass")
            if cls:
                c[cls] += 1
            total += 1

    return total, c


def build():
    out = {
        "sc": {},
        "hc": {},
        "classes": CLASS_LABELS
    }

    for mode in ["sc", "hc"]:
        for season in SEASONS:
            chars = load(mode, season)

            if not chars:
                continue

            out[mode][season] = {}

            for min_level in [80, 90, 95, 96, 97, 98, 99]:
                total, counts = count(chars, min_level)

                out[mode][season][min_level] = {
                    "total": total,
                    "counts": dict(counts)
                }
                out[mode][season][min_level]["dominance"] = dominance_index(counts)

    OUT_FILE.write_text(json.dumps(out, indent=2))
    print(f"Saved {OUT_FILE}")


if __name__ == "__main__":
    build()