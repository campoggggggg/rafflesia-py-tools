def score_change_attack(text: str) -> float:
    if "attack becomes 0." in text:
        return 1.5
    return 0.0
