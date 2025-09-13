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

def fetch_char_summaries(characters):
    char_url = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"
    final_data = []
    for character in characters:
        char_name = character.get("charName", "unknown")
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

#    class_counts = count_classes(unique_characters) # if we wanted a pie chart generated here, i think it's fine to keep in makehome
#    generate_pie_chart_all(class_counts)

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
#    with open("sc_ladder.json", "w") as file:
#        json.dump(character_data, file, indent=2)
    return character_data
#    print(f"✅ Saved {len(character_data)} characters to sc_ladder.json (top 1,000 + class-specific)")


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
#    with open("hc_ladder.json", "w") as file:
#        json.dump(character_data, file, indent=2)
    return character_data
#    print(f"✅ Saved {len(character_data)} unique characters to hc_ladder.json")


def main():
    sc_data = GetAllCharData()
    hc_data = GetAllHCCharData()

    combined_data = sc_data + hc_data

    with open("all_characters.json", "w") as file:
        json.dump(combined_data, file, indent=2)

    print(f"✅ Saved {len(combined_data)} total characters to all_characters.json")


if __name__ == "__main__":
    main()
