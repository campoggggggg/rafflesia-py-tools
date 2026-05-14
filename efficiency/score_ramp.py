import re


def score_ramp(text: str) -> float:
    score = 0.0
    match = re.search(r"gain (\(M\))+", text)
    if match:
        n = len(re.findall(r"\(M\)", match.group(0)))
        score += n * 1.0
    match = re.search(r"gain (\d+) mana", text)
    if match:
        score += int(match.group(1)) * 1.0
    return score
