import os
import json
import datetime
from urllib.parse import urlencode, quote_plus
import urllib.parse
from pathlib import Path
import re

# Import sharding helper
from character_storage import load_characters_as_list


# --- CONFIG ---
SNAPSHOT_DIR = "snapshots"
INDEX_FILE = "index.json"
CHARACTER_FILES = ["sc_characters.json", "hc_characters.json"]  # Split files
FALLBACK_FILE = "all_characters.json"   # Fallback to combined file if splits don't exist
#CHARACTER_FILE = "Verotika.json"   # or hc_ladder.json
#CHARACTER_FILE = "sorcsallsuck.json"   # or hc_ladder.json

#BASE_IMPORT_PATH = "https://build.pathofdiablo.com/"  # change if needed
BASE_IMPORT_PATH = "https://qordwasalreadytaken.github.io/path-of-diablo-planner/index.html"
#BASE_IMPORT_PATH = "file:///home/derek/path-of-diablo-planner/index.html"

GAME_VERSION = 2                    # PoD-specific features

# Replace with however you pass global settings in your builder
SETTINGS = {
    "parameters": 1,
    "coupling": 0,
    "synthwep": 0,
    "autocast": 0,
}

with open(Path(__file__).parent / "item_metadata.json", "r", encoding="utf-8") as f:
    STAT_DEFS = json.load(f)

COMPILED_STAT_PATTERNS = {}
for stat_key, stat_data in STAT_DEFS.items():
    if not isinstance(stat_data, dict):
        continue
    if stat_data.get("editable") != 1:
        continue
    fmt = stat_data.get("format", [])
    if not fmt:
        continue
    # join with .* to allow numbers/extra text between pieces
    pattern = ".*".join(re.escape(p) for p in fmt)
    COMPILED_STAT_PATTERNS[stat_key] = re.compile(pattern, re.I)

with open(Path(__file__).parent / "item_metadata.json", "r", encoding="utf-8") as f:
    STAT_DEFS = json.load(f)

COMPILED_STAT_PATTERNS = {}
for stat_key, stat_data in STAT_DEFS.items():
    if not isinstance(stat_data, dict):
        continue
    if stat_data.get("editable") != 1:
        continue
    fmt = stat_data.get("format", [])
    if not fmt:
        continue
    # join with .* to allow numbers/extra text between pieces
    pattern = ".*".join(re.escape(p) for p in fmt)
    COMPILED_STAT_PATTERNS[stat_key] = re.compile(pattern, re.I)

skills_amazon = [
    {"name": "Jab", "i": 0},
    {"name": "Power Strike", "i": 1},
    {"name": "Poison Javelin", "i": 2},
    {"name": "Fend", "i": 3},
    {"name": "Lightning Bolt", "i": 4},
    {"name": "Charged Strike", "i": 5},
    {"name": "Plague Javelin", "i": 6},
    {"name": "Molten Strike", "i": 7},
    {"name": "Lightning Strike", "i": 8},
    {"name": "Lightning Fury", "i": 9},
    {"name": "Inner Sight", "i": 10},
    {"name": "Lethal Strike", "i": 11},
    {"name": "Phase Run", "i": 12},
    {"name": "Dodge", "i": 13},
    {"name": "Avoid", "i": 14},
    {"name": "Penetrate", "i": 15},
    {"name": "Evade", "i": 16},
    {"name": "Decoy", "i": 17},
    {"name": "Valkyrie", "i": 18},
    {"name": "Pierce", "i": 19},
    {"name": "Cold Arrow", "i": 20},
    {"name": "Magic Arrow", "i": 21},
    {"name": "Multiple Shot", "i": 22},
    {"name": "Fire Arrow", "i": 23},
    {"name": "Ice Arrow", "i": 24},
    {"name": "Guided Arrow", "i": 25},
    {"name": "Exploding Arrow", "i": 26},
    {"name": "Strafe", "i": 27},
    {"name": "Immolation Arrow", "i": 28},
    {"name": "Freezing Arrow", "i": 29},
]
skills_assassin = [
    {"name": "Dragon Claw", "i":0},
    {"name": "Fists of Fire", "i":1},
    {"name": "Claws of Thunder", "i":2},
    {"name": "Blades of Ice", "i":3},
    {"name": "Tiger Strike", "i":4},
    {"name": "Dragon Talon", "i":5},
    {"name": "Cobra Strike", "i":6},
    {"name": "Dragon Flight", "i":7},
    {"name": "Claw Mastery", "i":9},
    {"name": "Psychic Hammer", "i":10},
    {"name": "Burst of Speed", "i":11},
    {"name": "Weapon Block", "i":13},
    {"name": "Cloak of Shadows", "i":14},
    {"name": "Fade", "i":15},
    {"name": "Shadow Warrior", "i":16},
    {"name": "Mind Blast", "i":17},
    {"name": "Venom", "i":18},
    {"name": "Shadow Master", "i":19},
    {"name": "Fire Blast", "i":20},
    {"name": "Shock Web", "i":21},
    {"name": "Blade Throw", "i":22},
    {"name": "Charged Bolt Sentry", "i":23},
    {"name": "Wake of Fire", "i":24},
    {"name": "Blade Fury", "i":25},
    {"name": "Lightning Sentry", "i":26},
    {"name": "Wake of Inferno", "i":27},
    {"name": "Death Sentry", "i":28},
    {"name": "Blade Shield", "i":29}
]
skills_barbarian = [
    {"name": "Howl", "i":0},
    {"name": "Find Potion", "i":1},
    {"name": "Taunt", "i":2},
    {"name": "Shout", "i":3},
    {"name": "Find Item", "i":4},
    {"name": "Battle Cry", "i":5},
    {"name": "Battle Orders", "i":6},
    {"name": "Grim Ward", "i":7},
    {"name": "War Cry", "i":8},
    {"name": "Battle Command", "i":9},
    {"name": "Edged Weapon Mastery", "i":10},
    {"name": "Pole Weapon Mastery", "i":11},
    {"name": "Blunt Weapon Mastery", "i":12},
    {"name": "Thrown Weapon Mastery", "i":13},
    {"name": "Increased Stamina", "i":14},
    {"name": "Counter Attack", "i":15},
    {"name": "Iron Skin", "i":16},
    {"name": "Increased Speed", "i":17},
    {"name": "Puncture", "i":18},
    {"name": "Whirling Axes", "i":19},
    {"name": "Natural Resistance", "i":20},
    {"name": "Double Swing", "i":21},
    {"name": "Frenzy", "i":22},
    {"name": "Bash", "i":23},
    {"name": "Cleave", "i":24},
    {"name": "Stun", "i":25},
    {"name": "Leap Slam", "i":26},
    {"name": "Double Throw", "i":27},
    {"name": "Concentrate", "i":28},
    {"name": "Ethereal Throw", "i":29},
    {"name": "Whirlwind", "i":30},
]
skills_druid = [
    {"name": "Firestorm", "i":0},
    {"name": "Molten Boulder", "i":1},
    {"name": "Flame Dash", "i":2},
    {"name": "Arctic Blast", "i":3},
    {"name": "Fissure", "i":4},
    {"name": "Cyclone Armor", "i":5},
    {"name": "Twister", "i":6},
    {"name": "Volcano", "i":7},
    {"name": "Tornado", "i":8},
    {"name": "Armageddon", "i":9},
    {"name": "Hurricane", "i":10},
    {"name": "Werewolf", "i":11},
    {"name": "Lycanthropy", "i":12},
    {"name": "Werebear", "i":13},
    {"name": "Feral Rage", "i":14},
    {"name": "Maul", "i":15},
    {"name": "Rabies", "i":16},
    {"name": "Fire Claws", "i":17},
    {"name": "Hunger", "i":18},
    {"name": "Shock Wave", "i":19},
    {"name": "Fury", "i":20},
    {"name": "Raven", "i":21},
    {"name": "Poison Creeper", "i":22},
    {"name": "Heart of Wolverine", "i":23},
    {"name": "Summon Spirit Wolf", "i":24},
    {"name": "Carrion Vine", "i":25},
    {"name": "Oak Sage", "i":26},
    {"name": "Summon Dire Wolf", "i":27},
    {"name": "Solar Creeper", "i":28},
    {"name": "Spirit of Barbs", "i":29},
]
skills_necromancer = [
    {"name": "Summon Mastery", "i":0},
    {"name": "Raise Skeleton Warrior", "i":1},
    {"name": "Bone Offering", "i":2},
    {"name": "Clay Golem", "i":3},
    {"name": "Flesh Offering", "i":4},
    {"name": "Raise Skeletal Mage", "i":5},
    {"name": "Blood Golem", "i":6},
    {"name": "Convocation", "i":7},
    {"name": "Iron Golem", "i":8},
    {"name": "Fire Golem", "i":9},
    {"name": "Revive", "i":10},
    {"name": "Deadly Poison", "i":11},
    {"name": "Teeth", "i":12},
    {"name": "Bone Armor", "i":13},
    {"name": "Corpse Explosion", "i":14},
    {"name": "Desecrate", "i":15},
    {"name": "Bone Spear", "i":16},
    {"name": "Bone Wall", "i":17},
    {"name": "Bone Spirit", "i":18},
    {"name": "Poison Nova", "i":19},
    {"name": "Amplify Damage", "i":20},
    {"name": "Dim Vision", "i":21},
    {"name": "Hemorrhage", "i":22},
    {"name": "Weaken", "i":23},
    {"name": "Iron Maiden", "i":24},
    {"name": "Terror", "i":25},
    {"name": "Confuse", "i":26},
    {"name": "Life Tap", "i":27},
    {"name": "Attract", "i":28},
    {"name": "Decrepify", "i":29},
    {"name": "Lower Resist", "i":30},
]
skills_paladin = [
    {"name": "Prayer", "i":0},
    {"name": "Resist Fire", "i":1},
    {"name": "Defiance", "i":2},
    {"name": "Resist Cold", "i":3},
    {"name": "Cleansing", "i":4},
    {"name": "Resist Lightning", "i":5},
    {"name": "Vigor", "i":6},
    {"name": "Meditation", "i":7},
    {"name": "Redemption", "i":8},
    {"name": "Salvation", "i":9},
    {"name": "Might", "i":10},
    {"name": "Holy Fire", "i":11},
    {"name": "Precision", "i":12},
    {"name": "Blessed Aim", "i":13},
    {"name": "Concentration", "i":14},
    {"name": "Holy Freeze", "i":15},
    {"name": "Holy Shock", "i":16},
    {"name": "Sanctuary", "i":17},
    {"name": "Fanaticism", "i":18},
    {"name": "Conviction", "i":19},
    {"name": "Sacrifice", "i":20},
    {"name": "Smite", "i":21},
    {"name": "Holy Bolt", "i":22},
    {"name": "Zeal", "i":23},
    {"name": "Charge", "i":24},
    {"name": "Vengeance", "i":25},
    {"name": "Blessed Hammer", "i":26},
    {"name": "Conversion", "i":27},
    {"name": "Holy Shield", "i":28},
    {"name": "Fist of the Heavens", "i":29},
    {"name": "Dashing Strike", "i":30},
]
skills_sorceress = [
    {"name": "Ice Bolt", "i":0},
    {"name": "Frigerate", "i":1},
    {"name": "Frost Nova", "i":2},
    {"name": "Ice Blast", "i":3},
    {"name": "Shiver Armor", "i":4},
    {"name": "Glacial Spike", "i":5},
    {"name": "Blizzard", "i":6},
    {"name": "Freezing Pulse", "i":7},
    {"name": "Chilling Armor", "i":8},
    {"name": "Frozen Orb", "i":9},
    {"name": "Cold Mastery", "i":10},
    {"name": "Charged Bolt", "i":11},
    {"name": "Static Field", "i":12},
    {"name": "Telekinesis", "i":13},
    {"name": "Nova", "i":14},
    {"name": "Lightning Surge", "i":15},
    {"name": "Chain Lightning", "i":16},
    {"name": "Teleport", "i":17},
    {"name": "Discharge", "i":18},
    {"name": "Energy Shield", "i":19},
    {"name": "Lightning Mastery", "i":20},
    {"name": "Thunder Storm", "i":21},
    {"name": "Fire Bolt", "i":22},
    {"name": "Warmth", "i":23},
    {"name": "Inferno", "i":24},
    {"name": "Immolate", "i":25},
    {"name": "Fire Ball", "i":26},
    {"name": "Fire Wall", "i":27},
    {"name": "Enflame", "i":28},
    {"name": "Meteor", "i":29},
    {"name": "Fire Mastery", "i":30},
    {"name": "Hydra", "i":31},
]


# Class -> skills map
skill_definitions = {
    "amazon": skills_amazon,
    "assassin": skills_assassin,
    "barbarian": skills_barbarian,
    "druid": skills_druid,
    "necromancer": skills_necromancer,
    "paladin": skills_paladin,
    "sorceress": skills_sorceress,
}


# --- build encoded skills string ---
def build_skills_string(character_class, character_skills):
    defs = skill_definitions.get(character_class.lower())
    if defs is None or not defs:
        raise ValueError(f"No skill definitions found for class {character_class}")

    skills = []
    for skill in sorted(defs, key=lambda s: s["i"]):
        points = character_skills.get(skill["name"], 0)
        skills.append(f"{points:02d}")  # always 2 digits
    return "".join(skills)


EQUIP_MAPPING = {
    "helmet": "helm",
    "body": "armor",
    "gloves": "gloves",
    "boots": "boots",
    "belt": "belt",
    "amulet": "amulet",
    "ring1": "ring1",
    "ring2": "ring2",
    "weapon1": "weapon",   # main hand
    "weapon2": "offhand",  # offhand
    # we ignore sweapon1 and sweapon2 entirely
}

EQUIP_ORDER = [
    "helm",
    "armor",
    "gloves",
    "boots",
    "belt",
    "amulet",
    "ring1",
    "ring2",
    "weapon",
    "offhand",
]


# Gem name fragments in Path of Diablo
GEM_KEYWORDS = [
    "Chipped", "Flawed", "Normal", "Flawless", "Perfect"
]
GEM_TYPES = [
    "Amethyst", "Topaz", "Ruby", "Sapphire",
    "Emerald", "Diamond", "Skull"
]

def is_socket_rune_or_gem(socket_item):
    """Return True if this socket item is a Rune or Gem."""
    title = socket_item.get("Title", "")
    qcode = socket_item.get("QualityCode", "")
    
    # Runes → check quality code
    if qcode == "q_rune" or "Rune" in title:
        return True
    
    # Gems → empty qualitycode, match gem words
    if qcode == "" and any(pref in title for pref in GEM_KEYWORDS) and any(t in title for t in GEM_TYPES):
        return True
    
    return False

def pretty_slot_label(slot):
    """
    Turn a json-worn or URL slot key into a user-friendly label used in item names.
    Accepts inputs like: 'helmet', 'helm', 'body', 'ring1', 'weapon1', 'weapon2', 'offhand', ...
    Returns: 'Helm', 'Armor', 'Ring', 'Weapon', 'Offhand', etc.
    """
    if not slot:
        return ""

    s = str(slot).lower()

    mapping = {
        # URL keys
        "helm": "Helm", "armor": "Armor", "gloves": "Gloves", "boots": "Boots",
        "belt": "Belt", "amulet": "Amulet", "ring1": "Ring", "ring2": "Ring",
        "weapon": "Weapon", "offhand": "Offhand",

        # JSON worn names
        "helmet": "Helm", "body": "Armor", "gloves": "Gloves", "boots": "Boots",
        "belt": "Belt", "amulet": "Amulet", "ring": "Ring", "ring1": "Ring", "ring2": "Ring",
        "weapon1": "Weapon", "weapon2": "Offhand", "sweapon1": "Weapon (swap)", "sweapon2": "Offhand (swap)",
    }

    if s in mapping:
        return mapping[s]

    # Fallback: drop trailing digits and underscores and title-case
    s2 = re.sub(r'\d+$', '', s)            # remove trailing digits like "1" or "2"
    s2 = s2.replace('_', ' ').strip()
    return s2.title()

def format_stat_line(stat_key, stat_value):
    """Formats a single stat line using stat definitions or fallbacks."""

    # Handle manual/custom parsers first
    if stat_key.startswith("chanceToCast"):
        return parseChanceToCast(stat_key, stat_value)
    elif stat_key.startswith("chargedSkill"):
        return parseChargedSkill(stat_key, stat_value)
    elif stat_key.startswith("afterKill"):
        return parseAfterKillStat(stat_key, stat_value)
    elif stat_key.endswith("Damage_min") or stat_key.endswith("Damage_max"):
        return parse_damage_property(stat_key, stat_value)

    # If in stats.json
    if stat_key in STAT_DEFS:
        fmt = STAT_DEFS[stat_key].get("format", [])
        parts = []
        for piece in fmt:
            if piece == "+":
                parts.append(f"{stat_value}")
            elif piece == "%":
                parts.append(f"{stat_value}%")
            elif "{}" in piece:
                parts.append(piece.format(stat_value))
            else:
                parts.append(piece)
        return " ".join(parts)

    # Fallback for unknown stats
    return f"{stat_key}: {stat_value}"

with open("item_metadata.json") as f:
    stats = json.load(f)


def parseChanceToCast(line):
    """Parse '% Chance to cast level X <Skill> when <Trigger>'."""
    match = re.search(r"(\d+)% Chance to cast level (\d+)\s+(.+?)\s+(when .+)$", line)
    if not match:
        return []
    percent, level, skill, trigger = match.groups()
    return [{"statKey": "ctc", "value": [int(percent), int(level), skill.strip(), trigger.strip()]}]

def parseChargedSkill(line):
    """Parse 'Level X <Skill> (Y/Z Charges)'."""
    match = re.search(r"Level (\d+)\s+(.+?)\s+\((\d+)/\d+ Charges\)", line)
    if not match:
        return []
    level, skill, charges = match.groups()
    return [{"statKey": "cskill", "value": [int(level), skill.strip(), int(charges)]}]

def parseAfterKillStat(line):
    """Parse '+X Mana/Life after each Kill'."""
    match = re.search(r"\+(\d+)\s+(?:to\s+)?(Mana|Life)\s+after\s+each\s+Kill", line, re.I)
    if not match:
        return []
    value, stat_type = match.groups()
    return [{"statKey": f"{stat_type.lower()}_after_kill", "value": int(value)}]

def parse_damage_property(line, stats=None):
    """
    Parse 'Adds X–Y [Element] Damage' and return min/max stat keys.
    Returns a list of dicts.
    """
    match = re.search(r"Adds (\d+)[–-](\d+)\s*(\w*)\s*Damage", line, re.I)
    if not match:
        return []
    min_val, max_val, element_raw = match.groups()
    element = element_raw.lower()
    key_min = key_max = "damage"  # default physical
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
            continue  # skip invalid entries
        if stat_data.get("editable") != 1:
            continue

        fmt = stat_data.get("format", [])
        if not fmt:
            continue

        # build regex pattern
        pattern = ".*".join(re.escape(p) for p in fmt)
        match = re.match(pattern, line, re.I)
        if match:
            # extract number from first group or fallback
            nums = re.findall(r"[-+]?\d+", line)
            value = int(nums[0]) if nums else 1
            results.append({"statKey": stat_key, "value": value})
            print(f"✅ MATCH: '{line}' -> {stat_key}:{value} (pattern={pattern})")
            break

    return results if results else None

def format_stat_line(stat_key, stat_value):
    """Formats a single stat line using stat definitions or fallbacks."""

    # Handle manual/custom parsers first
    if stat_key.startswith("chanceToCast"):
        return parseChanceToCast(stat_key, stat_value)
    elif stat_key.startswith("chargedSkill"):
        return parseChargedSkill(stat_key, stat_value)
    elif stat_key.startswith("afterKill"):
        return parseAfterKillStat(stat_key, stat_value)
    elif stat_key.endswith("Damage_min") or stat_key.endswith("Damage_max"):
        return parse_damage_property(stat_key, stat_value)

    # If in stats.json
    if stat_key in STAT_DEFS:
        fmt = STAT_DEFS[stat_key].get("format", [])
        parts = []
        for piece in fmt:
            if piece == "+":
                parts.append(f"{stat_value}")
            elif piece == "%":
                parts.append(f"{stat_value}%")
            elif "{}" in piece:
                parts.append(piece.format(stat_value))
            else:
                parts.append(piece)
        return " ".join(parts)

    # Fallback for unknown stats
    return f"{stat_key}: {stat_value}"

with open("item_metadata.json") as f:
    stats = json.load(f)


def build_equipment_url(equipped_items, stats):
    """
    Returns (runewords_dict, eq_segments) for a character's equipped items.
    Runewords only include name and base. Unique/set items only include names.
    Only magic/rare/crafted items include properties.
    """
    RUNES_BY_ID = {
        "2693": "Delirium",
        "-26": "Pattern2"
    }

    runewords_dict = {}
    eq_segments = []
    multi_props_keys = {"ctc", "cskill"}

    for item in equipped_items:
        worn = item.get("Worn")
        slot = EQUIP_MAPPING.get(worn, worn)
        if not slot:
            continue

        quality = item.get("QualityCode", "")
        title = item.get("Title", "") or ""
        tag = item.get("Tag", "")
        sockets = [s.get("Title") for s in item.get("Sockets", []) if is_socket_rune_or_gem(s)]

        # Runewords → use regular slot format with name and base
        if quality == "q_runeword":
            rw_name = RUNES_BY_ID.get(title, title)
            # Format: "RunewordName - BaseName"
            runeword_display = f"{rw_name} - {tag}"
            eq_segments.append(f"{slot}={quote_plus(runeword_display)}")
            continue

        # Unique/Set → simple name only
        if quality in ("q_unique", "q_set"):
            eq_segments.append(f"{slot}={quote_plus(title or f'Imported {pretty_slot_label(slot)}')}")
            continue

        # Normal/High/Magic/Rare/Crafted → use comma-separated format matching saveImportedItemToUrl
        if quality in ("q_normal", "q_high", "q_magic", "q_rare", "q_crafted"):
            props = {}
            multi_props = {k: [] for k in multi_props_keys}

            # Collect item properties for all these quality types
            for prop in item.get("PropertyList", []):
                parsed = (
                    parseChanceToCast(prop)
                    or parseChargedSkill(prop)
                    or parseAfterKillStat(prop)
                    or parse_damage_property(prop, stats)
                    or parse_generic_property(prop, stats)
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
                    if key in multi_props_keys:
                        # Prevent duplicates in multi_props
                        if value not in multi_props[key]:
                            multi_props[key].append(value)
                    else:
                        props[key] = value

            # Merge multi_props into props if any
            for k, v in multi_props.items():
                if v:
                    props[k] = v

            # Use the actual base item name from TextTag or Tag instead of generic slot names
#            base_name = item.get("TextTag") or item.get("Tag") or pretty_slot_label(slot)
            base_name = item.get("Tag") or pretty_slot_label(slot)
            # Handle special cases for arrows/bolts
            if tag in ['Bolts', 'Arrows']:
                # Both q_normal and q_high should display as "normal"
                quality_display = "normal" if quality in ("q_normal", "q_high") else quality.replace('q_', '')
                name = f"Imported {quality_display} {tag}"
            else:
                # Both q_normal and q_high should display as "normal"
                quality_display = "normal" if quality in ("q_normal", "q_high") else quality.replace('q_', '')
                name = f"Imported {quality_display} {base_name}"
            
            # Build comma-separated format matching saveImportedItemToUrl: [title, tier, corruption, ...sockets, props]
            arr = [name, "0", "none"]  # title, tier=0, corruption=none
            
            # Add sockets if present (only actual socket names, no "none" padding)
            if sockets:
                arr.extend(sockets)
            
            # Add properties as single comma-separated token "key:val,key:val,..."
            if props:
                prop_pairs = []
                for key, value in props.items():
                    if isinstance(value, list):
                        # For arrays like ctc/cskill, join with | (pipe separator)
                        prop_pairs.append(f"{key}:{'|'.join(map(str, value))}")
                    else:
                        prop_pairs.append(f"{key}:{value}")
                # Add all props as a single token
                if prop_pairs:
                    arr.append(','.join(prop_pairs))
            
            eq_segments.append(f"{slot}={quote_plus(','.join(arr))}")
            continue

        # Fallback → mark as none
        eq_segments.append(f"{slot}=none")

    return runewords_dict, eq_segments


def build_final_url(character, base_path=BASE_IMPORT_PATH):
    class_name = character["Class"].lower()
    level = character["Stats"]["Level"]

    # Skill string
    skill_points = {s["Name"]: s.get("Level",0) for tab in character.get("SkillTabs", []) for s in tab.get("Skills", [])}
    skills_str = build_skills_string(class_name, skill_points)

    # Core params
    params = {
        "v": 2,
        "url": 1,
        "class": class_name,
        "level": level,
        "difficulty": 3,
        "quests": 1,
        "running": 0,
        "strength": character["Stats"].get("Strength",0),
        "dexterity": character["Stats"].get("Dexterity",0),
        "vitality": character["Stats"].get("Vitality",0),
        "energy": character["Stats"].get("Energy",0),
        "coupling": 1,
        "synthwep": 0,
        "autocast": 1,
        "skills": skills_str,
        "selected": "none,none"
    }

    runewords_dict, eq_segments = build_equipment_url(character.get("Equipped", []), stats)

    # Core URL without eq_segments (no runewords parameter needed)
    core_url = f"{base_path}?{urlencode(params, doseq=True)}"

    # Append custom_<slot> segments directly, do NOT urlencode again
    if eq_segments:
        return f"{core_url}&{'&'.join(eq_segments)}"
    return core_url


# --- JSON helpers ---
def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def safe_filename(name: str) -> str:
    # Normalize: lowercase + replace anything not filename-safe
    return re.sub(r'[^a-z0-9_-]', '_', name.lower())

def load_all_characters():
    """Load characters from sharded files using the centralized helper."""
    all_characters = load_characters_as_list('both')
    
    if not all_characters:
        print("⚠️ No character files found!")
        return []
    
    print(f"✅ Total characters loaded: {len(all_characters)}")
    return all_characters

def main():
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%dT%H:%M")    

    characters = load_all_characters()
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    for char in characters:
        name = char.get("Name")
        if not name:
            continue

        url = build_final_url(char)

        # Path for this character’s history file (case-insensitive)
        char_file = os.path.join(SNAPSHOT_DIR, f"{safe_filename(name)}.json")

        # Load existing history (if any)
        if os.path.exists(char_file):
            history = load_json(char_file)
        else:
            history = []

        # Avoid duplicate entry for same timestamp
        if not any(entry["timestamp"] == today for entry in history):
            history.append({
                "timestamp": today,
                "url": url,
                "originalName": name  # preserve display casing
            })

        # Save back
        save_json(char_file, history)

    print(f"✅ Updated {len(characters)} character histories at {today}")

if __name__ == "__main__":
    main()