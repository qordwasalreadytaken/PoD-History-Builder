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

# Define snapshot directory for per-character history
SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'snapshots')
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

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
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'character_index.json')
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
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"

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

        response = requests.get(char_url.format(char_name=char_name))
        if response.status_code == 200:
            character_data.append(response.json())
        else:
            print(f"⚠️ Failed to fetch character: {char_name}")

    # Step 6: Save the extended character list
    with open("sc_ladder.json", "w") as file:
        json.dump(character_data, file, indent=2)

    print(f"✅ Saved {len(character_data)} characters to sc_ladder.json (top 1,000 + class-specific)")


def GetAllHCCharData():
    base_ladder_url = "https://beta.pathofdiablo.com/api/ladder/13/1/"  # Softcore
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"

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

        response = requests.get(char_url.format(char_name=char_name))
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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    new_history_dir = script_dir
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


def character_changed(new_data, last_data):
    # Only compare points in skills and names of equipped items
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

    return skills_new != skills_last or equipped_new != equipped_last

def load_character_history(char_name):
    path = os.path.join(SNAPSHOT_DIR, f'{char_name}.json')
    # Always load using lowercase filename
    path = os.path.join(SNAPSHOT_DIR, f'{char_name.lower()}.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return []

def process_characters(characters):
    timestamp = datetime.utcnow().isoformat() + 'Z'
    recently_changed = []
    for char_name, char_data in characters.items():
        history = load_character_history(char_name)
        last_snapshot = history[-1]['data'] if history else None
        if last_snapshot is None or character_changed(char_data, last_snapshot):
            history.append({
                'timestamp': timestamp,
                'data': char_data
            })
            save_character_history(char_name, history)
            recently_changed.append(char_name)
    # Write recently changed characters to recently_changed.json (overwrite each run)
    recently_changed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recently_changed.json')
    with open(recently_changed_path, 'w') as f:
        json.dump(recently_changed, f, indent=2)
    return recently_changed

# Example usage: load your character data from ladder JSONs
def main():
    GetAllCharData()
    GetAllHCCharData()
    copy_ladders_to_dailies()
#    create_character_index()
    all_characters = {}
    for ladder_file in ["sc_ladder.json", "hc_ladder.json"]:
        if os.path.exists(ladder_file):
            with open(ladder_file, "r") as f:
                for char in json.load(f):
                    char_name = char.get("charName") or char.get("Name")
                    if char_name:
                        all_characters[char_name] = char
    process_characters(all_characters)

if __name__ == "__main__":
    main()