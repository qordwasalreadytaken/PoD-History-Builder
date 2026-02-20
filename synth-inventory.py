

import json
import hashlib
import os
import re
from pathlib import Path
from urllib.parse import quote_plus
from character_storage import load_characters_as_list
import datetime
seen_date = datetime.datetime.now().strftime('%Y-%m-%d')

# Load stat definitions for property parsing
with open(Path(__file__).parent / "item_metadata.json", "r", encoding="utf-8") as f:
    STAT_DEFS = json.load(f)

def parseChanceToCast(line):
    match = re.search(r"(\d+)% Chance to cast level (\d+)\s+(.+?)\s+(when .+)$", line)
    if not match:
        return []
    percent, level, skill, trigger = match.groups()
    return [{"statKey": "ctc", "value": [int(percent), int(level), skill.strip(), trigger.strip()]}]

def parseChargedSkill(line):
    match = re.search(r"Level (\d+)\s+(.+?)\s+\((\d+)/(\d+) Charges\)", line)
    if not match:
        return []
    level, skill, charges, _ = match.groups()
    return [{"statKey": "cskill", "value": [int(level), skill.strip(), int(charges)]}]

def parseAfterKillStat(line):
    match = re.search(r"\+(\d+)\s+(?:to\s+)?(Mana|Life)\s+after\s+each\s+Kill", line, re.I)
    if not match:
        return []
    value, stat_type = match.groups()
    return [{"statKey": f"{stat_type.lower()}_after_kill", "value": int(value)}]

def parse_damage_property(line, stats=None):
    match = re.search(r"Adds (\d+)[–-](\d+)\s*(\w*)\s*Damage", line, re.I)
    if not match:
        return []
    min_val, max_val, element_raw = match.groups()
    element = element_raw.lower()
    key_min = key_max = "damage"
    if element == "fire":
        key_min, key_max = "fDamage_min", "fDamage_max"
    elif element == "cold":
        key_min, key_max = "cDamage_min", "cDamage_max"
    elif element == "lightning":
        key_min, key_max = "lDamage_min", "lDamage_max"
    elif element == "poison":
        key_min, key_max = "pDamage_min", "pDamage_max"
    return [
        {"statKey": key_min, "value": int(min_val)},
        {"statKey": key_max, "value": int(max_val)},
    ]

def parse_generic_property(line, stats):
    results = []
    for stat_key, stat_data in stats.items():
        if not isinstance(stat_data, dict):
            continue
        if stat_data.get("editable") != 1:
            continue
        fmt = stat_data.get("format", [])
        if not fmt:
            continue
        pattern = ".*".join(re.escape(p) for p in fmt)
        match = re.match(pattern, line, re.I)
        if match:
            nums = re.findall(r"[-+]?\d+", line)
            value = int(nums[0]) if nums else 1
            results.append({"statKey": stat_key, "value": value})
            break
    return results if results else None

def build_planner_url(item):
    # Parse properties
    props = {}
    multi_props = {"ctc": [], "cskill": []}
    for prop in item.get("properties", []):
        parsed = (
            parseChanceToCast(prop)
            or parseChargedSkill(prop)
            or parseAfterKillStat(prop)
            or parse_damage_property(prop, STAT_DEFS)
            or parse_generic_property(prop, STAT_DEFS)
        )
        if not parsed:
            continue
        if isinstance(parsed, dict):
            parsed = [parsed]
        for entry in parsed:
            key = entry.get("statKey")
            value = entry.get("value")
            if not key:
                continue
            if key in multi_props:
                if value not in multi_props[key]:
                    multi_props[key].append(value)
            else:
                props[key] = value
    for k, v in multi_props.items():
        if v:
            props[k] = v
    # Compose planner URL (minimal, single item import)
    base_url = "https://qordwasalreadytaken.github.io/path-of-diablo-planner/index.html"
    # Use slot 'imported' for all synth items
    arr = [item.get("title") or item.get("base_type") or "Synth Item", "0", "none"]
    # Add properties as single comma-separated token "key:val,key:val,..."
    if props:
        prop_pairs = []
        for key, value in props.items():
            if isinstance(value, list):
                prop_pairs.append(f"{key}:{'|'.join(map(str, value))}")
            else:
                prop_pairs.append(f"{key}:{value}")
        if prop_pairs:
            arr.append(','.join(prop_pairs))
    url = f"{base_url}?imported={quote_plus(','.join(arr))}"
    return url

def synth_item_id(item):
    base = item.get('base_type', '') + '|' + item.get('title', '')
    props = '|'.join(sorted(item.get('properties', [])))
    synth_from = '|'.join(sorted(item.get('synthesised_from', []))) if item.get('synthesised_from') else ''
    key = base + '|' + props + '|' + synth_from
    return hashlib.sha256(key.encode()).hexdigest()

def extract_synth_items(char, location):
    import datetime
    seen_date = datetime.datetime.now().strftime('%Y-%m-%d')
    items = []
    for item in char.get(location, []) or []:
        tag = (item.get('Tag', '') + item.get('TextTag', '')).lower()
        if 'synthesized' in tag:
            sockets = item.get('Sockets', [])
#            if sockets:
#                print(f"DEBUG: Found synth item with sockets: {item.get('Title', '')} | Sockets: {len(sockets)}")
            items.append({
                'id': None,  # to be filled later
                'friendly_id': None,  # to be filled later
                'owner': char.get('Name', ''),
                'base_type': item.get('Tag', ''),
                'title': item.get('Title', ''),
                'properties': item.get('PropertyList', []),
                'synthesised_from': item.get('SynthesisedFrom', []),
                'location': location,
                'Quality': item.get('Quality', ''),
                'QualityCode': item.get('QualityCode', ''),
                'Ethereal': item.get('Ethereal', ''),
                'DamageMinimum': item.get('DamageMinimum', ''),
                'DamageMaximum': item.get('DamageMaximum', ''),
                'LevelReq': item.get('LevelReq', ''),
                'SocketCount': item.get('SocketCount', ''),
                'seen_date': seen_date,
                'sockets': sockets
            })
    return items


def main():
    synth_items = []
    seen_ids = set()

    # Load existing synth_inventory.json if it exists
    if os.path.exists('synth_inventory.json'):
        with open('synth_inventory.json', 'r') as f:
            try:
                synth_items = json.load(f)
                seen_ids = set(item['id'] for item in synth_items)
            except Exception:
                synth_items = []
                seen_ids = set()

    # Load all characters from sharded files (both leagues)
    all_characters = load_characters_as_list('both')

    new_items = []
    for char in all_characters:
        for loc in ['Equipped', 'Inventory', 'MercenaryEquipped']:
            for item in extract_synth_items(char, loc):
                item_id = synth_item_id(item)
                if item_id not in seen_ids:
                    item['id'] = item_id
                    new_items.append(item)
                    seen_ids.add(item_id)

    synth_items.extend(new_items)



    # Assign friendly_id as a simple count (1-based) and add planner_url
    for idx, item in enumerate(synth_items, 1):
        item['friendly_id'] = idx
        item['planner_url'] = build_planner_url(item)
#        print(f"Item: {item['title']} | Seen date: {item.get('seen_date')}")


    # Write as JSON (optional, for compatibility)
    with open('synth_inventory.json', 'w') as f:
        json.dump(synth_items, f, indent=2)

    # Write as JS variable assignment
    with open('synth_inventory.js', 'w', encoding='utf-8') as f:
        f.write('const synthInventory = ')
        json.dump(synth_items, f, indent=2, ensure_ascii=False)
        f.write(';\n')

if __name__ == '__main__':
    main()