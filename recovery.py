def calculate_recovery_score(
    sleep_hours: float,
    soreness: int,
    readiness: int,
    recent_training_load: int,
    hrv: float = None,
    resting_hr: float = None
) -> dict:
    """
    Calculate recovery score from 0 to 1.
    
    Inputs:
    - sleep_hours: hours of sleep (0-12)
    - soreness: muscle soreness (1-10, 10 = very sore)
    - readiness: how ready you feel (1-10, 10 = very ready)
    - recent_training_load: total workouts last 3 days (0-10)
    - hrv: heart rate variability (optional)
    - resting_hr: resting heart rate (optional)
    
    Output:
    - score: 0 to 1 (1 = fully recovered)
    - level: excellent / good / moderate / low / very_low
    - reason: human explanation
    - recommendation: push / maintain / deload
    """

    reasons = []
    warnings = []

    # ==================
    # SLEEP SCORE (30% weight)
    # ==================
    if sleep_hours >= 8:
        sleep_score = 1.0
    elif sleep_hours >= 7:
        sleep_score = 0.85
        reasons.append(f"You slept {sleep_hours} hours — slightly under ideal")
    elif sleep_hours >= 6:
        sleep_score = 0.65
        reasons.append(f"You slept {sleep_hours} hours — below recommended")
    elif sleep_hours >= 5:
        sleep_score = 0.4
        reasons.append(f"You slept only {sleep_hours} hours — recovery is compromised")
        warnings.append("low_sleep")
    else:
        sleep_score = 0.2
        reasons.append(f"You slept only {sleep_hours} hours — very poor recovery")
        warnings.append("very_low_sleep")

    # ==================
    # SORENESS SCORE (25% weight)
    # ==================
    soreness_score = max(0, (10 - soreness) / 10)
    if soreness >= 8:
        reasons.append("You reported very high muscle soreness")
        warnings.append("high_soreness")
    elif soreness >= 6:
        reasons.append("You reported moderate to high soreness")
    elif soreness >= 4:
        reasons.append("You reported moderate soreness")

    # ==================
    # READINESS SCORE (25% weight)
    # ==================
    readiness_score = readiness / 10
    if readiness <= 3:
        reasons.append("You reported feeling very fatigued")
        warnings.append("extreme_fatigue")
    elif readiness <= 5:
        reasons.append("You reported low energy today")

    # ==================
    # TRAINING LOAD SCORE (20% weight)
    # ==================
    if recent_training_load >= 8:
        load_score = 0.3
        reasons.append("You have trained heavily in the last 3 days")
        warnings.append("high_load")
    elif recent_training_load >= 5:
        load_score = 0.6
        reasons.append("You have had moderate training load recently")
    elif recent_training_load >= 3:
        load_score = 0.8
    else:
        load_score = 1.0

    # ==================
    # HRV BONUS (optional)
    # ==================
    hrv_adjustment = 0
    if hrv is not None:
        if hrv > 70:
            hrv_adjustment = 0.05
        elif hrv < 40:
            hrv_adjustment = -0.05
            reasons.append("Your HRV is low — nervous system is stressed")

    # ==================
    # RESTING HR BONUS (optional)
    # ==================
    if resting_hr is not None:
        if resting_hr > 80:
            hrv_adjustment -= 0.03
            reasons.append("Your resting heart rate is elevated")

    # ==================
    # FINAL SCORE CALCULATION
    # ==================
    raw_score = (
        sleep_score * 0.30 +
        soreness_score * 0.25 +
        readiness_score * 0.25 +
        load_score * 0.20 +
        hrv_adjustment
    )

    score = round(max(0.0, min(1.0, raw_score)), 2)

    # ==================
    # PAIN/INJURY OVERRIDE
    # ==================
    pain_detected = False
    if soreness >= 9:
        pain_detected = True
        score = min(score, 0.2)
        warnings.append("pain_detected")

    # ==================
    # LEVEL + RECOMMENDATION
    # ==================
    if score >= 0.8:
        level = "excellent"
        recommendation = "push"
    elif score >= 0.65:
        level = "good"
        recommendation = "push"
    elif score >= 0.5:
        level = "moderate"
        recommendation = "maintain"
    elif score >= 0.35:
        level = "low"
        recommendation = "deload"
    else:
        level = "very_low"
        recommendation = "deload"

    # Force deload if pain or extreme fatigue detected
    if pain_detected or "extreme_fatigue" in warnings or "very_low_sleep" in warnings:
        recommendation = "deload"

    # ==================
    # BUILD EXPLANATION
    # ==================
    if not reasons:
        reason_text = "Your recovery metrics all look great today!"
    else:
        reason_text = " ".join(reasons[:2]) + "."

    return {
        "score": score,
        "level": level,
        "recommendation": recommendation,
        "reason": reason_text,
        "warnings": warnings,
        "raw_inputs": {
            "sleep_hours": sleep_hours,
            "soreness": soreness,
            "readiness": readiness,
            "recent_training_load": recent_training_load,
            "hrv": hrv,
            "resting_hr": resting_hr
        },
        "scores_breakdown": {
            "sleep": round(sleep_score, 2),
            "soreness": round(soreness_score, 2),
            "readiness": round(readiness_score, 2),
            "training_load": round(load_score, 2)
        }
    }