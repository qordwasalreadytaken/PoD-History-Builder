import argparse
import json
import os
import time
from datetime import datetime

import requests


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)

DEFAULT_PLAYERLIST = os.path.join(REPO_ROOT, "playerlist.txt")
WATCHLIST_FILE = os.path.join(BASE_DIR, "watched_characters.json")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")
OUTPUT_FILE = os.path.join(BASE_DIR, "account_last_characters.json")

ACCOUNT_LAST_CHAR_URL = "https://beta.pathofdiablo.com/api/accounts/{account}/last-character"
CHAR_SUMMARY_URL = "https://beta.pathofdiablo.com/api/characters/{char_name}/summary"


def read_lines(path):
    with open(path, "r") as f:
        rows = [line.strip() for line in f]
    return [r for r in rows if r and not r.startswith("#")]


def normalize_character_name(name):
    if not name:
        return None
    return str(name).strip()


def load_json_list(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        pass
    return []


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def load_snapshot_names():
    if not os.path.isdir(SNAPSHOT_DIR):
        return set()
    names = set()
    for entry in os.listdir(SNAPSHOT_DIR):
        if entry.endswith(".json"):
            names.add(os.path.splitext(entry)[0].lower())
    return names


def fetch_with_retry(session, url, timeout, max_retries):
    for attempt in range(max_retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code in (429, 500, 502, 503, 504):
                if attempt < max_retries:
                    time.sleep(min(2 ** attempt, 8))
                    continue
            return response
        except requests.RequestException:
            if attempt < max_retries:
                time.sleep(min(2 ** attempt, 8))
                continue
            return None
    return None


def fetch_last_character_for_account(session, account, timeout, max_retries):
    url = ACCOUNT_LAST_CHAR_URL.format(account=account)
    response = fetch_with_retry(session, url, timeout=timeout, max_retries=max_retries)
    if response is None:
        return None, "network_error"
    if response.status_code != 200:
        return None, f"http_{response.status_code}"

    try:
        payload = response.json()
    except ValueError:
        return None, "invalid_json"

    name = normalize_character_name(payload.get("CharacterName"))
    if not name:
        return None, "missing_character"
    return name, None


def fetch_character_summary(session, char_name, timeout, max_retries):
    url = CHAR_SUMMARY_URL.format(char_name=char_name)
    response = fetch_with_retry(session, url, timeout=timeout, max_retries=max_retries)
    if response is None or response.status_code != 200:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def seed_snapshot(char_name, summary, timestamp):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    snapshot_path = os.path.join(SNAPSHOT_DIR, f"{char_name.lower()}.json")

    if os.path.exists(snapshot_path):
        try:
            with open(snapshot_path, "r") as f:
                history = json.load(f)
            if not isinstance(history, list):
                history = []
        except Exception:
            history = []
    else:
        history = []

    history.append({"timestamp": timestamp, "data": summary})
    save_json(snapshot_path, history)


def apply_slice(values, shard_count, shard_index):
    if shard_count <= 1:
        return values
    return [v for i, v in enumerate(values) if i % shard_count == shard_index]


def main():
    parser = argparse.ArgumentParser(description="Import last played character names for account list.")
    parser.add_argument("--accounts-file", default=DEFAULT_PLAYERLIST, help="Path to account list file")
    parser.add_argument("--output-file", default=OUTPUT_FILE, help="Path to discovered character list JSON")
    parser.add_argument("--throttle-ms", type=int, default=80, help="Delay between account requests in milliseconds")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=3, help="Retry count for transient HTTP failures")
    parser.add_argument("--seed-snapshots", action="store_true", help="Also fetch summary and write snapshot entries")
    parser.add_argument("--append-watchlist", action="store_true", help="Append discovered names to watched_characters.json")
    parser.add_argument("--shard-count", type=int, default=1, help="Total shard count for splitting the account list")
    parser.add_argument("--shard-index", type=int, default=0, help="Shard index to process (0-based)")
    args = parser.parse_args()

    if args.shard_count < 1:
        raise ValueError("--shard-count must be >= 1")
    if args.shard_index < 0 or args.shard_index >= args.shard_count:
        raise ValueError("--shard-index must be in range [0, shard-count)")

    accounts = read_lines(args.accounts_file)
    # Keep first occurrence only to reduce unnecessary API calls.
    seen_accounts = set()
    deduped_accounts = []
    for acct in accounts:
        key = acct.lower()
        if key in seen_accounts:
            continue
        seen_accounts.add(key)
        deduped_accounts.append(acct)

    sliced_accounts = apply_slice(deduped_accounts, args.shard_count, args.shard_index)

    session = requests.Session()
    discovered = {}
    failures = {}

    start = time.time()
    for i, account in enumerate(sliced_accounts, start=1):
        char_name, err = fetch_last_character_for_account(
            session,
            account,
            timeout=args.timeout,
            max_retries=args.max_retries,
        )
        if char_name:
            discovered[char_name.lower()] = char_name
        else:
            failures[account] = err

        if i % 500 == 0 or i == len(sliced_accounts):
            elapsed = time.time() - start
            print(
                f"Processed {i}/{len(sliced_accounts)} accounts | "
                f"found={len(discovered)} failed={len(failures)} elapsed={elapsed:.1f}s"
            )
        if args.throttle_ms > 0:
            time.sleep(args.throttle_ms / 1000.0)

    discovered_names = sorted(discovered.values(), key=lambda x: x.lower())

    existing_output = load_json_list(args.output_file)
    merged_output = sorted(set(existing_output).union(discovered_names), key=lambda x: x.lower())
    save_json(args.output_file, merged_output)

    if args.append_watchlist:
        existing_watchlist = load_json_list(WATCHLIST_FILE)
        merged_watchlist = sorted(set(existing_watchlist).union(discovered_names), key=lambda x: x.lower())
        save_json(WATCHLIST_FILE, merged_watchlist)

    seeded_count = 0
    if args.seed_snapshots:
        timestamp = datetime.utcnow().isoformat() + "Z"
        existing_snapshot_names = load_snapshot_names()
        for char_name in discovered_names:
            if char_name.lower() in existing_snapshot_names:
                continue
            summary = fetch_character_summary(
                session,
                char_name,
                timeout=args.timeout,
                max_retries=args.max_retries,
            )
            if summary is None:
                continue
            seed_snapshot(char_name, summary, timestamp)
            seeded_count += 1

    report = {
        "accounts_total": len(accounts),
        "accounts_unique": len(deduped_accounts),
        "accounts_processed": len(sliced_accounts),
        "shard_count": args.shard_count,
        "shard_index": args.shard_index,
        "characters_discovered_in_run": len(discovered_names),
        "characters_saved_total": len(merged_output),
        "failures": failures,
        "seed_snapshots": args.seed_snapshots,
        "snapshots_seeded_in_run": seeded_count,
        "append_watchlist": args.append_watchlist,
    }
    report_file = os.path.join(BASE_DIR, f"account_last_characters_report_{args.shard_index}.json")
    save_json(report_file, report)

    print("Done.")
    print(json.dumps({k: v for k, v in report.items() if k != "failures"}, indent=2))
    if failures:
        print(f"Failures captured in report: {report_file}")


if __name__ == "__main__":
    main()
