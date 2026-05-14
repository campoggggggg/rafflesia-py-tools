import re


def score_pump(text: str) -> float:
    score = 0.0
    permanent = "until the end of" not in text

    match = re.search(r"gains? \+(\d+)/\+(\d+)", text)
    if match:
        x, y = int(match.group(1)), int(match.group(2))
        base = (x + y) * (0.6 if permanent else 0.3)
        if re.search(r"all (friendly )?minion", text):
            base *= 2.0
        score += base
    else:
        # +x/+x variabile
        if re.search(r"gains? \+x/\+x", text):
            score += 3.0 if permanent else 1.5
        # +x/+0 o +0/+x variabile (un solo stat)
        elif re.search(r"gains? \+x/\+0|\+0/\+x", text):
            score += 2.0 if permanent else 1.0

    match = re.search(r"gains? -(\d+)/-(\d+)", text)
    if match:
        x, y = int(match.group(1)), int(match.group(2))
        base = (x + y) * (0.6 if permanent else 0.3)
        if re.search(r"all (enemy )?minion", text):
            base *= 2.0
        score += base

    return score
