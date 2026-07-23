#!/usr/bin/env python3
"""
Load a training program into the database.
Usage: python3 load_program.py [program.json]

If no JSON file is provided, loads Dr. Swole's Torso/Limbs program.
"""

import sqlite3
import json
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "workouts.db"

TORSO_LIMBS = {
    "name": "Dr. Swole's Torso/Limbs",
    "description": "4-Day Torso-Limbs Program (Moderate Volume)",
    "days_per_week": 4,
    "days": [
        {
            "day_number": 1,
            "day_name": "Upper 1",
            "muscle_groups": ["Chest", "Back", "Shoulders", "Arms", "Legs"],
            "exercises": [
                {"name": "Dumbbell Bench Press", "sets": 3, "reps": "5-10"},
                {"name": "Dumbbell Overhead Press", "sets": 3, "reps": "6-10"},
                {"name": "Weighted Chin-Up", "sets": 4, "reps": "6-10"},
                {"name": "Seal Row", "sets": 3, "reps": "8-12"},
                {"name": "Barbell Upright Row", "sets": 4, "reps": "8-12"},
                {"name": "Machine Lateral Raise", "sets": 3, "reps": "8-12"},
                {"name": "Standing Calf Raise", "sets": 5, "reps": "8-12"},
            ],
        },
        {
            "day_number": 2,
            "day_name": "Lower 1",
            "muscle_groups": ["Legs", "Back", "Chest", "Arms"],
            "exercises": [
                {"name": "Front Squat", "sets": 3, "reps": "5-10"},
                {"name": "Romanian Deadlift", "sets": 3, "reps": "6-10"},
                {"name": "Bulgarian Split Squat", "sets": 3, "reps": "8-12"},
                {"name": "Leg Extension", "sets": 3, "reps": "10-15"},
                {"name": "Close-Grip Bench Press", "sets": 3, "reps": "6-10"},
                {"name": "Lying Bicep Curl", "sets": 4, "reps": "6-10"},
                {"name": "Cable Pressdown", "sets": 3, "reps": "10-15"},
            ],
        },
        {
            "day_number": 3,
            "day_name": "Upper 2",
            "muscle_groups": ["Chest", "Back", "Shoulders", "Arms", "Legs"],
            "exercises": [
                {"name": "Incline Bench Press", "sets": 3, "reps": "6-10"},
                {"name": "Cable Fly", "sets": 3, "reps": "10-15"},
                {"name": "Yates Row", "sets": 4, "reps": "8-12"},
                {"name": "Lat Pulldown", "sets": 3, "reps": "10-15"},
                {"name": "Barbell Upright Row", "sets": 4, "reps": "10-15"},
                {"name": "Cable Lateral Raise", "sets": 3, "reps": "10-15"},
                {"name": "Machine Calf Raise", "sets": 5, "reps": "10-15"},
            ],
        },
        {
            "day_number": 4,
            "day_name": "Lower 2",
            "muscle_groups": ["Legs", "Back", "Arms"],
            "exercises": [
                {"name": "Trap Bar Deadlift", "sets": 3, "reps": "5-8"},
                {"name": "Smith Machine Squat", "sets": 3, "reps": "8-12"},
                {"name": "Leg Press", "sets": 3, "reps": "8-12"},
                {"name": "Leg Curl", "sets": 3, "reps": "10-15"},
                {"name": "EZ Bar Curl", "sets": 3, "reps": "8-12"},
                {"name": "EZ Bar Skullcrushers", "sets": 4, "reps": "8-12"},
                {"name": "Cable Hammer Curl", "sets": 3, "reps": "10-15"},
            ],
        },
    ],
}


def load_program(program_data):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Insert program
    conn.execute(
        "INSERT OR IGNORE INTO programs (name, description, days_per_week) VALUES (?, ?, ?)",
        (program_data["name"], program_data["description"], program_data["days_per_week"]),
    )
    program = conn.execute(
        "SELECT id FROM programs WHERE name = ?", (program_data["name"],)
    ).fetchone()

    if not program:
        print(f"✗ Failed to create program: {program_data['name']}")
        return

    program_id = program["id"]
    print(f"✓ Program: {program_data['name']} (id={program_id})")

    for day in program_data["days"]:
        # Insert day
        conn.execute(
            "INSERT OR IGNORE INTO program_days (program_id, day_number, day_name, muscle_groups) VALUES (?, ?, ?, ?)",
            (program_id, day["day_number"], day["day_name"], json.dumps(day["muscle_groups"])),
        )
        day_row = conn.execute(
            "SELECT id FROM program_days WHERE program_id = ? AND day_number = ?",
            (program_id, day["day_number"]),
        ).fetchone()

        if not day_row:
            print(f"  ✗ Failed to create day: {day['day_name']}")
            continue

        day_id = day_row["id"]

        # Insert exercises
        for i, ex in enumerate(day["exercises"], 1):
            exercise = conn.execute(
                "SELECT id FROM exercises WHERE name = ?", (ex["name"],)
            ).fetchone()

            if not exercise:
                print(f"  ⚠ Unknown exercise: {ex['name']}")
                continue

            conn.execute(
                "INSERT OR IGNORE INTO program_exercises (program_day_id, exercise_id, target_sets, target_reps, order_index) VALUES (?, ?, ?, ?, ?)",
                (day_id, exercise["id"], ex["sets"], ex["reps"], i),
            )

        print(f"  ✓ Day {day['day_number']}: {day['day_name']} ({len(day['exercises'])} exercises)")

    conn.commit()
    conn.close()
    print("\n✓ Done!")


def main():
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        with open(json_file) as f:
            program_data = json.load(f)
    else:
        program_data = TORSO_LIMBS

    load_program(program_data)


if __name__ == "__main__":
    main()
