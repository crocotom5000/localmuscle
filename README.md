# Local Muscle — Workout Chat Bot

A chat-based workout tracker that logs your sessions to a local SQLite database.

## What You Need

- Python 3.10+
- This repo cloned to `~/src/localmuscle`

## How It Works

Talk to the bot in natural language. It parses your input and logs workouts to the database.

## Quick Start

```
You:    list days
Me:     [shows program days]

You:    start workout 1
Me:     [shows exercises for Upper 1]

You:    bench 8x155, 8x135, 6x155
        ohp 10x65, 9x65, 9x65
        ...

You:    save
Me:     ✓ Logged Upper 1 — 7 exercises, 22 sets
```

## Commands

| Say This | What It Does |
|----------|--------------|
| `list days` | Show all program days |
| `start workout N` | Show exercises for day N |
| `save` | Log the workout you just typed |
| `recent` | Show last 4 workouts with details |
| `history` | Show recent workouts (compact) |
| `workout N` | Show details for workout #N |
| `progress <exercise>` | Show progression over time |
| `suggest <exercise>` | Get next weight suggestion |
| `stats` | Show overall statistics |
| `lookup <alias>` | Check if an alias exists |

## Input Format

Type exercises one per line:

```
bench 8x155, 8x135, 6x155
upright row 55,55,55,55 nautilus
curl 50,50,50 arsenal
```

**Format:** `<exercise> <sets> <note (optional)>`

- **NxW** = reps x weight (e.g., `8x155`)
- **W only** = weight, defaults to 8 reps (e.g., `55` = 8x55)
- **Note** = text after the last number (e.g., `nautilus`, `tough`)

## Exercise Aliases

Use shorthand — the bot knows 100+ aliases:

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
| curl | Bicep Curl |
| pushdown | Tricep Pushdown |
| single leg press, slp | Single Leg Press |
| isp, iso lateral | Iso Lateral Press |
| arsenal tri | Cable Pressdown |

Run `lookup <alias>` to check if an alias exists.

## Adding Exercises

If you use an exercise not in the database, just tell the bot:

> "add single leg press as an alias for bulgarian split squat"
> "add iso lateral press as a new chest exercise"

## Program: Dr. Swole's Torso/Limbs

| Day | Name | Focus |
|-----|------|-------|
| 1 | Upper 1 | Chest, Back, Shoulders, Arms, Calves |
| 2 | Lower 1 | Legs, Back, Chest, Arms |
| 3 | Upper 2 | Chest, Back, Shoulders, Arms, Calves |
| 4 | Lower 2 | Legs, Back, Arms |

## Data Storage

All data lives in `workouts.db` (SQLite). Backup this file to keep your history.

```
exercises          - Exercise catalog
exercise_aliases   - Shorthand names
programs           - Training programs
program_days       - Days within a program
program_exercises  - Prescribed exercises per day
workouts           - Logged workout sessions
workout_sets       - Individual sets (one row per set)
```
