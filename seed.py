import json
from db import get_db


def seed_exercises():
    exercises = [
        # Existing
        ("Bench Press", "Compound", "Chest"),
        ("Incline Bench Press", "Compound", "Chest"),
        ("Dumbbell Fly", "Isolation", "Chest"),
        ("Cable Crossover", "Isolation", "Chest"),
        ("Squat", "Compound", "Legs"),
        ("Leg Press", "Compound", "Legs"),
        ("Lunge", "Compound", "Legs"),
        ("Leg Curl", "Isolation", "Legs"),
        ("Leg Extension", "Isolation", "Legs"),
        ("Deadlift", "Compound", "Back"),
        ("Barbell Row", "Compound", "Back"),
        ("Pull Up", "Compound", "Back"),
        ("Lat Pulldown", "Compound", "Back"),
        ("Seated Row", "Compound", "Back"),
        ("Overhead Press", "Compound", "Shoulders"),
        ("Lateral Raise", "Isolation", "Shoulders"),
        ("Front Raise", "Isolation", "Shoulders"),
        ("Face Pull", "Isolation", "Shoulders"),
        ("Bicep Curl", "Isolation", "Arms"),
        ("Tricep Pushdown", "Isolation", "Arms"),
        ("Hammer Curl", "Isolation", "Arms"),
        ("Skull Crushers", "Isolation", "Arms"),
        ("Plank", "Isolation", "Core"),
        ("Crunch", "Isolation", "Core"),
        ("Russian Twist", "Isolation", "Core"),
        ("Leg Raise", "Isolation", "Core"),
        # New exercises for Dr. Swole's program
        ("Dumbbell Bench Press", "Compound", "Chest"),
        ("Dumbbell Overhead Press", "Compound", "Shoulders"),
        ("Weighted Chin-Up", "Compound", "Back"),
        ("Seal Row", "Compound", "Back"),
        ("Barbell Upright Row", "Compound", "Shoulders"),
        ("Machine Lateral Raise", "Isolation", "Shoulders"),
        ("Standing Calf Raise", "Isolation", "Legs"),
        ("Front Squat", "Compound", "Legs"),
        ("Romanian Deadlift", "Compound", "Back"),
        ("Bulgarian Split Squat", "Compound", "Legs"),
        ("Close-Grip Bench Press", "Compound", "Chest"),
        ("Lying Bicep Curl", "Isolation", "Arms"),
        ("Cable Pressdown", "Isolation", "Arms"),
        ("Cable Fly", "Isolation", "Chest"),
        ("Yates Row", "Compound", "Back"),
        ("Cable Lateral Raise", "Isolation", "Shoulders"),
        ("Machine Calf Raise", "Isolation", "Legs"),
        ("Trap Bar Deadlift", "Compound", "Back"),
        ("Smith Machine Squat", "Compound", "Legs"),
        ("EZ Bar Curl", "Isolation", "Arms"),
        ("EZ Bar Skullcrushers", "Isolation", "Arms"),
        ("Cable Hammer Curl", "Isolation", "Arms"),
    ]
    conn = get_db()
    for name, category, muscle_group in exercises:
        conn.execute(
            "INSERT OR IGNORE INTO exercises (name, category, muscle_group) VALUES (?, ?, ?)",
            (name, category, muscle_group),
        )
    conn.commit()
    conn.close()


def seed_aliases():
    aliases = [
        # Bench Press
        ("Bench Press", "bench"),
        ("Bench Press", "bp"),
        ("Bench Press", "flat bench"),
        # Dumbbell Bench Press
        ("Dumbbell Bench Press", "db bench"),
        ("Dumbbell Bench Press", "dbp"),
        ("Dumbbell Bench Press", "dumbbell bench"),
        # Incline Bench Press
        ("Incline Bench Press", "incline"),
        ("Incline Bench Press", "ibp"),
        ("Incline Bench Press", "incline bench"),
        # Close-Grip Bench Press
        ("Close-Grip Bench Press", "cg bench"),
        ("Close-Grip Bench Press", "cgbp"),
        ("Close-Grip Bench Press", "close grip"),
        # Overhead Press
        ("Overhead Press", "ohp"),
        ("Overhead Press", "military press"),
        ("Overhead Press", "mp"),
        # Dumbbell Overhead Press
        ("Dumbbell Overhead Press", "db ohp"),
        ("Dumbbell Overhead Press", "db overhead"),
        ("Dumbbell Overhead Press", "dumbbell ohp"),
        # Front Squat
        ("Front Squat", "fs"),
        ("Front Squat", "front squat"),
        # Squat
        ("Squat", "squat"),
        ("Squat", "bs"),
        ("Squat", "back squat"),
        # Smith Machine Squat
        ("Smith Machine Squat", "smith squat"),
        ("Smith Machine Squat", "smiths"),
        # Deadlift
        ("Deadlift", "dl"),
        ("Deadlift", "dead"),
        # Romanian Deadlift
        ("Romanian Deadlift", "rdl"),
        ("Romanian Deadlift", "romanian"),
        # Trap Bar Deadlift
        ("Trap Bar Deadlift", "trap bar"),
        ("Trap Bar Deadlift", "trap dl"),
        ("Trap Bar Deadlift", "tbdl"),
        # Barbell Row
        ("Barbell Row", "bbr"),
        ("Barbell Row", "bb row"),
        ("Barbell Row", "barbell row"),
        # Yates Row
        ("Yates Row", "yates"),
        ("Yates Row", "yates row"),
        # Seal Row
        ("Seal Row", "seal"),
        ("Seal Row", "seal row"),
        # Lat Pulldown
        ("Lat Pulldown", "pulldown"),
        ("Lat Pulldown", "lpd"),
        ("Lat Pulldown", "lat pd"),
        # Weighted Chin-Up
        ("Weighted Chin-Up", "chinup"),
        ("Weighted Chin-Up", "chin-up"),
        ("Weighted Chin-Up", "weighted chin"),
        # Pull Up
        ("Pull Up", "pullup"),
        ("Pull Up", "pull-up"),
        ("Pull Up", "pu"),
        # Leg Press
        ("Leg Press", "lp"),
        ("Leg Press", "leg press"),
        # Bulgarian Split Squat
        ("Bulgarian Split Squat", "bulgarian"),
        ("Bulgarian Split Squat", "bss"),
        ("Bulgarian Split Squat", "split squat"),
        # Lunge
        ("Lunge", "lunge"),
        # Leg Curl
        ("Leg Curl", "leg curl"),
        ("Leg Curl", "hamstring curl"),
        ("Leg Curl", "leg curls"),
        # Leg Extension
        ("Leg Extension", "leg ext"),
        ("Leg Extension", "extensions"),
        # Standing Calf Raise
        ("Standing Calf Raise", "standing calf"),
        ("Standing Calf Raise", "calf raise"),
        ("Standing Calf Raise", "calves"),
        # Machine Calf Raise
        ("Machine Calf Raise", "machine calf"),
        ("Machine Calf Raise", "machine calves"),
        # Bicep Curl
        ("Bicep Curl", "curl"),
        ("Bicep Curl", "bc"),
        ("Bicep Curl", "bicep curls"),
        # Lying Bicep Curl
        ("Lying Bicep Curl", "lying curl"),
        ("Lying Bicep Curl", "lying bicep"),
        ("Lying Bicep Curl", "prone curl"),
        # EZ Bar Curl
        ("EZ Bar Curl", "ez curl"),
        ("EZ Bar Curl", "ez bar curl"),
        ("EZ Bar Curl", "ez bicep"),
        # Cable Hammer Curl
        ("Cable Hammer Curl", "cable hammer"),
        ("Cable Hammer Curl", "hammer curl cable"),
        # Hammer Curl
        ("Hammer Curl", "hammer"),
        ("Hammer Curl", "hammer curl"),
        # Tricep Pushdown
        ("Tricep Pushdown", "pushdown"),
        ("Tricep Pushdown", "tri push"),
        ("Tricep Pushdown", "tricep push"),
        # Cable Pressdown
        ("Cable Pressdown", "pressdown"),
        ("Cable Pressdown", "cable push"),
        ("Cable Pressdown", "cable press"),
        # Skull Crushers
        ("Skull Crushers", "skull crushers"),
        ("Skull Crushers", "skulls"),
        # EZ Bar Skullcrushers
        ("EZ Bar Skullcrushers", "ez skulls"),
        ("EZ Bar Skullcrushers", "ez skull crushers"),
        # Lateral Raise
        ("Lateral Raise", "lateral"),
        ("Lateral Raise", "side raise"),
        # Cable Lateral Raise
        ("Cable Lateral Raise", "cable lateral"),
        ("Cable Lateral Raise", "cable side"),
        # Machine Lateral Raise
        ("Machine Lateral Raise", "machine lateral"),
        ("Machine Lateral Raise", "machine side"),
        # Face Pull
        ("Face Pull", "face pull"),
        ("Face Pull", "fp"),
        # Front Raise
        ("Front Raise", "front raise"),
        ("Front Raise", "fr"),
        # Cable Fly
        ("Cable Fly", "cable fly"),
        ("Cable Fly", "cable flies"),
        # Dumbbell Fly
        ("Dumbbell Fly", "db fly"),
        ("Dumbbell Fly", "fly"),
        # Cable Crossover
        ("Cable Crossover", "crossover"),
        ("Cable Crossover", "cables"),
        # Plank
        ("Plank", "plank"),
        # Leg Raise
        ("Leg Raise", "leg raise"),
        ("Leg Raise", "lr"),
        # Crunch
        ("Crunch", "crunch"),
        # Russian Twist
        ("Russian Twist", "russian twist"),
        ("Russian Twist", "rt"),
    ]
    conn = get_db()
    for exercise_name, alias in aliases:
        exercise = conn.execute(
            "SELECT id FROM exercises WHERE name = ?", (exercise_name,)
        ).fetchone()
        if exercise:
            conn.execute(
                "INSERT OR IGNORE INTO exercise_aliases (exercise_id, alias) VALUES (?, ?)",
                (exercise["id"], alias),
            )
    conn.commit()
    conn.close()


def seed_program():
    conn = get_db()

    # Create program
    conn.execute(
        "INSERT OR IGNORE INTO programs (name, description, days_per_week) VALUES (?, ?, ?)",
        ("Dr. Swole's Torso/Limbs", "4-Day Torso-Limbs Program (Moderate Volume)", 4),
    )
    program = conn.execute("SELECT id FROM programs WHERE name = ?", ("Dr. Swole's Torso/Limbs",)).fetchone()
    program_id = program["id"]

    # Day 1 - Upper 1
    conn.execute(
        "INSERT OR IGNORE INTO program_days (program_id, day_number, day_name, muscle_groups) VALUES (?, ?, ?, ?)",
        (program_id, 1, "Upper 1", json.dumps(["Chest", "Back", "Shoulders", "Arms", "Legs"])),
    )
    day1 = conn.execute("SELECT id FROM program_days WHERE program_id = ? AND day_number = ?", (program_id, 1)).fetchone()
    day1_id = day1["id"]

    upper1_exercises = [
        ("Dumbbell Bench Press", 3, "5-10", 1),
        ("Dumbbell Overhead Press", 3, "6-10", 2),
        ("Weighted Chin-Up", 4, "6-10", 3),
        ("Seal Row", 3, "8-12", 4),
        ("Barbell Upright Row", 4, "8-12", 5),
        ("Machine Lateral Raise", 3, "8-12", 6),
        ("Standing Calf Raise", 5, "8-12", 7),
    ]
    for ex_name, sets, reps, order in upper1_exercises:
        ex = conn.execute("SELECT id FROM exercises WHERE name = ?", (ex_name,)).fetchone()
        if ex:
            conn.execute(
                "INSERT OR IGNORE INTO program_exercises (program_day_id, exercise_id, target_sets, target_reps, order_index) VALUES (?, ?, ?, ?, ?)",
                (day1_id, ex["id"], sets, reps, order),
            )

    # Day 2 - Lower 1
    conn.execute(
        "INSERT OR IGNORE INTO program_days (program_id, day_number, day_name, muscle_groups) VALUES (?, ?, ?, ?)",
        (program_id, 2, "Lower 1", json.dumps(["Legs", "Back", "Chest", "Arms"])),
    )
    day2 = conn.execute("SELECT id FROM program_days WHERE program_id = ? AND day_number = ?", (program_id, 2)).fetchone()
    day2_id = day2["id"]

    lower1_exercises = [
        ("Front Squat", 3, "5-10", 1),
        ("Romanian Deadlift", 3, "6-10", 2),
        ("Bulgarian Split Squat", 3, "8-12", 3),
        ("Leg Extension", 3, "10-15", 4),
        ("Close-Grip Bench Press", 3, "6-10", 5),
        ("Lying Bicep Curl", 4, "6-10", 6),
        ("Cable Pressdown", 3, "10-15", 7),
    ]
    for ex_name, sets, reps, order in lower1_exercises:
        ex = conn.execute("SELECT id FROM exercises WHERE name = ?", (ex_name,)).fetchone()
        if ex:
            conn.execute(
                "INSERT OR IGNORE INTO program_exercises (program_day_id, exercise_id, target_sets, target_reps, order_index) VALUES (?, ?, ?, ?, ?)",
                (day2_id, ex["id"], sets, reps, order),
            )

    # Day 3 - Upper 2
    conn.execute(
        "INSERT OR IGNORE INTO program_days (program_id, day_number, day_name, muscle_groups) VALUES (?, ?, ?, ?)",
        (program_id, 3, "Upper 2", json.dumps(["Chest", "Back", "Shoulders", "Arms", "Legs"])),
    )
    day3 = conn.execute("SELECT id FROM program_days WHERE program_id = ? AND day_number = ?", (program_id, 3)).fetchone()
    day3_id = day3["id"]

    upper2_exercises = [
        ("Incline Bench Press", 3, "6-10", 1),
        ("Cable Fly", 3, "10-15", 2),
        ("Yates Row", 4, "8-12", 3),
        ("Lat Pulldown", 3, "10-15", 4),
        ("Barbell Upright Row", 4, "10-15", 5),
        ("Cable Lateral Raise", 3, "10-15", 6),
        ("Machine Calf Raise", 5, "10-15", 7),
    ]
    for ex_name, sets, reps, order in upper2_exercises:
        ex = conn.execute("SELECT id FROM exercises WHERE name = ?", (ex_name,)).fetchone()
        if ex:
            conn.execute(
                "INSERT OR IGNORE INTO program_exercises (program_day_id, exercise_id, target_sets, target_reps, order_index) VALUES (?, ?, ?, ?, ?)",
                (day3_id, ex["id"], sets, reps, order),
            )

    # Day 4 - Lower 2
    conn.execute(
        "INSERT OR IGNORE INTO program_days (program_id, day_number, day_name, muscle_groups) VALUES (?, ?, ?, ?)",
        (program_id, 4, "Lower 2", json.dumps(["Legs", "Back", "Arms"])),
    )
    day4 = conn.execute("SELECT id FROM program_days WHERE program_id = ? AND day_number = ?", (program_id, 4)).fetchone()
    day4_id = day4["id"]

    lower2_exercises = [
        ("Trap Bar Deadlift", 3, "5-8", 1),
        ("Smith Machine Squat", 3, "8-12", 2),
        ("Leg Press", 3, "8-12", 3),
        ("Leg Curl", 3, "10-15", 4),
        ("EZ Bar Curl", 3, "8-12", 5),
        ("EZ Bar Skullcrushers", 4, "8-12", 6),
        ("Cable Hammer Curl", 3, "10-15", 7),
    ]
    for ex_name, sets, reps, order in lower2_exercises:
        ex = conn.execute("SELECT id FROM exercises WHERE name = ?", (ex_name,)).fetchone()
        if ex:
            conn.execute(
                "INSERT OR IGNORE INTO program_exercises (program_day_id, exercise_id, target_sets, target_reps, order_index) VALUES (?, ?, ?, ?, ?)",
                (day4_id, ex["id"], sets, reps, order),
            )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    seed_exercises()
    seed_aliases()
    seed_program()
    print("✓ Seeded exercises, aliases, and program.")
