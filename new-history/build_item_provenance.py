import argparse
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SNAPSHOT_DIR = BASE_DIR / "snapshots"
DEFAULT_OUTPUT_FILE = BASE_DIR / "item_provenance.json"


def read_snapshot_history(path):
    try:
        with path.open(encoding="utf-8") as file:
            history = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Skipping {path.name}: {error}")
        return []

    if not isinstance(history, list):
        print(f"Skipping {path.name}: expected a list of snapshots")
        return []
    return history


def add_equipped_observations(index, history):
    observations_added = 0
    for snapshot in history:
        if not isinstance(snapshot, dict):
            continue

        timestamp = snapshot.get("timestamp")
        data = snapshot.get("data")
        if not isinstance(timestamp, str) or not isinstance(data, dict):
            continue

        character_name = data.get("Name")
        equipped_items = data.get("Equipped")
        if not isinstance(character_name, str) or not isinstance(equipped_items, list):
            continue

        for item in equipped_items:
            if not isinstance(item, dict):
                continue

            item_id = str(item.get("ID", "")).strip()
            if not item_id or item_id == "0":
                continue

            observation = {
                "timestamp": timestamp,
                "character": character_name,
                "equipped": item.get("Worn", ""),
            }
            item_entry = index.setdefault(
                item_id,
                {
                    "title": item.get("Title", "Unknown item"),
                    "tag": item.get("Tag", ""),
                    "observations": [],
                },
            )
            item_entry["observations"].append(observation)
            observations_added += 1
    return observations_added


def retain_ownership_changes(observations):
    ownership_changes = []
    previous_character = None
    for observation in observations:
        if observation["character"] == previous_character:
            continue
        ownership_changes.append(observation)
        previous_character = observation["character"]
    return ownership_changes


def build_provenance_index(snapshot_dir):
    index = {}
    snapshot_files = sorted(snapshot_dir.glob("*.json"))
    observations_added = 0

    for snapshot_file in snapshot_files:
        observations_added += add_equipped_observations(index, read_snapshot_history(snapshot_file))

    for item_entry in index.values():
        item_entry["observations"].sort(
            key=lambda observation: (observation["timestamp"], observation["character"], observation["equipped"])
        )
        item_entry["observations"] = retain_ownership_changes(item_entry["observations"])

    return index, len(snapshot_files), observations_added


def main():
    parser = argparse.ArgumentParser(
        description="Build an equipped-item provenance index from character snapshots."
    )
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    args = parser.parse_args()

    if not args.snapshot_dir.is_dir():
        raise SystemExit(f"Snapshot directory not found: {args.snapshot_dir}")

    index, file_count, observation_count = build_provenance_index(args.snapshot_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(index, file, indent=2)
        file.write("\n")

    print(
        f"Indexed {observation_count} equipped-item observations across "
        f"{file_count} snapshot files into {len(index)} item IDs."
    )


if __name__ == "__main__":
    main()