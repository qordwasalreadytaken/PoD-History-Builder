import requests
import json

def GetSingleCharData(char_name):
    char_url = f"https://beta.pathofdiablo.com/api/characters/{char_name}/summary"
    response = requests.get(char_url)

    if response.status_code == 200:
        character_data = response.json()
        # Optional: save to file
        with open(f"{char_name}.json", "w") as file:
            json.dump(character_data, file, indent=2)
        print(f"✅ Saved character data for '{char_name}'")
        return character_data
    else:
        print(f"⚠️ Failed to fetch character: {char_url}")
        return None

# Example usage
if __name__ == "__main__":
    char_name = "sorcsallsuck"  # Replace with actual character name
    GetSingleCharData(char_name)
