# Local Muscle — Workout Chat Bot

A chat-based workout tracker that logs your sessions to a local SQLite database.

## What You Need

- Python 3.10+
- This repo cloned to `~/src/localmuscle`

## Setup

```bash
# Initialize database with exercises and aliases
python3 workout.py init

# Load the training program
python3 load_program.py
```

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

## Data Model

```mermaid
erDiagram
    exercises ||--o{ exercise_aliases : "has"
    exercises ||--o{ program_exercises : "prescribed in"
    exercises ||--o{ workout_sets : "logged in"

    programs ||--o{ program_days : "has"
    programs ||--o{ workouts : "tracked in"

    program_days ||--o{ program_exercises : "has"

    workouts ||--o{ workout_sets : "has"

    exercises {
        int id PK
        text name UK
        text category
        text muscle_group
    }

    exercise_aliases {
        int id PK
        int exercise_id FK
        text alias UK
    }

    programs {
        int id PK
        text name UK
        text description
        int days_per_week
    }

    program_days {
        int id PK
        int program_id FK
        int day_number
        text day_name
        text muscle_groups
    }

    program_exercises {
        int id PK
        int program_day_id FK
        int exercise_id FK
        int target_sets
        text target_reps
        int order_index
    }

    workouts {
        int id PK
        text date
        text notes
        int program_id FK
        int day_number
        text created_at
    }

    workout_sets {
        int id PK
        int workout_id FK
        int exercise_id FK
        int set_number
        int reps
        real weight
        text weight_unit
        text notes
    }
    ```

## Backups

The database is backed up daily to Google Cloud Storage at 2:00 AM. Backups are retained for 30 days.

### Manual Backup

```bash
python3 backup.py              # Run backup
python3 backup.py --dry-run    # Preview without uploading
```

### Setup (one-time)

1. Install dependencies:

```bash
pip install --break-system-packages -r requirements.txt
```

2. Create `.env` from the example:

```bash
cp .env.example .env
# Edit .env with your values
```

3. Verify the cron job is installed:

```bash
crontab -l | grep localmuscle
```

### GCS Setup

If you need to set up GCS access from scratch:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project (or use existing)
3. Enable the **Cloud Storage API**
4. Create a bucket (e.g., `localmuscle-backups`)
5. Create a **Service Account** (IAM → Service Accounts)
6. Grant it the **Storage Object Admin** role
7. Download the JSON key to `~/localmuscle-*.json`
8. Update `GOOGLE_APPLICATION_CREDENTIALS` in `.env`

### Cron Job

The backup runs daily via cron:

```
0 2 * * * cd /home/exedev/localmuscle && /usr/bin/python3 backup.py >> /home/exedev/localmuscle/logs/backup.log 2>&1
```

Logs are written to `logs/backup.log`.
