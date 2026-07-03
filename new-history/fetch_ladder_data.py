######## To manually add a character to the watchilist
# python fetch_ladder_data.py --add-watched SomeCharacterName
# or open an issue with "add charactername" as gthe subject
# ########

import requests
import json
import os
import time
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime
import pprint
pp = pprint.PrettyPrinter(indent=4)
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import glob

# Directories and files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define snapshot directory for per-character history
SNAPSHOT_DIR = os.path.join(BASE_DIR, 'snapshots')
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# Optional list of extra characters to always watch (even if not on ladder)
WATCHLIST_FILE = os.path.join(BASE_DIR, 'watched_characters.json')

# One-time bulk import output containing discovered character names from
# account last-character lookups. We also monitor these names every run.
ACCOUNT_DISCOVERY_FILE = os.path.join(BASE_DIR, 'account_last_characters.json')

# Character summary endpoint (used for ladder and watched characters)
CHAR_URL = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"


def save_character_history(char_name, history):
    path = os.path.join(SNAPSHOT_DIR, f'{char_name}.json')
    # Save all snapshot files in lowercase
    path = os.path.join(SNAPSHOT_DIR, f'{char_name.lower()}.json')
    with open(path, 'w') as f:
        json.dump(history, f, indent=2)

def create_character_index():
    """Scan all dailies/*.json files and build a character index mapping character names to snapshot files."""
    dailies_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dailies')
    index = {}
    for json_file in glob.glob(os.path.join(dailies_dir, '*.json')):
        # Extract date/mode from filename
        filename = os.path.basename(json_file)
        date_part = filename.split('-')[0:3]
        date = '-'.join(date_part)
        mode = 'Hardcore' if 'hc_' in filename else 'Softcore'
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                for char in data:
                    name = char.get('Name')
                    if not name:
                        continue
                    entry = { 'file': filename, 'date': date, 'mode': mode }
                    if name not in index:
                        index[name] = []
                    index[name].append(entry)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    # Save index
    index_path = os.path.join(BASE_DIR, 'character_index.json')
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)
    print(f"✅ Character index created with {len(index)} characters.")


def fetch_ladder_characters(base_ladder_url, start_page=1, end_page=5):
    all_characters = []
    for page in range(start_page, end_page + 1):
        url = f"{base_ladder_url}{page}"
        print(f"Fetching {url}")
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            all_characters.extend(data.get("ladder", []))
        else:
            print(f"⚠️ Failed to fetch page {page}: {response.status_code}")
    return all_characters

def fetch_1kladder_characters(base_ladder_url, pages):
    """Fetch all characters from multiple pages of the ladder."""
    all_characters = []
    for page in range(0, pages + 1):
        ladder_url = f"{base_ladder_url}{page}"
        print(f"Fetching {ladder_url}")
        response = requests.get(ladder_url)
        if response.status_code == 200:
            ladder_data = response.json()
            all_characters.extend(ladder_data.get("ladder", []))
        else:
            print(f"⚠️ Failed to fetch page {page}: {response.status_code}")
    return all_characters


def GetAllCharData():
    base_ladder_url = "https://beta.pathofdiablo.com/api/ladder/13/0/"  # Softcore

    # Step 1: Fetch top 1,000 characters (pages 0 to 5)
    all_characters = fetch_ladder_characters(f"{base_ladder_url}0/", start_page=0, end_page=5)
#    all_characters = fetch_ladder_characters(base_ladder_url, start_page=0, end_page=5)
#    all_characters = fetch_ladder_characters(base_ladder_url, start_page=1, end_page=5)
    top_1000_characters = {char["charName"]: char for char in all_characters}.values()

    # Step 3: Continue with class-specific characters
    classes = {
        "Amazon": "1/",
        "Assassin": "7/",
        "Barbarian": "5/",
        "Druid": "6/",
        "Necromancer": "3/",
        "Paladin": "4/",
        "Sorceress": "2/"
    }

    for class_name, api_suffix in classes.items():
        class_ladder_url = f"{base_ladder_url}{api_suffix}"
        class_characters = fetch_ladder_characters(class_ladder_url, 1)
        all_characters.extend(class_characters)  # Combine lists

    # Step 4: Remove duplicates by character name
    unique_characters = {char["charName"]: char for char in all_characters}.values()

    # Step 5: Fetch complete character data
    character_data = []
    for character in unique_characters:
        char_name = character.get("charName", "unknown")
        char_id = character.get("id", None)

        if char_name == "unknown":
            char_name = f"unknown_{char_id or int(time.time() * 1000)}"

        response = requests.get(CHAR_URL.format(char_name=char_name))
        if response.status_code == 200:
            character_data.append(response.json())
        else:
            print(f"⚠️ Failed to fetch character: {char_name}")

    # Step 6: Save the extended character list
    with open("sc_ladder.json", "w") as file:
        json.dump(character_data, file, indent=2)

    print(f"✅ Saved {len(character_data)} characters to sc_ladder.json (top 1,000 + class-specific)")


def GetAllHCCharData():
    base_ladder_url = "https://beta.pathofdiablo.com/api/ladder/13/1/"  # Hardcore

    # Fetch top 1,000 characters
#    all_characters = fetch_ladder_characters(f"{base_ladder_url}0/", 5)
    all_characters = fetch_ladder_characters(base_ladder_url, start_page=0, end_page=5)

    # Fetch top 200 per class
    classes = {
        "Amazon": "1/",
        "Assassin": "7/",
        "Barbarian": "5/",
        "Druid": "6/",
        "Necromancer": "3/",
        "Paladin": "4/",
        "Sorceress": "2/"
    }

    for class_name, api_suffix in classes.items():
#        class_ladder_url = f"{base_ladder_url[:-2]}{api_suffix}"  # Adjusting URL for class-specific calls
        class_ladder_url = f"{base_ladder_url}{api_suffix}"  # Adjusting URL for class-specific calls
        class_characters = fetch_ladder_characters(class_ladder_url, 1)  # Only one page needed
        all_characters.extend(class_characters)

    # Remove duplicates (some characters appear in both top 1,000 and top 200 class rankings)
    unique_characters = {char["charName"]: char for char in all_characters}.values()

    character_data = []
    for character in unique_characters:
        char_name = character.get("charName", "unknown")
        char_id = character.get("id", None)

        if char_name == "unknown":
            char_name = f"unknown_{char_id or int(time.time() * 1000)}"

        response = requests.get(CHAR_URL.format(char_name=char_name))
        if response.status_code == 200:
            character_data.append(response.json())
        else:
            print(f"⚠️ Failed to fetch character: https://beta.pathofdiablo.com/api/characters/{char_name}/summary")

    # Save as one big JSON
    with open("hc_ladder.json", "w") as file:
        json.dump(character_data, file, indent=2)

    print(f"✅ Saved {len(character_data)} unique characters to hc_ladder.json")

def copy_ladders_to_dailies():
    """Copy sc_ladder.json and hc_ladder.json to dailies/ with a date-stamped filename."""
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    new_history_dir = BASE_DIR
    dailies_dir = os.path.join(new_history_dir, 'dailies')
    os.makedirs(dailies_dir, exist_ok=True)
    for base in ['sc_ladder.json', 'hc_ladder.json']:
        src = os.path.join(new_history_dir, base)
        if os.path.exists(src):
            if base.startswith('sc_'):
                dst = os.path.join(dailies_dir, f"{now}-sc_ladder.json")
            elif base.startswith('hc_'):
                dst = os.path.join(dailies_dir, f"{now}-hc_ladder.json")
            else:
                continue
            import shutil
            shutil.copy2(src, dst)
            print(f"Copied {src} to {dst}")
    # After copying, update the character index
    create_character_index()


def get_character_change_details(new_data, last_data):
    # Compare only skill levels and equipped item titles so snapshots stay compact.
    new_data = new_data if isinstance(new_data, dict) else {}
    last_data = last_data if isinstance(last_data, dict) else {}

    def extract_skills_from_skilltabs(data):
        skilltabs = data.get('SkillTabs')
        skills = {}
        if isinstance(skilltabs, list):
            for tab in skilltabs:
                for skill in tab.get('Skills', []):
                    name = skill.get('Name')
                    level = skill.get('Level')
                    if name is not None and level is not None:
                        skills[name] = level
        return skills

    def extract_equipped_titles(data):
        equipped = data.get('Equipped')
        if not equipped or not isinstance(equipped, list):
            return []
        return sorted([item.get('Title', '') for item in equipped if isinstance(item, dict) and 'Title' in item])

    skills_new = extract_skills_from_skilltabs(new_data)
    skills_last = extract_skills_from_skilltabs(last_data)
    equipped_new = extract_equipped_titles(new_data)
    equipped_last = extract_equipped_titles(last_data)

    skills_new_keys = set(skills_new.keys())
    skills_last_keys = set(skills_last.keys())
    skills_added_names = sorted(skills_new_keys - skills_last_keys)
    skills_removed_names = sorted(skills_last_keys - skills_new_keys)
    skills_updated = []
    for name in sorted(skills_new_keys & skills_last_keys):
        old_level = skills_last.get(name)
        new_level = skills_new.get(name)
        if old_level != new_level:
            skills_updated.append({
                'name': name,
                'from_level': old_level,
                'to_level': new_level
            })

    equipped_new_counter = Counter(equipped_new)
    equipped_last_counter = Counter(equipped_last)
    equipped_added = []
    equipped_removed = []
    all_titles = sorted(set(equipped_new_counter.keys()) | set(equipped_last_counter.keys()))
    for title in all_titles:
        delta = equipped_new_counter[title] - equipped_last_counter[title]
        if delta > 0:
            equipped_added.extend([title] * delta)
        elif delta < 0:
            equipped_removed.extend([title] * (-delta))

    skill_change = skills_new != skills_last
    equipped_change = equipped_new != equipped_last

    return {
        'skill_change': skill_change,
        'equipped_change': equipped_change,
        'skills_added': skills_added_names,
        'skills_removed': skills_removed_names,
        'skills_updated': skills_updated,
        'equipped_added': equipped_added,
        'equipped_removed': equipped_removed
    }


def character_changed(new_data, last_data, return_flags=False):
    details = get_character_change_details(new_data, last_data)

    if return_flags:
        return details['skill_change'], details['equipped_change']

    return details['skill_change'] or details['equipped_change']

def load_character_history(char_name):
    path = os.path.join(SNAPSHOT_DIR, f'{char_name}.json')
    # Always load using lowercase filename
    path = os.path.join(SNAPSHOT_DIR, f'{char_name.lower()}.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return []

def process_characters(characters):
    # Normalize character names to lowercase to avoid processing the same
    # character multiple times in a single run due to case or source
    # differences (e.g., "Devoraan" from ladder vs "devoraan" from
    # existing snapshots/watchlist). The last seen data for a given
    # lowercase name wins.
    normalized_characters = {}
    for name, data in characters.items():
        if not name:
            continue
        key = str(name).lower()
        normalized_characters[key] = data

#    charlevel = char_data.get('level', 'Unknown')
#    timestamp = "Level: " + str(charlevel) + " " + datetime.utcnow().isoformat() + 'Z'
    timestamp = datetime.utcnow().isoformat() + 'Z'
    recently_changed = []
    for char_name, char_data in normalized_characters.items():
        history = load_character_history(char_name)
        last_snapshot = history[-1]['data'] if history else None
        if last_snapshot is None:
            change_details = {
                'skill_change': False,
                'equipped_change': False,
                'skills_added': [],
                'skills_removed': [],
                'skills_updated': [],
                'equipped_added': [],
                'equipped_removed': []
            }
            skill_change = change_details['skill_change']
            equipped_change = change_details['equipped_change']
            has_change = True
        else:
            change_details = get_character_change_details(char_data, last_snapshot)
            skill_change = change_details['skill_change']
            equipped_change = change_details['equipped_change']
            has_change = skill_change or equipped_change

        if has_change:
            history.append({
                'timestamp': timestamp,
                'data': char_data,
                'skill_change': skill_change,
                'equipped_change': equipped_change,
                'skills_added': change_details['skills_added'],
                'skills_removed': change_details['skills_removed'],
                'skills_updated': change_details['skills_updated'],
                'equipped_added': change_details['equipped_added'],
                'equipped_removed': change_details['equipped_removed']
            })
            save_character_history(char_name, history)
            recently_changed.append(char_name)
    # Write recently changed characters to recently_changed.json (overwrite each run)
    recently_changed_path = os.path.join(BASE_DIR, 'recently_changed.json')
    with open(recently_changed_path, 'w') as f:
        json.dump(recently_changed, f, indent=2)
    return recently_changed


def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                return [str(name) for name in data]
        except Exception as e:
            print(f"⚠️ Failed to load watchlist: {e}")
    return []


def load_account_discovered_names():
    if os.path.exists(ACCOUNT_DISCOVERY_FILE):
        try:
            with open(ACCOUNT_DISCOVERY_FILE, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                return [str(name) for name in data]
        except Exception as e:
            print(f"⚠️ Failed to load account discovery list: {e}")
    return []


def save_watchlist(names):
    try:
        with open(WATCHLIST_FILE, 'w') as f:
            json.dump(sorted(set(names)), f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save watchlist: {e}")


def add_to_watchlist(char_name):
    names = load_watchlist()
    if char_name not in names:
        names.append(char_name)
        save_watchlist(names)
        print(f"✅ Added '{char_name}' to watchlist.")
    else:
        print(f"ℹ️ '{char_name}' is already in the watchlist.")


def get_snapshot_character_names():
    names = set()
    if not os.path.isdir(SNAPSHOT_DIR):
        return names
    for entry in os.listdir(SNAPSHOT_DIR):
        if entry.endswith('.json'):
            name, _ = os.path.splitext(entry)
            names.add(name)
    return names


def fetch_character_summary(char_name):
    url = CHAR_URL.format(char_name=char_name)
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    print(f"⚠️ Failed to fetch watched character: {url} ({response.status_code})")
    return None

# Example usage: load your character data from ladder JSONs
def main():
    # Refresh ladder-based character data first
    GetAllCharData()
    GetAllHCCharData()
#    copy_ladders_to_dailies()

    # Aggregate all characters from ladder snapshots
    all_characters = {}
    for ladder_file in ["sc_ladder.json", "hc_ladder.json"]:
        if os.path.exists(ladder_file):
            with open(ladder_file, "r") as f:
                for char in json.load(f):
                    char_name = char.get("charName") or char.get("Name")
                    if char_name:
                        all_characters[char_name] = char

    # Build the full set of characters we want to keep tracking
    monitored_names = set(all_characters.keys())
    monitored_names.update(get_snapshot_character_names())
    monitored_names.update(load_watchlist())
    monitored_names.update(load_account_discovered_names())

    # Fetch summaries for any characters that are not currently in ladder files
    for char_name in sorted(monitored_names):
        if char_name not in all_characters:
            char_data = fetch_character_summary(char_name)
            if char_data is not None:
                all_characters[char_name] = char_data

    process_characters(all_characters)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch ladder data and track character history.")
    parser.add_argument("--add-watched", "-a", action="append", help="Character name to add to the watchlist (can be used multiple times).")
    parser.add_argument("--list-watched", "-l", action="store_true", help="List watched characters and exit.")
    args = parser.parse_args()

    if args.add_watched or args.list_watched:
        if args.add_watched:
            for name in args.add_watched:
                if name:
                    add_to_watchlist(name)
        if args.list_watched:
            names = load_watchlist()
            print("Watched characters (from watched_characters.json):")
            for n in sorted(names):
                print(f" - {n}")
    else:
        main()