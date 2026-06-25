from recovery import calculate_recovery_score
from safety import run_safety_filter

WORKOUT_PLANS = {
    "weight_loss": {
        "beginner": {
            "push": [
                {"name": "Jumping Jacks", "sets": 3, "reps": "30", "rest": "30s"},
                {"name": "Bodyweight Squat", "sets": 3, "reps": "15", "rest": "45s"},
                {"name": "Push Up", "sets": 3, "reps": "10", "rest": "45s"},
                {"name": "Mountain Climbers", "sets": 3, "reps": "20", "rest": "30s"},
                {"name": "Walking Lunge", "sets": 3, "reps": "12 each leg", "rest": "45s"},
            ],
            "maintain": [
                {"name": "Brisk Walking", "sets": 1, "reps": "20 minutes", "rest": "none"},
                {"name": "Bodyweight Squat", "sets": 2, "reps": "12", "rest": "60s"},
                {"name": "Modified Push Up", "sets": 2, "reps": "8", "rest": "60s"},
                {"name": "Step Touch", "sets": 2, "reps": "20", "rest": "45s"},
            ],
            "deload": [
                {"name": "Easy Walking", "sets": 1, "reps": "15 minutes", "rest": "none"},
                {"name": "Gentle Stretching", "sets": 1, "reps": "10 minutes", "rest": "none"},
            ]
        },
        "intermediate": {
            "push": [
                {"name": "Burpees", "sets": 4, "reps": "12", "rest": "45s"},
                {"name": "Squat Jump", "sets": 4, "reps": "15", "rest": "45s"},
                {"name": "Push Up", "sets": 4, "reps": "15", "rest": "45s"},
                {"name": "High Knees", "sets": 4, "reps": "30", "rest": "30s"},
                {"name": "Plank", "sets": 3, "reps": "45s", "rest": "30s"},
            ],
            "maintain": [
                {"name": "Jogging", "sets": 1, "reps": "20 minutes", "rest": "none"},
                {"name": "Squat", "sets": 3, "reps": "12", "rest": "60s"},
                {"name": "Push Up", "sets": 3, "reps": "12", "rest": "60s"},
                {"name": "Plank", "sets": 2, "reps": "30s", "rest": "45s"},
            ],
            "deload": [
                {"name": "Light Walking", "sets": 1, "reps": "20 minutes", "rest": "none"},
                {"name": "Yoga Flow", "sets": 1, "reps": "15 minutes", "rest": "none"},
            ]
        },
        "advanced": {
            "push": [
                {"name": "Sprint Intervals", "sets": 8, "reps": "30s sprint 30s rest", "rest": "30s"},
                {"name": "Box Jump", "sets": 5, "reps": "10", "rest": "45s"},
                {"name": "Weighted Squat", "sets": 5, "reps": "15", "rest": "45s"},
                {"name": "Burpees", "sets": 5, "reps": "15", "rest": "30s"},
                {"name": "Battle Ropes", "sets": 4, "reps": "30s", "rest": "30s"},
            ],
            "maintain": [
                {"name": "Moderate Run", "sets": 1, "reps": "25 minutes", "rest": "none"},
                {"name": "Squat", "sets": 3, "reps": "15", "rest": "60s"},
                {"name": "Push Up", "sets": 3, "reps": "15", "rest": "60s"},
            ],
            "deload": [
                {"name": "Easy Cycling", "sets": 1, "reps": "20 minutes", "rest": "none"},
                {"name": "Mobility Work", "sets": 1, "reps": "15 minutes", "rest": "none"},
            ]
        }
    },
    "muscle_gain": {
        "beginner": {
            "push": [
                {"name": "Push Up", "sets": 4, "reps": "10-12", "rest": "60s"},
                {"name": "Bodyweight Squat", "sets": 4, "reps": "15", "rest": "60s"},
                {"name": "Dumbbell Curl", "sets": 3, "reps": "12", "rest": "60s"},
                {"name": "Dumbbell Press", "sets": 3, "reps": "10", "rest": "60s"},
                {"name": "Plank", "sets": 3, "reps": "30s", "rest": "45s"},
            ],
            "maintain": [
                {"name": "Push Up", "sets": 3, "reps": "8-10", "rest": "90s"},
                {"name": "Squat", "sets": 3, "reps": "12", "rest": "90s"},
                {"name": "Dumbbell Curl", "sets": 2, "reps": "10", "rest": "90s"},
            ],
            "deload": [
                {"name": "Light Push Up", "sets": 2, "reps": "8", "rest": "90s"},
                {"name": "Bodyweight Squat", "sets": 2, "reps": "10", "rest": "90s"},
            ]
        },
        "intermediate": {
            "push": [
                {"name": "Bench Press", "sets": 4, "reps": "8-10", "rest": "90s"},
                {"name": "Squat", "sets": 4, "reps": "8-10", "rest": "90s"},
                {"name": "Bent Over Row", "sets": 4, "reps": "10", "rest": "90s"},
                {"name": "Overhead Press", "sets": 3, "reps": "8", "rest": "90s"},
                {"name": "Deadlift", "sets": 3, "reps": "8", "rest": "120s"},
            ],
            "maintain": [
                {"name": "Bench Press", "sets": 3, "reps": "8", "rest": "120s"},
                {"name": "Squat", "sets": 3, "reps": "8", "rest": "120s"},
                {"name": "Row", "sets": 3, "reps": "10", "rest": "90s"},
            ],
            "deload": [
                {"name": "Light Bench Press", "sets": 2, "reps": "8", "rest": "120s"},
                {"name": "Goblet Squat", "sets": 2, "reps": "10", "rest": "120s"},
            ]
        },
        "advanced": {
            "push": [
                {"name": "Heavy Bench Press", "sets": 5, "reps": "5", "rest": "120s"},
                {"name": "Heavy Squat", "sets": 5, "reps": "5", "rest": "120s"},
                {"name": "Weighted Pull Up", "sets": 4, "reps": "6-8", "rest": "120s"},
                {"name": "Overhead Press", "sets": 4, "reps": "6", "rest": "90s"},
                {"name": "Deadlift", "sets": 4, "reps": "5", "rest": "180s"},
            ],
            "maintain": [
                {"name": "Bench Press", "sets": 3, "reps": "6", "rest": "120s"},
                {"name": "Squat", "sets": 3, "reps": "6", "rest": "120s"},
                {"name": "Deadlift", "sets": 2, "reps": "5", "rest": "180s"},
            ],
            "deload": [
                {"name": "Light Bench Press 50% weight", "sets": 2, "reps": "8", "rest": "120s"},
                {"name": "Light Squat 50% weight", "sets": 2, "reps": "8", "rest": "120s"},
            ]
        }
    },
    "endurance": {
        "beginner": {
            "push": [
                {"name": "Brisk Walking", "sets": 1, "reps": "30 minutes", "rest": "none"},
                {"name": "Bodyweight Squat", "sets": 3, "reps": "20", "rest": "30s"},
                {"name": "Step Touch", "sets": 3, "reps": "30", "rest": "30s"},
            ],
            "maintain": [
                {"name": "Walking", "sets": 1, "reps": "20 minutes", "rest": "none"},
                {"name": "Light Cycling", "sets": 1, "reps": "15 minutes", "rest": "none"},
            ],
            "deload": [
                {"name": "Easy Walking", "sets": 1, "reps": "15 minutes", "rest": "none"},
            ]
        },
        "intermediate": {
            "push": [
                {"name": "Running", "sets": 1, "reps": "30 minutes", "rest": "none"},
                {"name": "Cycling", "sets": 1, "reps": "20 minutes", "rest": "none"},
                {"name": "Jump Rope", "sets": 5, "reps": "2 minutes", "rest": "60s"},
            ],
            "maintain": [
                {"name": "Jogging", "sets": 1, "reps": "20 minutes", "rest": "none"},
                {"name": "Cycling", "sets": 1, "reps": "15 minutes", "rest": "none"},
            ],
            "deload": [
                {"name": "Easy Walk", "sets": 1, "reps": "20 minutes", "rest": "none"},
            ]
        },
        "advanced": {
            "push": [
                {"name": "Long Run", "sets": 1, "reps": "45-60 minutes", "rest": "none"},
                {"name": "Interval Training", "sets": 10, "reps": "1 min fast 1 min slow", "rest": "none"},
                {"name": "Swimming", "sets": 1, "reps": "30 minutes", "rest": "none"},
            ],
            "maintain": [
                {"name": "Moderate Run", "sets": 1, "reps": "30 minutes", "rest": "none"},
            ],
            "deload": [
                {"name": "Easy Cycling", "sets": 1, "reps": "20 minutes", "rest": "none"},
            ]
        }
    },
    "general_fitness": {
        "beginner": {
            "push": [
                {"name": "Bodyweight Squat", "sets": 3, "reps": "15", "rest": "60s"},
                {"name": "Push Up", "sets": 3, "reps": "10", "rest": "60s"},
                {"name": "Plank", "sets": 3, "reps": "20s", "rest": "45s"},
                {"name": "Glute Bridge", "sets": 3, "reps": "15", "rest": "45s"},
                {"name": "Walking", "sets": 1, "reps": "20 minutes", "rest": "none"},
            ],
            "maintain": [
                {"name": "Squat", "sets": 2, "reps": "12", "rest": "60s"},
                {"name": "Push Up", "sets": 2, "reps": "8", "rest": "60s"},
                {"name": "Walking", "sets": 1, "reps": "15 minutes", "rest": "none"},
            ],
            "deload": [
                {"name": "Easy Walking", "sets": 1, "reps": "15 minutes", "rest": "none"},
                {"name": "Stretching", "sets": 1, "reps": "10 minutes", "rest": "none"},
            ]
        },
        "intermediate": {
            "push": [
                {"name": "Squat", "sets": 4, "reps": "15", "rest": "60s"},
                {"name": "Push Up", "sets": 4, "reps": "15", "rest": "60s"},
                {"name": "Dumbbell Row", "sets": 3, "reps": "12", "rest": "60s"},
                {"name": "Plank", "sets": 3, "reps": "45s", "rest": "45s"},
                {"name": "Running", "sets": 1, "reps": "20 minutes", "rest": "none"},
            ],
            "maintain": [
                {"name": "Squat", "sets": 3, "reps": "12", "rest": "60s"},
                {"name": "Push Up", "sets": 3, "reps": "12", "rest": "60s"},
                {"name": "Jogging", "sets": 1, "reps": "15 minutes", "rest": "none"},
            ],
            "deload": [
                {"name": "Walking", "sets": 1, "reps": "20 minutes", "rest": "none"},
                {"name": "Yoga", "sets": 1, "reps": "15 minutes", "rest": "none"},
            ]
        },
        "advanced": {
            "push": [
                {"name": "Weighted Squat", "sets": 5, "reps": "12", "rest": "60s"},
                {"name": "Bench Press", "sets": 4, "reps": "10", "rest": "60s"},
                {"name": "Pull Up", "sets": 4, "reps": "10", "rest": "60s"},
                {"name": "Deadlift", "sets": 3, "reps": "8", "rest": "90s"},
                {"name": "Running", "sets": 1, "reps": "25 minutes", "rest": "none"},
            ],
            "maintain": [
                {"name": "Squat", "sets": 3, "reps": "10", "rest": "90s"},
                {"name": "Bench Press", "sets": 3, "reps": "8", "rest": "90s"},
                {"name": "Running", "sets": 1, "reps": "20 minutes", "rest": "none"},
            ],
            "deload": [
                {"name": "Light Cycling", "sets": 1, "reps": "20 minutes", "rest": "none"},
                {"name": "Mobility Work", "sets": 1, "reps": "15 minutes", "rest": "none"},
            ]
        }
    }
}

def generate_explanation(
    action: str,
    recovery_data: dict,
    goal: str,
    level: str
) -> str:
    score = recovery_data["score"]
    reason = recovery_data["reason"]
    sleep = recovery_data["raw_inputs"]["sleep_hours"]
    soreness = recovery_data["raw_inputs"]["soreness"]

    if action == "push":
        return f"Your recovery score is {score} — you are ready to push hard today! {reason} This {goal.replace('_', ' ')} session is calibrated for your {level} level. 💪"
    elif action == "maintain":
        return f"Your recovery score is {score} — keeping today steady. {reason} Maintaining consistent training is just as important as pushing hard. 🎯"
    else:
        return f"Your recovery score is {score} — today is a deload day. {reason} Smart athletes know that rest is where gains are made. 🔄"

def generate_workout(
    goal: str,
    level: str,
    equipment: list,
    injury_flags: list,
    sleep_hours: float,
    soreness: int,
    readiness: int,
    recent_training_load: int,
    hrv: float = None,
    resting_hr: float = None
) -> dict:
    # Normalize inputs
    goal = goal.lower().replace(" ", "_")
    level = level.lower()

    valid_goals = ["weight_loss", "muscle_gain", "endurance", "general_fitness"]
    valid_levels = ["beginner", "intermediate", "advanced"]

    if goal not in valid_goals:
        goal = "general_fitness"
    if level not in valid_levels:
        level = "beginner"

    # Calculate recovery score
    recovery_data = calculate_recovery_score(
        sleep_hours=sleep_hours,
        soreness=soreness,
        readiness=readiness,
        recent_training_load=recent_training_load,
        hrv=hrv,
        resting_hr=resting_hr
    )

    action = recovery_data["recommendation"]

    # Get base workout plan
    base_plan = WORKOUT_PLANS.get(goal, WORKOUT_PLANS["general_fitness"])
    level_plan = base_plan.get(level, base_plan["beginner"])
    workout = level_plan.get(action, level_plan["maintain"])

    # Run safety filter
    safety_result = run_safety_filter(
        workout_plan=workout,
        injury_flags=injury_flags,
        recovery_score=recovery_data["score"],
        sleep_hours=sleep_hours,
        soreness=soreness,
        readiness=readiness
    )

    # Generate explanation
    explanation = generate_explanation(action, recovery_data, goal, level)

    return {
        "action": action,
        "goal": goal,
        "level": level,
        "workout_plan": safety_result["filtered_plan"],
        "explanation": explanation,
        "why_this_workout": f"Why this workout? {explanation}",
        "recovery": {
            "score": recovery_data["score"],
            "level": recovery_data["level"],
            "reason": recovery_data["reason"]
        },
        "safety": {
            "risk_level": safety_result["risk_level"],
            "substitutions": safety_result["substitutions"],
            "notes": safety_result["safety_notes"]
        }
    }