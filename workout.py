#!/usr/bin/env python3
"""
Workout Tracker CLI
Usage: python workout.py <command> [args]
"""

import sys
import re
import json
from datetime import datetime, date
from db import get_db, init_db
from seed import seed_exercises, seed_aliases, seed_program


def fmt_weight(w):
    """Format weight: 90.0 -> 90, 90.5 -> 90.5"""
    return int(w) if w == int(w) else w


def resolve_alias(name):
    """Resolve an exercise alias to the exercise name."""
    conn = get_db()
    alias = conn.execute(
        "SELECT e.name FROM exercise_aliases a JOIN exercises e ON a.exercise_id = e.id WHERE a.alias = ?",
        (name.lower().strip(),),
    ).fetchone()
    conn.close()
    if alias:
        return alias["name"]
    # Try exact match on exercise name
    conn = get_db()
    exercise = conn.execute(
        "SELECT name FROM exercises WHERE name LIKE ?",
        (f"%{name}%",),
    ).fetchone()
    conn.close()
    if exercise:
        return exercise["name"]
    return None


def parse_workout_input(text):
    """
    Parse workout input like:
    bench 8x150, 8x135, 8x135
    ohp 10x95, 10x95, 8x95
    upright row 55,55,55,55 nautilus
    Returns list of (exercise_name, [(reps, weight, note), ...])
    """
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    result = []

    for line in lines:
        # Try to match NxW format first: "bench 8x150, 8x135"
        match = re.match(r"^([a-zA-Z\s\-]+?)\s+(\d+x\d+(?:\s*[,\s]\s*\d+x\d+)*)", line)
        if match:
            raw_name = match.group(1).strip()
            sets_str = match.group(2)
            note = line[match.end():].strip().rstrip(",").strip() or None

            exercise_name = resolve_alias(raw_name)
            if not exercise_name:
                continue

            sets = []
            for s in re.findall(r"(\d+)x(\d+(?:\.\d+)?)", sets_str):
                reps, weight = int(s[0]), float(s[1])
                sets.append((reps, weight, note))

            if sets:
                result.append((exercise_name, sets))
            continue

        # Try weight-only format: "upright row 55,55,55,55 nautilus"
        # Extract exercise name (letters/spaces before first number)
        match = re.match(r"^([a-zA-Z\s\-]+?)\s+([\d,\s\.]+)(.*)", line)
        if match:
            raw_name = match.group(1).strip()
            weights_str = match.group(2).strip()
            note = match.group(3).strip().rstrip(",").strip() or None

            exercise_name = resolve_alias(raw_name)
            if not exercise_name:
                continue

            # Parse weights (just numbers separated by commas)
            weights = [w.strip() for w in weights_str.split(",") if w.strip()]
            sets = []
            for w in weights:
                try:
                    weight = float(w)
                    sets.append((8, weight, note))  # Default to 8 reps
                except ValueError:
                    continue

            if sets:
                result.append((exercise_name, sets))

    return result


def cmd_init(args):
    """Initialize database and seed data."""
    init_db()
    seed_exercises()
    seed_aliases()
    seed_program()
    print("✓ Database initialized with exercises, aliases, and program.")


def cmd_lookup(args):
    """Lookup an alias: lookup <alias>"""
    if not args:
        print("Usage: lookup <alias>")
        return
    name = " ".join(args)
    result = resolve_alias(name)
    if result:
        print(f"✓ '{name}' → {result}")
    else:
        print(f"✗ No exercise found for '{name}'")


def cmd_list_exercises(args):
    """List all exercises, optionally filtered by muscle group."""
    conn = get_db()
    if args:
        muscle_group = " ".join(args)
        rows = conn.execute(
            "SELECT id, name, category, muscle_group FROM exercises WHERE muscle_group = ? ORDER BY name",
            (muscle_group,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, name, category, muscle_group FROM exercises ORDER BY muscle_group, name"
        ).fetchall()
    conn.close()

    if not rows:
        print("No exercises found.")
        return

    current_group = None
    for row in rows:
        if row["muscle_group"] != current_group:
            current_group = row["muscle_group"]
            print(f"\n--- {current_group} ---")
        print(f"  [{row['id']}] {row['name']} ({row['category']})")


def cmd_list_programs(args):
    """List all programs."""
    conn = get_db()
    programs = conn.execute("SELECT * FROM programs ORDER BY id").fetchall()
    conn.close()

    if not programs:
        print("No programs found.")
        return

    for p in programs:
        print(f"  [{p['id']}] {p['name']} — {p['days_per_week']} days/week")
        if p["description"]:
            print(f"      {p['description']}")


def cmd_show_program(args):
    """Show full program: show-program <id>"""
    if not args:
        print("Usage: show-program <id>")
        return

    program_id = int(args[0])
    conn = get_db()

    program = conn.execute("SELECT * FROM programs WHERE id = ?", (program_id,)).fetchone()
    if not program:
        print(f"Program #{program_id} not found.")
        return

    print(f"\n{'='*50}")
    print(f"{program['name']}")
    print(f"{program['description']}")
    print(f"{'='*50}")

    days = conn.execute(
        "SELECT * FROM program_days WHERE program_id = ? ORDER BY day_number",
        (program_id,),
    ).fetchall()

    for day in days:
        print(f"\n--- Day {day['day_number']}: {day['day_name']} ---")
        exercises = conn.execute(
            """SELECT e.name, pe.target_sets, pe.target_reps
               FROM program_exercises pe
               JOIN exercises e ON pe.exercise_id = e.id
               WHERE pe.program_day_id = ?
               ORDER BY pe.order_index""",
            (day["id"],),
        ).fetchall()
        for ex in exercises:
            print(f"  {ex['name']} — {ex['target_sets']}x{ex['target_reps']}")

    conn.close()


def cmd_list_days(args):
    """List all days in the current program."""
    conn = get_db()

    program = conn.execute("SELECT * FROM programs ORDER BY id LIMIT 1").fetchone()
    if not program:
        print("No programs found.")
        return

    print(f"\n{program['name']}")
    print(f"{'='*40}")

    days = conn.execute(
        "SELECT * FROM program_days WHERE program_id = ? ORDER BY day_number",
        (program["id"],),
    ).fetchall()

    for day in days:
        exercises = conn.execute(
            "SELECT COUNT(*) as cnt FROM program_exercises WHERE program_day_id = ?",
            (day["id"],),
        ).fetchone()
        print(f"  [{day['day_number']}] {day['day_name']} — {exercises['cnt']} exercises")

    conn.close()


def get_last_workout_for_day(conn, program_id, day_number):
    """Get the last workout for a specific day number, with exercise details."""
    workout = conn.execute(
        """SELECT w.id, w.date
           FROM workouts w
           WHERE w.program_id = ? AND w.day_number = ?
           ORDER BY w.date DESC, w.id DESC LIMIT 1""",
        (program_id, day_number),
    ).fetchone()
    if not workout:
        return None

    sets = conn.execute(
        """SELECT e.name, ws.set_number, ws.reps, ws.weight, ws.weight_unit, ws.notes
           FROM workout_sets ws
           JOIN exercises e ON ws.exercise_id = e.id
           WHERE ws.workout_id = ?
           ORDER BY ws.id""",
        (workout["id"],),
    ).fetchall()

    return {"date": workout["date"], "sets": sets}


def print_last_workout(last):
    """Print last workout summary for reference."""
    print(f"\nLast time ({last['date']}):")
    current_ex = None
    sets_for_ex = []
    for s in last["sets"]:
        if s["name"] != current_ex:
            if current_ex and sets_for_ex:
                print(f"{current_ex} — {'  '.join(sets_for_ex)}")
            current_ex = s["name"]
            sets_for_ex = []
        sets_for_ex.append(f"{s['reps']}x{fmt_weight(s['weight'])}")
    if current_ex and sets_for_ex:
        print(f"{current_ex} — {'  '.join(sets_for_ex)}")


def cmd_start_workout(args):
    """Start a workout for a specific day: start-workout <day_number>"""
    if not args:
        print("Usage: start-workout <day_number>")
        print("Use 'list-days' to see available days.")
        return

    day_number = int(args[0])
    conn = get_db()

    program = conn.execute("SELECT id FROM programs ORDER BY id LIMIT 1").fetchone()
    if not program:
        print("No programs found.")
        return

    day = conn.execute(
        "SELECT * FROM program_days WHERE program_id = ? AND day_number = ?",
        (program["id"], day_number),
    ).fetchone()

    if not day:
        print(f"Day {day_number} not found.")
        return

    print(f"\n{day['day_name']}")
    print(f"{'='*40}")

    last = get_last_workout_for_day(conn, program["id"], day_number)
    if last:
        print_last_workout(last)
    else:
        print("  No history for this day yet.")

    print(f"\nType your sets when ready.")
    conn.close()


def cmd_get_next_workout(args):
    """Get next workout based on last logged workout."""
    conn = get_db()

    # Get the program (assume first program for now)
    program = conn.execute("SELECT id FROM programs ORDER BY id LIMIT 1").fetchone()
    if not program:
        print("No programs found. Create one first.")
        return

    program_id = program["id"]

    # Get last workout for this program
    last_workout = conn.execute(
        "SELECT day_number, date FROM workouts WHERE program_id = ? ORDER BY date DESC, id DESC LIMIT 1",
        (program_id,),
    ).fetchone()

    if last_workout:
        last_day = last_workout["day_number"]
        last_date = last_workout["date"]
        # Next day (cycle through 1-4)
        next_day = (last_day % 4) + 1
        print(f"\nLast workout: Day {last_day} ({last_date})")
    else:
        next_day = 1
        print(f"\nNo previous workouts found.")

    # Get the day info
    day = conn.execute(
        "SELECT * FROM program_days WHERE program_id = ? AND day_number = ?",
        (program_id, next_day),
    ).fetchone()

    if not day:
        print(f"Day {next_day} not found in program.")
        return

    print(f"Next up: {day['day_name']}")
    print(f"{'='*40}")

    last = get_last_workout_for_day(conn, program_id, next_day)
    if last:
        print_last_workout(last)
    else:
        print("  No history for this day yet.")

    print(f"\nType your sets when ready.")
    conn.close()


def cmd_log_workout(args):
    """Log workout from JSON: log-workout <json>"""
    if not args:
        print("Usage: log-workout <json>")
        return

    json_str = " ".join(args)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        return

    conn = get_db()

    # Get program (assume first)
    program = conn.execute("SELECT id FROM programs ORDER BY id LIMIT 1").fetchone()
    program_id = program["id"] if program else None

    # Get day number from JSON or determine next
    day_number = data.get("day_number")
    if not day_number and program_id:
        last_workout = conn.execute(
            "SELECT day_number FROM workouts WHERE program_id = ? ORDER BY date DESC, id DESC LIMIT 1",
            (program_id,),
        ).fetchone()
        if last_workout:
            day_number = (last_workout["day_number"] % 4) + 1
        else:
            day_number = 1

    # Create workout
    notes = data.get("notes", "")
    cursor = conn.execute(
        "INSERT INTO workouts (date, notes, program_id, day_number) VALUES (?, ?, ?, ?)",
        (date.today().isoformat(), notes, program_id, day_number),
    )
    workout_id = cursor.lastrowid

    # Add sets
    for ex in data.get("exercises", []):
        exercise_name = ex.get("name", "")
        exercise = conn.execute(
            "SELECT id FROM exercises WHERE name = ?", (exercise_name,)
        ).fetchone()

        if not exercise:
            print(f"⚠ Unknown exercise: {exercise_name}, skipping...")
            continue

        exercise_id = exercise["id"]

        for i, s in enumerate(ex.get("sets", []), 1):
            conn.execute(
                """INSERT INTO workout_sets
                   (workout_id, exercise_id, set_number, reps, weight, weight_unit, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    workout_id,
                    exercise_id,
                    i,
                    s.get("reps", 0),
                    s.get("weight", 0),
                    s.get("unit", "lb"),
                    s.get("note"),
                ),
            )

    conn.commit()

    # Get day name
    day_name = "Workout"
    if program_id and day_number:
        day = conn.execute(
            "SELECT day_name FROM program_days WHERE program_id = ? AND day_number = ?",
            (program_id, day_number),
        ).fetchone()
        if day:
            day_name = day["day_name"]

    total_sets = sum(len(ex.get("sets", [])) for ex in data.get("exercises", []))
    conn.close()

    print(f"✓ Logged {day_name} — {len(data.get('exercises', []))} exercises, {total_sets} sets")


def cmd_add_set(args):
    """Add a single set: add-set <workout_id> <exercise_alias> <reps> <weight>"""
    if len(args) < 4:
        print("Usage: add-set <workout_id> <exercise_alias> <reps> <weight>")
        return

    workout_id = int(args[0])
    exercise_name = resolve_alias(args[1])
    if not exercise_name:
        print(f"✗ Unknown exercise: {args[1]}")
        return

    reps = int(args[2])
    weight = float(args[3])

    conn = get_db()

    # Get exercise id
    exercise = conn.execute("SELECT id FROM exercises WHERE name = ?", (exercise_name,)).fetchone()
    if not exercise:
        print(f"✗ Exercise not found: {exercise_name}")
        return

    # Get next set number
    last_set = conn.execute(
        "SELECT MAX(set_number) as max_set FROM workout_sets WHERE workout_id = ? AND exercise_id = ?",
        (workout_id, exercise["id"]),
    ).fetchone()
    set_number = (last_set["max_set"] or 0) + 1

    conn.execute(
        """INSERT INTO workout_sets (workout_id, exercise_id, set_number, reps, weight, weight_unit)
           VALUES (?, ?, ?, ?, ?, 'lb')""",
        (workout_id, exercise["id"], set_number, reps, weight),
    )
    conn.commit()
    conn.close()

    print(f"✓ Added: {exercise_name} set {set_number}: {reps}x{weight}lb")


def cmd_history(args):
    """Show workout history: history [limit]"""
    limit = int(args[0]) if args else 10
    conn = get_db()

    workouts = conn.execute(
        """SELECT w.*, pd.day_name
           FROM workouts w
           LEFT JOIN program_days pd ON w.program_id = pd.program_id AND w.day_number = pd.day_number
           ORDER BY w.date DESC, w.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()

    if not workouts:
        print("No workouts found.")
        return

    for w in workouts:
        day_name = w["day_name"] or "Workout"
        print(f"\n{'='*50}")
        print(f"Workout #{w['id']} | {w['date']} | {day_name}")
        if w["notes"]:
            print(f"Notes: {w['notes']}")

        # Get sets grouped by exercise
        sets = conn.execute(
            """SELECT e.name, ws.set_number, ws.reps, ws.weight, ws.weight_unit, ws.notes
               FROM workout_sets ws
               JOIN exercises e ON ws.exercise_id = e.id
               WHERE ws.workout_id = ?
               ORDER BY e.name, ws.set_number""",
            (w["id"],),
        ).fetchall()

        current_exercise = None
        for s in sets:
            if s["name"] != current_exercise:
                current_exercise = s["name"]
                print(f"\n  {current_exercise}:")
            note = f" ({s['notes']})" if s["notes"] else ""
            print(f"    Set {s['set_number']}: {s['reps']}x{fmt_weight(s['weight'])}{s['weight_unit']}{note}")

    conn.close()


def cmd_workout_detail(args):
    """Show detailed workout: workout <id>"""
    if not args:
        print("Usage: workout <id>")
        return

    workout_id = int(args[0])
    conn = get_db()

    workout = conn.execute(
        """SELECT w.*, pd.day_name
           FROM workouts w
           LEFT JOIN program_days pd ON w.program_id = pd.program_id AND w.day_number = pd.day_number
           WHERE w.id = ?""",
        (workout_id,),
    ).fetchone()

    if not workout:
        print(f"Workout #{workout_id} not found.")
        return

    day_name = workout["day_name"] or "Workout"
    print(f"\n{'='*50}")
    print(f"Workout #{workout['id']} | {workout['date']} | {day_name}")
    if workout["notes"]:
        print(f"Notes: {workout['notes']}")
    print(f"{'='*50}")

    # Get sets grouped by exercise
    sets = conn.execute(
        """SELECT e.name, e.muscle_group, ws.set_number, ws.reps, ws.weight, ws.weight_unit, ws.notes
           FROM workout_sets ws
           JOIN exercises e ON ws.exercise_id = e.id
           WHERE ws.workout_id = ?
           ORDER BY e.muscle_group, e.name, ws.set_number""",
        (workout_id,),
    ).fetchall()

    current_group = None
    current_exercise = None
    for s in sets:
        if s["muscle_group"] != current_group:
            current_group = s["muscle_group"]
            print(f"\n{current_group}:")
        if s["name"] != current_exercise:
            current_exercise = s["name"]
            print(f"  {current_exercise}:")
        note = f" ({s['notes']})" if s["notes"] else ""
        print(f"    Set {s['set_number']}: {s['reps']}x{fmt_weight(s['weight'])}{s['weight_unit']}{note}")

    # Summary
    total_sets = len(sets)
    total_volume = sum(s["reps"] * s["weight"] for s in sets)
    print(f"\n{'='*50}")
    print(f"Total sets: {total_sets}")
    print(f"Total volume: {total_volume:,.0f} lb")

    conn.close()


def cmd_progress(args):
    """Show progress for an exercise: progress <exercise_name>"""
    if not args:
        print("Usage: progress <exercise_name>")
        return

    exercise_name = " ".join(args)
    resolved = resolve_alias(exercise_name)
    if not resolved:
        print(f"Exercise '{exercise_name}' not found.")
        return

    conn = get_db()

    exercise = conn.execute(
        "SELECT id FROM exercises WHERE name = ?", (resolved,)
    ).fetchone()

    rows = conn.execute(
        """SELECT w.date, ws.set_number, ws.reps, ws.weight, ws.weight_unit
           FROM workout_sets ws
           JOIN workouts w ON ws.workout_id = w.id
           WHERE ws.exercise_id = ?
           ORDER BY w.date, ws.set_number""",
        (exercise["id"],),
    ).fetchall()

    if not rows:
        print(f"No records found for '{resolved}'.")
        return

    print(f"\nProgress for {resolved}:")
    print(f"{'Date':<12} {'Set':>4} {'Reps':>5} {'Weight':>8}")
    print("-" * 35)
    for row in rows:
        print(f"{row['date']:<12} {row['set_number']:>4} {row['reps']:>5} {fmt_weight(row['weight']):>6}{row['weight_unit']}")

    conn.close()


def cmd_suggest(args):
    """Suggest next weight: suggest <exercise>"""
    if not args:
        print("Usage: suggest <exercise>")
        return

    exercise_name = " ".join(args)
    resolved = resolve_alias(exercise_name)
    if not resolved:
        print(f"Exercise '{exercise_name}' not found.")
        return

    conn = get_db()

    exercise = conn.execute(
        "SELECT id FROM exercises WHERE name = ?", (resolved,)
    ).fetchone()

    # Get last workout's sets for this exercise
    last_sets = conn.execute(
        """SELECT ws.reps, ws.weight, ws.weight_unit
           FROM workout_sets ws
           JOIN workouts w ON ws.workout_id = w.id
           WHERE ws.exercise_id = ?
           ORDER BY w.date DESC, ws.set_number
           LIMIT 10""",
        (exercise["id"],),
    ).fetchall()

    if not last_sets:
        print(f"No records found for '{resolved}'.")
        return

    # Simple suggestion: if you hit 8+ reps, increase weight
    avg_reps = sum(s["reps"] for s in last_sets) / len(last_sets)
    last_weight = last_sets[0]["weight"]
    unit = last_sets[0]["weight_unit"]

    print(f"\nLast session for {resolved}:")
    for s in reversed(last_sets):
        print(f"  {s['reps']}x{s['weight']}{unit}")

    print(f"\nSuggestion:")
    if avg_reps >= 8:
        new_weight = last_weight + 5 if last_weight >= 100 else 2.5
        print(f"  You averaged {avg_reps:.1f} reps — try {new_weight}{unit} next time")
    else:
        print(f"  You averaged {avg_reps:.1f} reps — stick with {last_weight}{unit} and aim for 8+")

    conn.close()


def cmd_delete_workout(args):
    """Delete a workout: delete-workout <id>"""
    if not args:
        print("Usage: delete-workout <id>")
        return

    workout_id = int(args[0])
    conn = get_db()
    conn.execute("DELETE FROM workout_sets WHERE workout_id = ?", (workout_id,))
    conn.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
    conn.commit()
    conn.close()
    print(f"✓ Deleted workout #{workout_id}")


def cmd_stats(args):
    """Show overall statistics."""
    conn = get_db()

    total_workouts = conn.execute("SELECT COUNT(*) as cnt FROM workouts").fetchone()["cnt"]
    total_sets = conn.execute("SELECT COALESCE(SUM(1), 0) as cnt FROM workout_sets").fetchone()["cnt"]
    total_volume = conn.execute(
        "SELECT COALESCE(SUM(reps * weight), 0) as vol FROM workout_sets"
    ).fetchone()["vol"]

    top_exercises = conn.execute(
        """SELECT e.name, COUNT(*) as count
           FROM workout_sets ws
           JOIN exercises e ON ws.exercise_id = e.id
           GROUP BY e.name
           ORDER BY count DESC
           LIMIT 10"""
    ).fetchall()

    conn.close()

    print(f"\n{'='*50}")
    print("WORKOUT STATISTICS")
    print(f"{'='*50}")
    print(f"Total workouts: {total_workouts}")
    print(f"Total sets: {total_sets}")
    print(f"Total volume: {total_volume:,.0f} lb")

    if top_exercises:
        print(f"\nTop exercises:")
        for ex in top_exercises:
            print(f"  {ex['name']}: {ex['count']} times")


def cmd_recent(args):
    """Show last 4 workouts with details."""
    limit = int(args[0]) if args else 4
    conn = get_db()

    workouts = conn.execute(
        """SELECT w.*, pd.day_name
           FROM workouts w
           LEFT JOIN program_days pd ON w.program_id = pd.program_id AND w.day_number = pd.day_number
           ORDER BY w.date DESC, w.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()

    if not workouts:
        print("No workouts found.")
        return

    for w in workouts:
        day_name = w["day_name"] or "Workout"
        print(f"\n{'='*60}")
        print(f"Workout #{w['id']} | {w['date']} | {day_name}")

        # Get exercises with their sets
        exercises = conn.execute(
            """SELECT e.name,
                      GROUP_CONCAT(ws.reps || 'x' || CAST(CAST(ws.weight AS INT) AS TEXT), ', ') as sets,
                      COUNT(*) as set_count,
                      SUM(ws.reps * ws.weight) as volume
               FROM workout_sets ws
               JOIN exercises e ON ws.exercise_id = e.id
               WHERE ws.workout_id = ?
               GROUP BY e.name
               ORDER BY MIN(ws.id)""",
            (w["id"],),
        ).fetchall()

        # Print table
        print(f"\n  {'Exercise':<30} {'Sets':>5} {'Reps':>20}")
        print(f"  {'-'*30} {'-'*5} {'-'*20}")
        for ex in exercises:
            print(f"  {ex['name']:<30} {ex['set_count']:>5} {ex['sets']:>20}")

    conn.close()


COMMANDS = {
    "init": cmd_init,
    "lookup": cmd_lookup,
    "list-exercises": cmd_list_exercises,
    "list-programs": cmd_list_programs,
    "list-days": cmd_list_days,
    "show-program": cmd_show_program,
    "start-workout": cmd_start_workout,
    "get-next-workout": cmd_get_next_workout,
    "log-workout": cmd_log_workout,
    "add-set": cmd_add_set,
    "recent": cmd_recent,
    "history": cmd_history,
    "workout": cmd_workout_detail,
    "progress": cmd_progress,
    "suggest": cmd_suggest,
    "delete-workout": cmd_delete_workout,
    "stats": cmd_stats,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Workout Tracker CLI")
        print("\nCommands:")
        print("  init                - Initialize database")
        print("  lookup <alias>      - Resolve alias to exercise")
        print("  list-exercises      - List all exercises [muscle_group]")
        print("  list-programs       - List all programs")
        print("  list-days           - List all days in current program")
        print("  show-program <id>   - Show program details")
        print("  start-workout <day> - Start workout for specific day")
        print("  get-next-workout    - Get next workout to do")
        print("  log-workout <json>  - Log workout from JSON")
        print("  add-set             - Add single set to workout")
        print("  recent [n]          - Show last n workouts (default 4)")
        print("  history             - Show workout history [limit]")
        print("  workout             - Show workout details")
        print("  progress            - Show exercise progress")
        print("  suggest             - Suggest next weight")
        print("  delete-workout      - Delete a workout")
        print("  stats               - Show statistics")
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]
    COMMANDS[cmd](args)


if __name__ == "__main__":
    main()
