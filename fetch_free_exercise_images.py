"""
Improved version — uses looser fuzzy matching (word-overlap scoring instead of
requiring every word to match) to find images for the exercises that failed
last time. Safe to run again for ALL 40 — it will simply find better/same
matches for the ones that already worked, and hopefully catch more this time.
"""

import requests
import json

FREE_DB_JSON_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
IMAGE_BASE_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"

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

# Manual fallback keywords for the trickiest ones — dataset naming often
# differs a lot from common gym-speak names
FALLBACK_SEARCH_TERMS = {
    4: ["dumbbell flyes", "chest fly", "flye"],
    6: ["dip", "bench dip", "tricep"],
    7: ["pushdown", "triceps pushdown", "cable pushdown"],
    25: ["dip", "chest dip"],
    29: ["plie squat", "sumo", "wide stance squat"],
    31: ["burpee", "squat thrust", "burpees"],
    32: ["kettlebell swing", "russian kettlebell swing", "two arm kettlebell swing"],
    33: ["man maker", "renegade row"],
    38: ["mountain climber", "climber"],
    39: ["jumping jack", "jack"],
}


def normalize(s):
    return s.lower().replace("-", " ").replace("_", " ").strip()


def word_overlap_score(a_words, b_words):
    if not a_words or not b_words:
        return 0
    overlap = len(a_words & b_words)
    return overlap / max(len(a_words), 1)


def find_best_match(target_name, all_exercises, extra_terms=None):
    target_norm = normalize(target_name)
    target_words = set(target_norm.split())

    exact = [e for e in all_exercises if normalize(e.get("name", "")) == target_norm]
    if exact:
        return exact[0]

    candidates = []
    search_terms = [target_norm] + (extra_terms or [])

    for term in search_terms:
        term_words = set(term.split())
        for e in all_exercises:
            e_norm = normalize(e.get("name", ""))
            e_words = set(e_norm.split())
            score = word_overlap_score(term_words, e_words)
            if score >= 0.5:  # at least half the words overlap — looser than before
                candidates.append((score, len(e_norm), e))

    if candidates:
        # Highest overlap score first, then shortest/plainest name as tiebreaker
        candidates.sort(key=lambda x: (-x[0], x[1]))
        return candidates[0][2]

    return None


def main():
    print("Downloading free-exercise-db dataset...")
    resp = requests.get(FREE_DB_JSON_URL, timeout=20)
    resp.raise_for_status()
    all_exercises = resp.json()
    print(f"Loaded {len(all_exercises)} exercises from the dataset.\n")

    results = {}
    for ex_id, name in EXERCISE_NAMES.items():
        extra_terms = FALLBACK_SEARCH_TERMS.get(ex_id)
        match = find_best_match(name, all_exercises, extra_terms)
        if match and match.get("images"):
            image_urls = [IMAGE_BASE_URL + img for img in match["images"][:2]]
            results[ex_id] = image_urls
            print(f"[{ex_id}/40] '{name}' -> matched '{match['name']}' ({len(image_urls)} images)")
        else:
            print(f"[{ex_id}/40] '{name}' -> still NO MATCH, keeping SVG fallback")

    print("\n" + "=" * 60)
    print(f"Done. Matched {len(results)}/40 exercises.")
    print("=" * 60)

    with open("exercise_images_v2.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved backup to exercise_images_v2.json")

    print("\n--- COPY EVERYTHING BELOW THIS LINE ---\n")
    print("const EXERCISE_IMAGES = {")
    for ex_id, urls in results.items():
        urls_str = ", ".join(f'"{u}"' for u in urls)
        print(f"    {ex_id}: [{urls_str}],")
    print("};")
    print("\n--- COPY EVERYTHING ABOVE THIS LINE ---")


if __name__ == "__main__":
    main()