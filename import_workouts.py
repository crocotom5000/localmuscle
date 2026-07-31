#!/usr/bin/env python3
"""
Import historical workouts from a text file.

Usage:
    python3 import_workouts.py workouts.txt [--dry-run]

Format expected:
    7/22 eos lower 1
    Back squat 6x205, 8x155, 8x155 stronggg
    bench 3 6-10 bench 135,135,135
    RDL 225 6,5,5
    ...
"""

import sys
import re
import sqlite3
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db import get_db, init_db
from workout import resolve_alias, fmt_weight

DAY_MAP = {
    "upper 1": 1,
    "upper 2": 3,
    "lower 1": 2,
    "lower 2": 4,
}


def parse_date(line):
    """Parse date line like '7/22 eos lower 1' -> (date, day_number)."""
    match = re.match(r"(\d+)/(\d+)\s+\w+\s+(lower|upper)\s+(\d+)", line, re.IGNORECASE)
    if not match:
        return None, None
    month = int(match.group(1))
    day_num_in_month = int(match.group(2))
    day_type = f"{match.group(3).lower()} {match.group(4)}"
    day_number = DAY_MAP.get(day_type)
    return date(2026, month, day_num_in_month), day_number


def parse_exercise_line(line):
    """Parse a single exercise line.
    
    Returns (exercise_name, [(reps, weight, note)], raw_name).
    
    Formats handled:
    - "bench 3 6-10 135,135,135" → 6x135, 6x135, 6x135
    - "bench 3 6-10 bench 135,135,135" → 6x135, 6x135, 6x135
    - "Back squat 6x205, 8x155" → 6x205, 8x155
    - "RDL 225 6,5,5" → 6x225, 5x225, 5x225
    - "Leg extension 3x10 100, 110" → 10x100, 10x110
    - "calf raise 8x180 5 sets" → 8x180 x5
    - "EZ bar curl arsenal 50 8,8,7" → 8x50, 8x50, 7x50
    """
    # Skip non-exercise lines
    if re.match(r"^(weight|orlando|switch|blister|silicone|no weight|trust|i think|a bit)", line.lower()):
        return None, [], None
    if not any(c.isdigit() for c in line):
        return None, [], None
    
    # Normalize tabs to spaces
    line = line.replace("\t", " ")
    
    # Extract note from end of line
    note = None
    last_num_end = 0
    for m in re.finditer(r"\d+(?:\.\d+)?", line):
        last_num_end = m.end()
    after_last = line[last_num_end:].strip().rstrip(",").strip()
    if after_last and len(after_last.split()) <= 3:
        note = after_last
    
    # Equipment/qualifier words that can appear in exercise names
    equipment_words = [
        "bar", "db", "dumbbell", "machine", "nautilus", "arsenal", "synergy",
        "humansport", "hammer", "life fitness", "fitbit", "hoist", "decline",
        "incline", "flat", "ez", "cable", "smith", "seated", "lying", "standing",
        "single", "iso", "lateral", "weighted", "bb"
    ]
    
    # Find exercise name: everything before the first number (handles tabs too)
    # Also handle cases like "press down4" where there's no space before digit
    name_match = re.match(r"^([a-zA-Z\s\-]+?)\s+\d", line)
    if not name_match:
        # Try to find name ending at word boundary before digit
        name_match = re.match(r"^([a-zA-Z\s\-]+?\w)(?=\s*\d)", line)
    if not name_match:
        return None, [], None
    
    raw_name = name_match.group(1).strip()
    
    # Try to resolve the full name first
    exercise_name = resolve_alias(raw_name)
    
    # If not found, try stripping equipment words from the end
    if not exercise_name:
        words = raw_name.split()
        # Try removing trailing equipment words
        for i in range(len(words), 0, -1):
            candidate = " ".join(words[:i])
            exercise_name = resolve_alias(candidate)
            if exercise_name:
                raw_name = candidate
                break
    
    if not exercise_name:
        return None, [], raw_name
    
    # Get the rest of the line after exercise name
    rest = line[name_match.end() - 1:].strip()  # -1 to include the first digit
    
    sets = []
    
    # Check for NxW format (e.g., "6x205, 8x155")
    nxw_matches = list(re.finditer(r"(\d+)\s*x\s*(\d+(?:\.\d+)?)", rest))
    
    if nxw_matches:
        # Has explicit NxW format
        for m in nxw_matches:
            reps = int(m.group(1))
            weight = float(m.group(2))
            if weight >= 10:  # Real weight
                sets.append((reps, weight, note))
        
        # Check for "N sets" pattern (e.g., "8x180 5 sets")
        sets_match = re.search(r"(\d+)\s*(?:sets?|reps?)", rest, re.IGNORECASE)
        if sets_match and nxw_matches:
            extra_sets = int(sets_match.group(1)) - 1
            if extra_sets > 0 and sets:
                last_set = sets[-1]
                for _ in range(extra_sets):
                    sets.append(last_set)
    else:
        # No NxW format - parse weight-only or target notation
        # Remove target notation like "3 8-12", "4 8-12", "1x5-8", "3x10"
        # These indicate prescription, not performance
        target_match = re.search(r"(?:^|\s)(\d+)\s+(\d+)-(\d+)", rest)
        target_match2 = re.search(r"(?:^|\s)(\d+)x(\d+)-(\d+)", rest)
        target_match3 = re.search(r"(?:^|\s)(\d+)x(\d+)(?:\s|$)", rest)
        
        target_reps = None
        
        if target_match:
            # "3 8-12" format
            target_reps = int(target_match.group(2))  # Lower range
            # Remove target notation from rest
            rest = rest[:target_match.start()] + rest[target_match.end():]
        elif target_match2:
            # "1x5-8" format
            target_reps = int(target_match2.group(2))  # Lower range
            rest = rest[:target_match2.start()] + rest[target_match2.end():]
        elif target_match3:
            # "3x10" format (target, not performance)
            target_reps = int(target_match3.group(2))
            rest = rest[:target_match3.start()] + rest[target_match3.end():]
        
        # Clean up rest - remove exercise name mentions, equipment words
        rest = re.sub(r"\b(bench|bar|nautilus|arsenal|synergy|humansport|hammer|life fitness|fitbit|hoist|dl from floor|stronggg|tough|tufff|yas|push|pushhhh|skipped|fairly easy|lets go|lets do|can go up|shaky|trust the process|cal deficit|cal def|wrist mobility|a bit tired)\b", "", rest, flags=re.IGNORECASE)
        rest = re.sub(r"\b(sled|nautilis|reg bench|inclined?|decline|horizontal|flat)\b", "", rest, flags=re.IGNORECASE)
        
        # Find all remaining numbers
        numbers = []
        for m in re.finditer(r"(\d+(?:\.\d+)?)", rest):
            try:
                val = float(m.group(1))
                numbers.append(val)
            except ValueError:
                pass
        
        if numbers:
            # Check if first number could be weight and rest are reps
            # Pattern: "225 6,5,5" or "50 8,8,7"
            # vs "100, 110" (just weights)
            
            if len(numbers) > 1 and numbers[0] >= 30:
                # Likely "weight reps, reps, reps" format
                weight = numbers[0]
                reps_list = [int(n) for n in numbers[1:] if 1 <= n <= 20]
                if reps_list:
                    for r in reps_list:
                        sets.append((r, weight, note))
                else:
                    # No valid reps, assume target_reps or 8
                    reps = target_reps or 8
                    sets.append((reps, weight, note))
            else:
                # Weight-only format
                reps = target_reps or 8
                for w in numbers:
                    if w >= 10:  # Real weight
                        sets.append((reps, w, note))
    
    if not sets:
        return None, [], raw_name
    
    return exercise_name, sets, raw_name


def parse_workout_block(block):
    """Parse a workout block into structured data."""
    lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
    if not lines:
        return None
    
    workout_date, day_number = parse_date(lines[0])
    if not workout_date:
        return None
    
    date_line = lines[0]
    notes = ""
    if "cal def" in date_line.lower():
        notes = "cal deficit"
    
    exercises = []
    for line in lines[1:]:
        exercise_name, sets, raw_name = parse_exercise_line(line)
        if exercise_name and sets:
            exercises.append({
                "name": exercise_name,
                "sets": [{"reps": r, "weight": w, "note": n} for r, w, n in sets],
                "raw_name": raw_name,
            })
    
    return {
        "date": workout_date.isoformat(),
        "day_number": day_number,
        "notes": notes,
        "exercises": exercises,
    }


def import_workout(conn, workout_data):
    """Import a single workout into the database."""
    program = conn.execute("SELECT id FROM programs ORDER BY id LIMIT 1").fetchone()
    program_id = program["id"] if program else None
    
    existing = conn.execute(
        "SELECT id FROM workouts WHERE date = ? AND day_number = ?",
        (workout_data["date"], workout_data["day_number"]),
    ).fetchone()
    
    if existing:
        print(f"  ⚠ Skipping {workout_data['date']} Day {workout_data['day_number']} — already exists (#{existing['id']})")
        return False
    
    cursor = conn.execute(
        "INSERT INTO workouts (date, notes, program_id, day_number) VALUES (?, ?, ?, ?)",
        (workout_data["date"], workout_data.get("notes", ""), program_id, workout_data["day_number"]),
    )
    workout_id = cursor.lastrowid
    
    total_sets = 0
    for ex in workout_data["exercises"]:
        exercise = conn.execute("SELECT id FROM exercises WHERE name = ?", (ex["name"],)).fetchone()
        if not exercise:
            print(f"  ⚠ Unknown exercise: {ex['name']} (raw: {ex.get('raw_name', '?')}), skipping")
            continue
        
        for i, s in enumerate(ex["sets"], 1):
            conn.execute(
                """INSERT INTO workout_sets
                   (workout_id, exercise_id, set_number, reps, weight, weight_unit, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (workout_id, exercise["id"], i, s["reps"], s["weight"], "lb", s.get("note")),
            )
            total_sets += 1
    
    conn.commit()
    print(f"  ✓ {workout_data['date']} Day {workout_data['day_number']} — {len(workout_data['exercises'])} exercises, {total_sets} sets")
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    
    if not args:
        print("Usage: import_workouts.py <file.txt> [--dry-run]")
        sys.exit(1)
    
    filepath = Path(args[0])
    if not filepath.exists():
        print(f"File not found: {filepath}")
        sys.exit(1)
    
    text = filepath.read_text()
    
    blocks = []
    current_block = []
    for line in text.split("\n"):
        if re.match(r"^\d+/\d+\s+\w+\s+(lower|upper)", line, re.IGNORECASE):
            if current_block:
                blocks.append("\n".join(current_block))
            current_block = [line]
        elif current_block:
            current_block.append(line)
    if current_block:
        blocks.append("\n".join(current_block))
    
    print(f"Found {len(blocks)} workout blocks\n")
    
    if dry_run:
        print("[DRY RUN — no changes made]\n")
    
    conn = get_db()
    imported = 0
    skipped = 0
    
    for block in blocks:
        workout = parse_workout_block(block)
        if not workout:
            print(f"  ⚠ Could not parse block, skipping:")
            print(f"    {block[:80]}...")
            continue
        
        if dry_run:
            print(f"  Would import: {workout['date']} Day {workout['day_number']} — {len(workout['exercises'])} exercises")
            for ex in workout["exercises"]:
                set_str = ", ".join(f"{s['reps']}x{s['weight']}" for s in ex["sets"])
                print(f"    {ex['name']}: {set_str}")
            imported += 1
        else:
            if import_workout(conn, workout):
                imported += 1
            else:
                skipped += 1
    
    conn.close()
    
    action = "would import" if dry_run else "imported"
    print(f"\nDone — {action} {imported} workouts, skipped {skipped}")


if __name__ == "__main__":
    main()
