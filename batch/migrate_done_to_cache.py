#!/usr/bin/env python3
"""
Migrate completion status from done.txt files to .completion_cache.json

This script performs two key tasks:
1. Scans all job directories for .done.txt files and adds them to the cache
2. Cleans existing cache records by converting full paths to basenames only

This is useful for:
- Migrating from the old done.txt-based completion tracking to the new cache-based system
- Cleaning up cache files that contain full paths instead of just job names

Usage:
    python migrate_done_to_cache.py <output_dir>

Example:
    python migrate_done_to_cache.py /content/drive/MyDrive/af2_output

The script will automatically:
- Load existing cache and normalize all keys to basenames (removes path prefixes)
- Scan for .done.txt files and add missing jobs
- Save a clean cache with basename-only keys
"""

import os
import sys
import json
import glob
from pathlib import Path


def load_completion_cache(output_dir):
    """Load completion cache from JSON file and normalize keys to basenames"""
    cache_file = os.path.join(output_dir, '.completion_cache.json')
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                raw_cache = json.load(f)

            # Normalize all keys to basenames only (remove path prefixes)
            normalized_cache = {}
            for key, value in raw_cache.items():
                # Extract basename from path (handles both / and \ separators)
                basename = os.path.basename(key.replace('\\', '/'))
                normalized_cache[basename] = value

            return normalized_cache
        except Exception as e:
            print(f"Warning: Could not load existing cache: {e}")
            return {}
    return {}


def save_completion_cache(output_dir, cache):
    """Save completion cache to JSON file"""
    cache_file = os.path.join(output_dir, '.completion_cache.json')
    try:
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2, sort_keys=True)
        print(f"\n✓ Cache saved to: {cache_file}")
    except Exception as e:
        print(f"✗ Error saving cache: {e}")
        sys.exit(1)


def find_completed_jobs(output_dir):
    """
    Scan output directory for job folders containing .done.txt files
    Returns a dictionary of {jobname: True} for all completed jobs
    """
    completed_jobs = {}

    if not os.path.exists(output_dir):
        print(f"✗ Error: Output directory does not exist: {output_dir}")
        sys.exit(1)

    # Get all subdirectories in output_dir
    subdirs = []
    try:
        for entry in os.scandir(output_dir):
            if entry.is_dir() and not entry.name.startswith('.'):
                subdirs.append(entry)
    except Exception as e:
        print(f"✗ Error scanning output directory: {e}")
        sys.exit(1)

    print(f"Scanning {len(subdirs)} job directories for .done.txt files...\n")

    found_count = 0
    for entry in subdirs:
        job_dir = entry.path
        jobname = entry.name

        # Look for any .done.txt file in this directory
        done_files = glob.glob(os.path.join(job_dir, '*.done.txt'))

        if done_files:
            completed_jobs[jobname] = True
            found_count += 1
            # Show first few characters of done file name
            done_file_name = os.path.basename(done_files[0])
            print(f"  ✓ Found: {jobname} (has {done_file_name})")

    print(f"\n✓ Found {found_count} completed jobs with .done.txt files")
    return completed_jobs


def merge_caches(existing_cache, new_entries):
    """
    Merge new entries into existing cache
    Returns the merged cache and statistics
    """
    merged = existing_cache.copy()

    added = 0
    already_exists = 0

    for jobname, status in new_entries.items():
        if jobname in merged:
            already_exists += 1
        else:
            merged[jobname] = status
            added += 1

    return merged, added, already_exists


def main():
    if len(sys.argv) != 2:
        print("Usage: python migrate_done_to_cache.py <output_dir>")
        print("\nExample:")
        print("  python migrate_done_to_cache.py /content/drive/MyDrive/af2_output")
        sys.exit(1)

    output_dir = sys.argv[1]

    print("=" * 70)
    print("Migrate done.txt completion status to .completion_cache.json")
    print("=" * 70)
    print(f"Output directory: {output_dir}\n")

    # Load existing cache (automatically normalizes paths to basenames)
    print("Loading and cleaning existing completion cache...")
    existing_cache = load_completion_cache(output_dir)
    print(f"✓ Loaded and normalized {len(existing_cache)} existing entries")
    print(f"  (All full paths converted to basenames only)\n")

    # Find all completed jobs
    print("=" * 70)
    completed_jobs = find_completed_jobs(output_dir)

    # Always save to clean up existing records, even if no new jobs found
    if not completed_jobs:
        print("\nNo new completed jobs found.")
        if existing_cache:
            print("Saving cleaned cache (full paths removed)...")
            save_completion_cache(output_dir, existing_cache)
            print("\n✓ Cache cleanup complete!")
        else:
            print("Nothing to update.")
        return

    # Merge with existing cache
    print("\n" + "=" * 70)
    print("Merging with existing cache...")
    merged_cache, added, already_exists = merge_caches(existing_cache, completed_jobs)

    print(f"  - New entries added: {added}")
    print(f"  - Already in cache: {already_exists}")
    print(f"  - Total entries in cache: {len(merged_cache)}")

    # Save updated cache
    print("\n" + "=" * 70)
    print("Saving updated cache...")
    save_completion_cache(output_dir, merged_cache)

    print("\n" + "=" * 70)
    print("✓ Migration complete!")
    print("=" * 70)
    print("\nSummary:")
    print(f"  - Jobs scanned: {len(completed_jobs)}")
    print(f"  - New jobs added to cache: {added}")
    print(f"  - Total jobs in cache: {len(merged_cache)}")
    print("\nAll entries are now stored as basenames (no path prefixes).")
    print("You can now safely use the notebook with cache-only completion tracking.")


if __name__ == "__main__":
    main()
