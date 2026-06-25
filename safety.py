UNSAFE_EXERCISES = {
    "lower_back": ["deadlift", "squat", "good morning", "bent over row"],
    "knee": ["squat", "lunge", "leg press", "jumping", "running"],
    "shoulder": ["overhead press", "bench press", "pull up", "dip"],
    "wrist": ["push up", "plank", "bench press", "curl"],
    "ankle": ["running", "jumping", "calf raise", "squat"],
}

SAFE_SUBSTITUTES = {
    "deadlift": "Romanian deadlift with light weight",
    "squat": "Leg press or wall sit",
    "good morning": "Cat-cow stretch",
    "bent over row": "Seated cable row",
    "lunge": "Step up on low box",
    "leg press": "Seated leg extension",
    "jumping": "Walking",
    "running": "Stationary bike",
    "overhead press": "Lateral raises with light weight",
    "bench press": "Cable chest fly",
    "pull up": "Lat pulldown with light weight",
    "dip": "Tricep pushdown",
    "push up": "Wall push up",
    "plank": "Dead bug exercise",
    "curl": "Hammer curl with light weight",
    "calf raise": "Seated calf raise",
}

def run_safety_filter(
    workout_plan: list,
    injury_flags: list,
    recovery_score: float,
    sleep_hours: float,
    soreness: int,
    readiness: int
) -> dict:
    """
    Safety filter that checks injury flags and recovery data.
    Returns safe workout plan with substitutions and notes.
    """
    safety_notes = []
    substitutions = []
    risk_level = "low"
    filtered_plan = []

    # Check overall risk level
    if soreness >= 9 or readiness <= 2:
        risk_level = "high"
        safety_notes.append("High pain or extreme fatigue detected — switching to mobility work only")
    elif recovery_score < 0.35 or sleep_hours < 5:
        risk_level = "high"
        safety_notes.append("Very low recovery — reducing intensity significantly")
    elif recovery_score < 0.5 or soreness >= 7:
        risk_level = "medium"
        safety_notes.append("Moderate recovery concerns — keeping volume conservative")

    # If high risk return mobility only plan
    if risk_level == "high":
        return {
            "risk_level": risk_level,
            "filtered_plan": get_mobility_plan(),
            "substitutions": [],
            "safety_notes": safety_notes,
            "intensity_adjustment": "reduced_to_mobility"
        }

    # Check each exercise against injury flags
    for exercise in workout_plan:
        exercise_name = exercise.get("name", "").lower()
        is_unsafe = False

        for injury in injury_flags:
            injury_lower = injury.lower()
            if injury_lower in UNSAFE_EXERCISES:
                unsafe_list = UNSAFE_EXERCISES[injury_lower]
                for unsafe in unsafe_list:
                    if unsafe in exercise_name:
                        substitute = SAFE_SUBSTITUTES.get(unsafe, f"Light {unsafe} alternative")
                        substitutions.append({
                            "original": exercise["name"],
                            "substitute": substitute,
                            "reason": f"Avoiding {injury} aggravation"
                        })
                        exercise = {**exercise, "name": substitute}
                        safety_notes.append(f"Substituted {exercise_name} due to {injury} concern")
                        is_unsafe = True
                        break

        # Reduce volume if medium risk
        if risk_level == "medium":
            if "sets" in exercise:
                exercise = {**exercise, "sets": max(1, exercise["sets"] - 1)}
            if "reps" in exercise:
                original_reps = exercise["reps"]
                if isinstance(original_reps, str) and "-" in original_reps:
                    low, high = original_reps.split("-")
                    exercise = {**exercise, "reps": f"{int(low)-2}-{int(high)-2}"}

        filtered_plan.append(exercise)

    return {
        "risk_level": risk_level,
        "filtered_plan": filtered_plan,
        "substitutions": substitutions,
        "safety_notes": safety_notes,
        "intensity_adjustment": "normal" if risk_level == "low" else "reduced"
    }

def get_mobility_plan():
    return [
        {"name": "Cat-Cow Stretch", "sets": 3, "reps": "10", "rest": "30s"},
        {"name": "Hip Flexor Stretch", "sets": 2, "reps": "30s each side", "rest": "30s"},
        {"name": "Child's Pose", "sets": 3, "reps": "30s", "rest": "30s"},
        {"name": "Shoulder Circles", "sets": 2, "reps": "10 each direction", "rest": "30s"},
        {"name": "Thoracic Rotation", "sets": 2, "reps": "10 each side", "rest": "30s"},
        {"name": "Ankle Circles", "sets": 2, "reps": "10 each direction", "rest": "30s"},
        {"name": "Deep Breathing", "sets": 1, "reps": "5 minutes", "rest": "none"},
    ]