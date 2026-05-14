def score_disruptive(text: str) -> float:
    score = 0.0

    if "target opponent cannot set cards or play set cards" in text:
        score += 3.0

    return score
