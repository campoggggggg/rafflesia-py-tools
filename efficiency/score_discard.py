import re
from .constants import DISCARD_ALL, DISCARD_1, MULT_DISCARD_BONUS


def score_discard(text: str) -> float:
    score = 0.0

    if "banish up to 1 card each from your opponent's hand, field, and grave" in text:
        return 4.0

    if "banish up to 1 card among those revealed" in text:
        return 3.5

    if "reveals their hand, choose and attach 1 card among those revealed" in text:
        score += 1.0

    if "discard your hand" in text:
        if "draw x" in text:
            return 0.0
        return DISCARD_ALL

    match = re.search(r"discard (\d+)", text)
    if match:
        x = int(match.group(1))
        score += DISCARD_1 * (MULT_DISCARD_BONUS ** x - 1) / (MULT_DISCARD_BONUS - 1)
        return score

    return score
