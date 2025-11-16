#!/usr/bin/env python3
"""
Track respec token usage by detecting skill point decreases in character histories.
Since skills can only decrease via respec tokens, any decrease indicates a respec.
"""

import json
import os
import re
from urllib.parse import parse_qs, urlparse
from collections import defaultdict
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================
# Minimum number of respecs required to appear on leaderboard
# Examples:
#   MIN_RESPECS = 1  -> Show everyone (good for early ladder, small datasets)
#   MIN_RESPECS = 3  -> Only heavy respecers (good for mature ladders)
#   MIN_RESPECS = 5  -> Only the most frequent respecers
MIN_RESPECS = 1

# Maximum number of entries in the leaderboard
TOP_N = 50
# ============================================================================


def extract_skills_from_url(url):
    """Extract the skills parameter from a build planner URL using regex for speed."""
    try:
        match = re.search(r'skills=([0-9]+)', url)
        return match.group(1) if match else ''
    except:
        return ''


def extract_stats_from_url(url):
    """Extract strength, dexterity, vitality, energy from URL using regex for speed."""
    try:
        # Use regex for faster parsing
        strength = re.search(r'strength=(\d+)', url)
        dexterity = re.search(r'dexterity=(\d+)', url)
        vitality = re.search(r'vitality=(\d+)', url)
        energy = re.search(r'energy=(\d+)', url)
        
        stats = {
            'strength': int(strength.group(1)) if strength else 0,
            'dexterity': int(dexterity.group(1)) if dexterity else 0,
            'vitality': int(vitality.group(1)) if vitality else 0,
            'energy': int(energy.group(1)) if energy else 0
        }
        return stats
    except:
        return {'strength': 0, 'dexterity': 0, 'vitality': 0, 'energy': 0}


def parse_skill_string(skills_str):
    """
    Convert skill string to list of integers.
    Format: Each skill takes 2 digits (00-99).
    Example: "20200001" = [20, 20, 00, 01]
    """
    if not skills_str:
        return []
    
    skill_points = []
    # Process string in pairs of 2 characters
    for i in range(0, len(skills_str), 2):
        if i + 1 < len(skills_str):
            try:
                points = int(skills_str[i:i+2])
                skill_points.append(points)
            except ValueError:
                skill_points.append(0)
        else:
            # Odd length string, shouldn't happen but handle it
            skill_points.append(0)
    
    return skill_points


def detect_respec(prev_skills, curr_skills):
    """
    Detect if a respec occurred by checking if any skill points decreased.
    
    Returns: (is_respec, details)
        is_respec: True if any skill decreased
        details: dict with skill indices that decreased and their changes
    """
    if not prev_skills or not curr_skills:
        return False, {}
    
    # Ensure equal length (pad shorter one with zeros)
    max_len = max(len(prev_skills), len(curr_skills))
    prev_skills = prev_skills + [0] * (max_len - len(prev_skills))
    curr_skills = curr_skills + [0] * (max_len - len(curr_skills))
    
    decreases = {}
    for i, (prev, curr) in enumerate(zip(prev_skills, curr_skills)):
        if curr < prev:  # Skill points decreased
            decreases[i] = {
                'from': prev,
                'to': curr,
                'decrease': prev - curr
            }
    
    return len(decreases) > 0, decreases


def detect_stat_respec(prev_stats, curr_stats):
    """
    Detect if a respec occurred by checking if any stat points decreased.
    Stats can only decrease via respec tokens.
    
    Returns: (is_respec, details)
        is_respec: True if any stat decreased
        details: dict with stats that decreased and their changes
    """
    if not prev_stats or not curr_stats:
        return False, {}
    
    decreases = {}
    for stat in ['strength', 'dexterity', 'vitality', 'energy']:
        prev_val = prev_stats.get(stat, 0)
        curr_val = curr_stats.get(stat, 0)
        if curr_val < prev_val:
            decreases[stat] = {
                'from': prev_val,
                'to': curr_val,
                'decrease': prev_val - curr_val
            }
    
    return len(decreases) > 0, decreases


def analyze_character_history(history_file):
    """
    Analyze a character's history file for respec events.
    Detects respecs by checking for skill point OR stat point decreases.
    
    Returns: list of respec events with timestamps and details
    """
    if not os.path.exists(history_file):
        return []
    
    with open(history_file, 'r') as f:
        history = json.load(f)
    
    if len(history) < 2:
        return []  # Need at least 2 snapshots to compare
    
    respecs = []
    prev_snapshot = history[0]
    prev_skills_str = extract_skills_from_url(prev_snapshot.get('url', ''))
    prev_skills = parse_skill_string(prev_skills_str)
    prev_stats = extract_stats_from_url(prev_snapshot.get('url', ''))
    
    for i, snapshot in enumerate(history[1:], start=1):
        curr_skills_str = extract_skills_from_url(snapshot.get('url', ''))
        curr_skills = parse_skill_string(curr_skills_str)
        curr_stats = extract_stats_from_url(snapshot.get('url', ''))
        
        # Check both skills and stats for decreases
        is_skill_respec, skill_details = detect_respec(prev_skills, curr_skills)
        is_stat_respec, stat_details = detect_stat_respec(prev_stats, curr_stats)
        
        # Either type of decrease indicates a respec
        is_respec = is_skill_respec or is_stat_respec
        
        if is_respec:
            respecs.append({
                'index': i,
                'timestamp': snapshot.get('timestamp', 'unknown'),
                'prev_timestamp': prev_snapshot.get('timestamp', 'unknown'),
                'url_before': prev_snapshot.get('url', ''),
                'url_after': snapshot.get('url', ''),
                'character_name': snapshot.get('originalName', ''),
                'skills_decreased': len(skill_details),
                'stats_decreased': len(stat_details),
                'total_points_removed': sum(d['decrease'] for d in skill_details.values()),
                'total_stats_removed': sum(d['decrease'] for d in stat_details.values()),
                'skill_details': skill_details,
                'stat_details': stat_details
            })
        
        prev_snapshot = snapshot
        prev_skills = curr_skills
        prev_stats = curr_stats
    
    return respecs


def scan_all_characters():
    """
    Scan all character history files and count respecs.
    
    Returns: dict mapping character name to respec data
    """
    snapshots_dir = 'snapshots'
    if not os.path.exists(snapshots_dir):
        print(f"⚠️ Snapshots directory not found: {snapshots_dir}")
        return {}
    
    character_respecs = {}
    files = [f for f in os.listdir(snapshots_dir) if f.endswith('.json')]
    total_files = len(files)
    
    for idx, filename in enumerate(files, 1):
        if idx % 100 == 0:
            print(f"  Processed {idx}/{total_files} files...", flush=True)
        
        char_name = filename[:-5]  # Remove .json extension
        filepath = os.path.join(snapshots_dir, filename)
        
        respecs = analyze_character_history(filepath)
        
        if respecs:
            character_respecs[char_name] = {
                'respecs': respecs,
                'total_respecs': len(respecs),
                'total_points_removed': sum(r['total_points_removed'] for r in respecs),
                'total_stats_removed': sum(r['total_stats_removed'] for r in respecs)
            }
    
    return character_respecs


def generate_leaderboard(character_respecs, top_n=50, min_respecs=1):
    """
    Generate a leaderboard of characters by respec count.
    
    Args:
        character_respecs: dict of character data
        top_n: maximum number of entries to return
        min_respecs: minimum number of respecs required to be included
    
    Returns: list of (char_name, respec_count, total_points_removed)
    """
    leaderboard = []
    
    for char_name, data in character_respecs.items():
        # Only include characters with at least min_respecs
        if data['total_respecs'] >= min_respecs:
            leaderboard.append((
                char_name,
                data['total_respecs'],
                data['total_points_removed']
            ))
    
    # Sort by respec count (descending), then by total points removed
    leaderboard.sort(key=lambda x: (x[1], x[2]), reverse=True)
    
    return leaderboard[:top_n]


def main():
    print("🔍 Scanning character histories for respec token usage...")
    print(f"   Configuration: MIN_RESPECS={MIN_RESPECS}, TOP_N={TOP_N}")
    print()
    
    character_respecs = scan_all_characters()
    
    if not character_respecs:
        print("No respecs detected in character histories.")
        return
    
    print(f"✅ Found {len(character_respecs)} characters with respecs")
    print()
    
    # Generate leaderboard with configured filters
    leaderboard = generate_leaderboard(character_respecs, top_n=TOP_N, min_respecs=MIN_RESPECS)
    
    # Show filter info if filtering is active
    if MIN_RESPECS > 1:
        filtered_count = len([c for c in character_respecs.values() if c['total_respecs'] >= MIN_RESPECS])
        print(f"📊 Showing {filtered_count} characters with {MIN_RESPECS}+ respecs (filtered from {len(character_respecs)} total)")
        print()
    
    print("=" * 80)
    print(f"RESPEC TOKEN USAGE LEADERBOARD (Top {TOP_N}, Min {MIN_RESPECS} respecs)")
    print("=" * 80)
    print(f"{'Rank':<6} {'Character':<30} {'Respecs':<10} {'Total Points Reset'}")
    print("-" * 80)
    
    for rank, (char_name, respec_count, points_removed) in enumerate(leaderboard, start=1):
        print(f"{rank:<6} {char_name:<30} {respec_count:<10} {points_removed}")
    
    print("=" * 80)
    print()
    
    # Save detailed results to JSON
    output = {
        'generated_at': datetime.now().isoformat(),
        'config': {
            'min_respecs': MIN_RESPECS,
            'top_n': TOP_N
        },
        'total_characters_with_respecs': len(character_respecs),
        'characters_shown': len(leaderboard),
        'leaderboard': [
            {
                'rank': rank,
                'character': char_name,
                'total_respecs': respec_count,
                'total_points_removed': points_removed
            }
            for rank, (char_name, respec_count, points_removed) in enumerate(leaderboard, start=1)
        ],
        'detailed_data': {
            char_name: data
            for char_name, data in character_respecs.items()
            if data['total_respecs'] >= MIN_RESPECS  # Only include characters meeting threshold
        }
    }
    
    output_file = 'respec_leaderboard.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"📊 Detailed results saved to: {output_file}")
    
    # Show some interesting stats
    total_respecs = sum(data['total_respecs'] for data in character_respecs.values())
    total_points = sum(data['total_points_removed'] for data in character_respecs.values())
    total_stats = sum(data['total_stats_removed'] for data in character_respecs.values())
    avg_respecs = total_respecs / len(character_respecs)
    
    print()
    print("SUMMARY STATISTICS")
    print(f"  Total characters analyzed: {len(os.listdir('snapshots'))}")
    print(f"  Characters with respecs: {len(character_respecs)}")
    print(f"  Total respec events: {total_respecs}")
    print(f"  Total skill points reset: {total_points}")
    print(f"  Total stat points reset: {total_stats}")
    print(f"  Average respecs per character: {avg_respecs:.2f}")
    
    # Find character with most respecs
    if leaderboard:
        top_char = leaderboard[0]
        print(f"  Most respecs: {top_char[0]} ({top_char[1]} times)")


if __name__ == "__main__":
    main()
