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

# Import sharding helper
from character_storage import load_characters, save_characters


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

def load_existing_characters(league="both"):
    """Load the list of characters we've seen before from sharded files."""
    # Use the sharding helper - it returns a dict of char_name -> char_data
    return load_characters(league)

def merge_character_lists(current_ladder_chars, existing_chars):
    """Merge current ladder characters with existing character list."""
    # Start with existing characters, normalize to use actual character names as keys
    all_chars = {}
    
    # Add existing characters (using their Name field as key)
    for char_name, char_data in existing_chars.items():
        if char_name != "unknown":
            all_chars[char_name] = char_data
    
    # Track duplicates for debugging
    duplicates = 0
    new_chars = 0
    
    # Add/update with current ladder characters (using their charName field as key)
    # This will overwrite existing chars if they're still on ladder (getting fresh data)
    for char in current_ladder_chars:
        char_name = char.get("charName", "unknown")
        if char_name != "unknown":  # Only add characters with valid names
            if char_name in all_chars:
                duplicates += 1
            else:
                new_chars += 1
            all_chars[char_name] = char  # Use fresh ladder data
    
    print(f"📊 Merge stats: {new_chars} new ladder chars, {duplicates} updated (were in history)")
    return list(all_chars.values())

def fetch_char_summaries(characters):
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"
    final_data = []
    for character in characters:
        # Handle both ladder format (charName) and existing format (Name)
        char_name = character.get("charName") or character.get("Name", "unknown")
        char_id = character.get("id", None)

        if char_name == "unknown":
            char_name = f"unknown_{char_id or int(time.time() * 1000)}"

        response = requests.get(char_url.format(char_name=char_name))
        if response.status_code == 200:
            final_data.append(response.json())
        else:
            print(f"⚠️ Failed to fetch character summary: {char_name}")
    return final_data


def GetAllCharData():
    base_ladder_url = "https://beta.pathofdiablo.com/api/ladder/13/0/"  # Softcore
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"

    # Load existing characters we've seen before
    existing_characters = load_existing_characters("sc")
    print(f"📋 Found {len(existing_characters)} existing SC characters")

    # Step 1: Fetch top 1,000 characters (pages 0 to 5)
    # Step 1: Fetch top 1,000 characters (pages 0 to 5)
    current_ladder_chars = fetch_ladder_characters(f"{base_ladder_url}0/", start_page=0, end_page=5)
#    all_characters = fetch_ladder_characters(base_ladder_url, start_page=0, end_page=5)
#    all_characters = fetch_ladder_characters(base_ladder_url, start_page=1, end_page=5)
    top_1000_characters = {char["charName"]: char for char in current_ladder_chars}.values()

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
        current_ladder_chars.extend(class_characters)  # Combine lists

    # Step 4: Merge current ladder characters with existing characters
    all_ladder_chars = merge_character_lists(current_ladder_chars, existing_characters)
    unique_characters = {char.get("charName") or char.get("Name", "unknown"): char for char in all_ladder_chars}.values()
    
    # Count character types for debugging
    ladder_chars = sum(1 for char in unique_characters if char.get("charName"))
    existing_chars = sum(1 for char in unique_characters if char.get("Name") and not char.get("charName"))
    print(f"🔄 Total characters to fetch: {len(list(unique_characters))} (📈 {ladder_chars} from ladder, 💾 {existing_chars} from history)")

#    class_counts = count_classes(unique_characters) # if we wanted a pie chart generated here, i think it's fine to keep in makehome
#    generate_pie_chart_all(class_counts)

    # Step 5: Fetch complete character data
    character_data = []
    for character in unique_characters:
        # Handle both ladder format (charName) and existing format (Name)
        char_name = character.get("charName") or character.get("Name", "unknown")
        char_id = character.get("id", None)

        if char_name == "unknown":
            char_name = f"unknown_{char_id or int(time.time() * 1000)}"

        response = requests.get(char_url.format(char_name=char_name))
        if response.status_code == 200:
            character_data.append(response.json())
        else:
            print(f"⚠️ Failed to fetch character: {char_name}")

    # Step 6: Save the extended character list
#    with open("sc_ladder.json", "w") as file:
#        json.dump(character_data, file, indent=2)
    return character_data
#    print(f"✅ Saved {len(character_data)} characters to sc_ladder.json (top 1,000 + class-specific)")


def GetAllHCCharData():
    base_ladder_url = "https://beta.pathofdiablo.com/api/ladder/13/1/"  # Hardcore
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"

    # Load existing characters we've seen before
    existing_characters = load_existing_characters("hc")
    print(f"📋 Found {len(existing_characters)} existing HC characters")

    # Fetch top 1,000 characters
#    all_characters = fetch_ladder_characters(f"{base_ladder_url}0/", 5)
    current_ladder_chars = fetch_ladder_characters(base_ladder_url, start_page=0, end_page=5)

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
        current_ladder_chars.extend(class_characters)

    # Merge current ladder characters with existing characters (some appear in both top 1,000 and top 200 class rankings)
    all_ladder_chars = merge_character_lists(current_ladder_chars, existing_characters)
    unique_characters = {char.get("charName") or char.get("Name", "unknown"): char for char in all_ladder_chars}.values()
    
    # Count character types for debugging
    ladder_chars = sum(1 for char in unique_characters if char.get("charName"))
    existing_chars = sum(1 for char in unique_characters if char.get("Name") and not char.get("charName"))
    print(f"🔄 Total HC characters to fetch: {len(list(unique_characters))} (📈 {ladder_chars} from ladder, 💾 {existing_chars} from history)")

    character_data = []
    for character in unique_characters:
        # Handle both ladder format (charName) and existing format (Name)
        char_name = character.get("charName") or character.get("Name", "unknown")
        char_id = character.get("id", None)

        if char_name == "unknown":
            char_name = f"unknown_{char_id or int(time.time() * 1000)}"

        response = requests.get(char_url.format(char_name=char_name))
        if response.status_code == 200:
            character_data.append(response.json())
        else:
            print(f"⚠️ Failed to fetch character: https://beta.pathofdiablo.com/api/characters/{char_name}/summary")

    # Save as one big JSON
#    with open("hc_ladder.json", "w") as file:
#        json.dump(character_data, file, indent=2)
    return character_data
#    print(f"✅ Saved {len(character_data)} unique characters to hc_ladder.json")


def save_split_files(sc_data, hc_data):
    """Save character data to sharded files."""
    
    # Save SC characters to sharded files
    save_characters(sc_data, 'sc')
    
    # Save HC characters to sharded files
    save_characters(hc_data, 'hc')
    
    print(f"📊 Total characters: {len(sc_data) + len(hc_data)} (sharded by name)")
    
    return sc_data + hc_data

def main():
    sc_data = GetAllCharData()
    hc_data = GetAllHCCharData()

    combined_data = save_split_files(sc_data, hc_data)
    
    # Show file sizes for monitoring (all shard files)
    from character_storage import get_all_shard_names
    all_shards = get_all_shard_names('both')
    total_size = 0
    for filename in all_shards:
        if os.path.exists(filename):
            size_mb = os.path.getsize(filename) / (1024 * 1024)
            total_size += size_mb
            print(f"📊 {filename}: {size_mb:.1f} MB")
    print(f"💾 Total storage: {total_size:.1f} MB across {len([f for f in all_shards if os.path.exists(f)])} shard files")


if __name__ == "__main__":
    main()
