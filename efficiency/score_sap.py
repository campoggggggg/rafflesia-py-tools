def score_sap(text: str) -> float:
    score = 0.0

    if "sap all enemy" in text:
        score += 1.5

    if "sap target enemy" in text or "sap target minion" in text:
        score += 0.5

    if "sap this" in text:
        score += -0.5

    if "sap target ready friendly" in text:
        score += -0.5

    if "sap any number of ready friendly" in text:
        score += -1.0

    return score
