"""Evidence Trust Ladder scoring rubric for project experimentation.

IMPORTANT: This is a transparent project rubric, not a validated probability
that an image is genuine. Replace/validate weights with the project team.
"""
WEIGHTS = {
    "forensic_agreement": 0.35,
    "image_integrity": 0.20,
    "robustness": 0.30,
    "corroboration": 0.15,
}

LEVELS = [
    (85, "Level 5 - Strong supporting evidence"),
    (70, "Level 4 - High confidence"),
    (50, "Level 3 - Moderate confidence"),
    (30, "Level 2 - Limited confidence"),
    (0, "Level 1 - Insufficient evidence"),
]

def calculate_trust_ladder(signals):
    """signals: optional 0-100 values keyed by WEIGHTS names.

    Missing signals are excluded and remaining weights are re-normalized.
    """
    available = {
        key: float(value) for key, value in signals.items()
        if key in WEIGHTS and value is not None
    }
    if not available:
        return {"score": None, "level": "Not enough data", "used_signals": []}

    if any(value < 0 or value > 100 for value in available.values()):
        raise ValueError("Every trust signal must be between 0 and 100.")

    weight_total = sum(WEIGHTS[key] for key in available)
    score = sum(available[key] * WEIGHTS[key] for key in available) / weight_total
    level = next(label for minimum, label in LEVELS if score >= minimum)
    return {
        "score": round(score, 2),
        "level": level,
        "used_signals": list(available.keys()),
        "note": "Experimental project rubric; not a probability or proof of authenticity."
    }
