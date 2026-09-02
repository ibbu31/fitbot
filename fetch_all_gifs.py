"""
Run this ONCE on your local PC (not on Cloud Run) to fetch a real GIF URL for
each of FitBot's 40 exercises. It prints a JavaScript object at the end that
you paste directly into exercises.html — after that, the site never needs to
call RapidAPI again.

Usage:
    python fetch_all_gifs.py
    (it will prompt you to paste your RapidAPI key — input is hidden)
"""

import requests
import time
import getpass
import json

# Your 40 exercise names, in the same id order as EXERCISES in exercises.html
EXERCISE_NAMES = {
    1: "Push Up", 2: "Bench Press", 3: "Overhead Press", 4: "Dumbbell Fly",
    5: "Lateral Raise", 6: "Tricep Dip", 7: "Tricep Pushdown", 8: "Incline Push Up",
    9: "Pull Up", 10: "Bent Over Row", 11: "Bicep Curl", 12: "Hammer Curl",
    13: "Face Pull", 14: "Lat Pulldown", 15: "Cable Row",
    16: "Squat", 17: "Deadlift", 18: "Lunge", 19: "Romanian Deadlift",
    20: "Leg Press", 21: "Calf Raise", 22: "Glute Bridge",
    23: "Arnold Press", 24: "Upright Row", 25: "Chest Dip", 26: "Cable Crossover",
    27: "Hip Thrust", 28: "Step Up", 29: "Sumo Squat", 30: "Good Morning",
    31: "Burpee", 32: "Kettlebell Swing", 33: "Man Maker", 34: "Thruster",
    35: "Plank", 36: "Crunch", 37: "Russian Twist", 38: "Mountain Climber",
    39: "Jumping Jack", 40: "Box Jump",
}

def search_exercise(name, api_key):
    """Search ExerciseDB and return the best-matching gifUrl, or None."""
    try:
        resp = requests.get(
            f"https://exercisedb.p.rapidapi.com/exercises/name/{name.lower()}",
            headers={
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
            },
            params={"limit": 10},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None

        # Prefer an exact name match (case-insensitive)
        for r in results:
            if r.get("name", "").lower() == name.lower():
                return r.get("gifUrl")

        # Otherwise, prefer the shortest name (usually the "plainest" variant)
        best = min(results, key=lambda r: len(r.get("name", "")))
        return best.get("gifUrl")

    except Exception as e:
        print(f"  ERROR searching '{name}': {e}")
        return None


def main():
    api_key = input("Paste your RapidAPI key: ").strip()
    if not api_key:
        print("No key entered — exiting.")
        return

    results = {}
    for ex_id, name in EXERCISE_NAMES.items():
        print(f"[{ex_id}/40] Searching '{name}'...")
        gif_url = search_exercise(name, api_key)
        if gif_url:
            results[ex_id] = gif_url
            print(f"  Found: {gif_url}")
        else:
            print(f"  No match found — will keep SVG fallback for this one")
        time.sleep(1)  # be polite to the API, avoid rate limits

    print("\n" + "=" * 60)
    print(f"Done. Found GIFs for {len(results)}/40 exercises.")
    print("=" * 60)

    # Save raw JSON as backup
    with open("exercise_gifs.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved raw data to exercise_gifs.json (backup)")

    # Print as a JS object ready to paste into exercises.html
    print("\n--- COPY EVERYTHING BELOW THIS LINE ---\n")
    print("const EXERCISE_GIFS = {")
    for ex_id, url in results.items():
        print(f'    {ex_id}: "{url}",')
    print("};")
    print("\n--- COPY EVERYTHING ABOVE THIS LINE ---")


if __name__ == "__main__":
    main()