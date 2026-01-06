"""
Character storage helper module for handling sharded JSON files.

This module provides transparent sharding to keep individual files under GitHub's 100MB limit.
Characters are distributed across multiple files based on the first letter of their name.
"""

import json
import os
from typing import List, Dict, Any


# Sharding configuration: distribute characters across files by first letter
SHARD_RANGES = {
    'a-c': 'abc',
    'd-f': 'def',
    'g-i': 'ghi',
    'j-l': 'jkl',
    'm-o': 'mno',
    'p-r': 'pqr',
    's-u': 'stu',
    'v-z': 'vwxyz0123456789_',  # Include digits and underscore in last shard
}


def get_shard_name(char_name: str, league: str) -> str:
    """
    Determine which shard file a character belongs to based on its name.
    
    Args:
        char_name: Character name (can be from charName or Name field)
        league: 'sc' for softcore or 'hc' for hardcore
        
    Returns:
        Filename like 'sc_a-c.json' or 'hc_m-o.json'
    """
    if not char_name or char_name == "unknown":
        # Put unknown characters in the last shard
        return f"{league}_v-z.json"
    
    first_char = char_name[0].lower()
    
    for range_name, letters in SHARD_RANGES.items():
        if first_char in letters:
            return f"{league}_{range_name}.json"
    
    # Fallback for any unexpected characters
    return f"{league}_v-z.json"


def get_all_shard_names(league: str) -> List[str]:
    """
    Get list of all possible shard filenames for a league.
    
    Args:
        league: 'sc', 'hc', or 'both'
        
    Returns:
        List of filenames like ['sc_a-c.json', 'sc_d-f.json', ...]
    """
    filenames = []
    
    if league in ('sc', 'both'):
        filenames.extend([f"sc_{range_name}.json" for range_name in SHARD_RANGES.keys()])
    
    if league in ('hc', 'both'):
        filenames.extend([f"hc_{range_name}.json" for range_name in SHARD_RANGES.keys()])
    
    return filenames


def load_characters(league: str = "both") -> Dict[str, Any]:
    """
    Load all characters from sharded files.
    
    Args:
        league: 'sc' for softcore, 'hc' for hardcore, or 'both' for all characters
        
    Returns:
        Dictionary mapping character name to character data
    """
    existing_chars = {}
    
    shard_files = get_all_shard_names(league)
    
    # Try loading from sharded files
    files_loaded = []
    for filename in shard_files:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    shard_data = json.load(f)
                    for char in shard_data:
                        # Use charName (from ladder) or Name (from existing data)
                        char_name = char.get("charName") or char.get("Name", "unknown")
                        if char_name != "unknown":
                            existing_chars[char_name] = char
                    files_loaded.append(filename)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Failed to load {filename}: {e}")
    
    # Fallback to old combined files if no shards exist
    if not files_loaded:
        fallback_files = []
        if league in ('sc', 'both'):
            fallback_files.append('sc_characters.json')
        if league in ('hc', 'both'):
            fallback_files.append('hc_characters.json')
        if not any(os.path.exists(f) for f in fallback_files):
            fallback_files = ['all_characters.json']
        
        for filename in fallback_files:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        data = json.load(f)
                        for char in data:
                            char_name = char.get("charName") or char.get("Name", "unknown")
                            if char_name != "unknown":
                                existing_chars[char_name] = char
                        files_loaded.append(filename)
                        print(f"📋 Loaded from fallback file: {filename}")
                except (json.JSONDecodeError, IOError) as e:
                    print(f"⚠️ Failed to load {filename}: {e}")
    
    if files_loaded and league == "both":
        print(f"📋 Loaded {len(existing_chars)} characters from {len(files_loaded)} shard files")
    elif files_loaded:
        print(f"📋 Loaded {len(existing_chars)} {league.upper()} characters from {len(files_loaded)} shard files")
    
    return existing_chars


def save_characters(characters: List[Dict[str, Any]], league: str) -> None:
    """
    Save characters to sharded files based on their names.
    
    Args:
        characters: List of character dictionaries
        league: 'sc' for softcore or 'hc' for hardcore
    """
    # Group characters by shard
    shards = {range_name: [] for range_name in SHARD_RANGES.keys()}
    
    for char in characters:
        char_name = char.get("charName") or char.get("Name", "unknown")
        shard_file = get_shard_name(char_name, league)
        shard_key = shard_file.replace(f"{league}_", "").replace(".json", "")
        
        if shard_key in shards:
            shards[shard_key].append(char)
        else:
            # Shouldn't happen, but add to last shard as fallback
            shards['v-z'].append(char)
    
    # Save each shard to a file
    total_saved = 0
    for range_name, shard_chars in shards.items():
        if shard_chars:  # Only create files that have data
            filename = f"{league}_{range_name}.json"
            with open(filename, 'w') as f:
                json.dump(shard_chars, f, indent=2)
            
            file_size_mb = os.path.getsize(filename) / (1024 * 1024)
            total_saved += len(shard_chars)
            print(f"✅ Saved {len(shard_chars)} characters to {filename} ({file_size_mb:.1f} MB)")
    
    print(f"📊 Total {league.upper()} characters saved: {total_saved} across {sum(1 for s in shards.values() if s)} shards")


def load_characters_as_list(league: str = "both") -> List[Dict[str, Any]]:
    """
    Load all characters from sharded files as a list (for compatibility with existing code).
    
    Args:
        league: 'sc' for softcore, 'hc' for hardcore, or 'both' for all characters
        
    Returns:
        List of character dictionaries
    """
    char_dict = load_characters(league)
    return list(char_dict.values())
