# Workout Tracker Skill

## Overview

This skill manages a local SQLite workout tracker at `~/src/localmuscle/`. It supports logging workouts, tracking progress, and following a training program (Dr. Swole's 4-Day Torso/Limbs).

## Conversation Flow

1. User says `list days` → run `python3 workout.py list-days`
2. User says `start workout N` → run `python3 workout.py start-workout N`
3. User types their sets in natural language
4. User says `save` → parse input, construct JSON, run `python3 workout.py log-workout '<json>'`
5. Confirm what was logged

## Parsing User Input

The user types exercises in this format:

```
<exercise> <sets> <note (optional)>
```

### Format Examples

**NxW format (reps x weight):**
```
bench 8x155, 8x135, 6x155
squat 6x205, 8x155, 8x155 stronggg
```

**Weight-only format (defaults to 8 reps):**
```
upright row 55,55,55,55 nautilus
curl 50,50,50 arsenal
```

**Mixed with targets:**
```
row 3 8-12 8x110, 9x110
leg ext 3x10 100, 110 hoist
```

### Parsing Rules

1. **Exercise name**: Everything before the first number. Use aliases from database.
2. **Sets**: Either `NxW` (reps x weight) or just `W` (weight, default 8 reps)
3. **Note**: Text after the last number on a line (e.g., "nautilus", "tough", "arsenal")
4. **Separator**: Commas or spaces between sets

### Constructing JSON

For each line, build:
```json
{
  "name": "Exercise Name",
  "sets": [
    {"reps": 8, "weight": 155, "note": "optional note"},
    {"reps": 8, "weight": 135}
  ]
}
```

Full log-workout command:
```bash
python3 workout.py log-workout '{"day_number": N, "exercises": [...]}'
```

## Exercise Aliases

The database has 100+ aliases. Common ones:

| Alias | Exercise |
|-------|----------|
| bench, bp | Bench Press |
| db bench | Dumbbell Bench Press |
| ohp | Overhead Press |
| dl | Deadlift |
| rdl | Romanian Deadlift |
| squat, bs | Squat |
| fs | Front Squat |
| row, bbr | Barbell Row |
| yates | Yates Row |
| curl | Bicep Curl |
| pushdown | Tricep Pushdown |
| single leg press, slp | Single Leg Press |
| isp, iso lateral | Iso Lateral Press |
| arsenal tri, arsenal tri machine | Cable Pressdown |

Use `python3 workout.py lookup <alias>` to check if an alias exists.

## Adding New Exercises/Aliases

If user mentions an exercise not in DB:

```python
import sqlite3
conn = sqlite3.connect('workouts.db')

# Add new exercise
conn.execute("INSERT OR IGNORE INTO exercises (name, category, muscle_group) VALUES (?, ?, ?)", (name, category, muscle_group))

# Add alias
exercise = conn.execute("SELECT id FROM exercises WHERE name = ?", (name,)).fetchone()
conn.execute("INSERT OR IGNORE INTO exercise_aliases (exercise_id, alias) VALUES (?, ?)", (exercise['id'], alias))

conn.commit()
conn.close()
```

## Program: Dr. Swole's Torso/Limbs

| Day | Name | Focus |
|-----|------|-------|
| 1 | Upper 1 | Chest, Back, Shoulders, Arms, Calves |
| 2 | Lower 1 | Legs, Back, Chest, Arms |
| 3 | Upper 2 | Chest, Back, Shoulders, Arms, Calves |
| 4 | Lower 2 | Legs, Back, Arms |

## Common Commands

```bash
python3 workout.py list-days              # Show all program days
python3 workout.py start-workout N        # Show exercises for day N
python3 workout.py log-workout '<json>'   # Log workout
python3 workout.py history                # Recent workouts
python3 workout.py workout N              # Show workout details
python3 workout.py progress <exercise>    # Show progression
python3 workout.py suggest <exercise>     # Suggest next weight
python3 workout.py stats                  # Overall statistics
```

## Default Unit

Weights are in **pounds (lb)**. If user mentions kg, convert or set `unit: "kg"` in JSON.
