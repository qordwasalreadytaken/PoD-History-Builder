import argparse
import json
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")


def dedup_file(path: str) -> None:
    """Deduplicate snapshots in a single file by timestamp.

    For each timestamp, keep the latest snapshot entry (last one in the
    original file). Resulting snapshots are written back sorted by
    timestamp so history remains chronological.
    """

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ Skipping {os.path.basename(path)} (failed to read/parse): {e}")
        return

    if not isinstance(data, list):
        print(f"⚠️ Skipping {os.path.basename(path)} (expected list at top level)")
        return

    original_len = len(data)
    if original_len <= 1:
        return

    by_timestamp = {}
    for entry in data:
        ts = entry.get("timestamp")
        if not isinstance(ts, str):
            # Keep entries without a usable timestamp by making up a
            # unique key based on position and current time
            ts = f"__no_ts__-{len(by_timestamp)}"
        by_timestamp[ts] = entry

    # Separate real timestamps from synthetic ones used for malformed entries
    real_items = [(ts, e) for ts, e in by_timestamp.items() if not ts.startswith("__no_ts__-")]
    other_items = [(ts, e) for ts, e in by_timestamp.items() if ts.startswith("__no_ts__-")]

    # Sort real timestamps chronologically; they are ISO 8601 strings
    try:
        real_items.sort(key=lambda item: item[0])
    except Exception:
        # Fallback to original string ordering if parsing fails for some
        # reason
        real_items.sort(key=lambda item: item[0])

    new_data = [e for _, e in real_items] + [e for _, e in other_items]

    if len(new_data) == original_len:
        # Nothing was actually removed
        return

    with open(path, "w") as f:
        json.dump(new_data, f, indent=2)

    print(f"✅ Deduplicated {os.path.basename(path)}: {original_len} → {len(new_data)} entries")


def dedup_all_snapshots() -> None:
    if not os.path.isdir(SNAPSHOT_DIR):
        print(f"No snapshot directory found at {SNAPSHOT_DIR}")
        return

    for entry in os.listdir(SNAPSHOT_DIR):
        if not entry.endswith(".json"):
            continue
        full_path = os.path.join(SNAPSHOT_DIR, entry)
        if os.path.isfile(full_path):
            dedup_file(full_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deduplicate character snapshot JSON files by timestamp.")
    parser.add_argument("--file", "-f", help="Specific snapshot file (character name or path) to deduplicate.")
    parser.add_argument("--all", action="store_true", help="Deduplicate all snapshot files in the snapshots directory.")
    args = parser.parse_args()

    if args.file:
        # Allow either bare character name (e.g., devoraan) or a full path
        path = args.file
        if not os.path.isabs(path) and not path.endswith(".json"):
            path = os.path.join(SNAPSHOT_DIR, f"{path.lower()}.json")
        elif not os.path.isabs(path):
            path = os.path.join(SNAPSHOT_DIR, path)

        if not os.path.exists(path):
            print(f"⚠️ File not found: {path}")
            return
        dedup_file(path)
    elif args.all:
        dedup_all_snapshots()
    else:
        print("Specify either --file NAME or --all")


if __name__ == "__main__":
    main()
