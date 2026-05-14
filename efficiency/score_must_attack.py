def score_must_attack(text: str) -> float:
    if "must attack if able" in text:
        return -0.3
    return 0.0
