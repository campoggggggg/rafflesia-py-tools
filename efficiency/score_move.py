import re
from .constants import BOUNCE_ENEMY, BOUNCE_ALLY


def score_move(text: str) -> float:
    score = 0.0

    # grave → hand (proprio), scala se "for each card"
    if re.search(r"move\b.*\bfrom your grave\b.*\bto your hand\b", text):
        if "for each card" in text:
            return 3.0
        return 1.2

    # grave → field set (proprio)
    if re.search(r"move\b.*\bfrom your grave\b.*\bto the field set\b", text):
        m = re.search(r"move up to (\d+)", text)
        n = int(m.group(1)) if m else 1
        return n * 1.2

    # enemy grave → bottom (disturbo graveyard)
    if re.search(r"move\b.*\bfrom their grave\b", text):
        return 0.5

    # bounce avversario
    if "move all target enemy" in text:
        score += BOUNCE_ENEMY * 3.0
    elif "move target enemy" in text:
        score += BOUNCE_ENEMY

    # bounce alleato
    if "move all friendly minion" in text:
        score += BOUNCE_ALLY * 3.0
    elif "move friendly minion" in text:
        score += BOUNCE_ALLY

    if "move this to the field set" in text:
        score += 1.2

    m = re.search(r"move (?:up to )?(\d+) card(?:s)? from the top of your deck to the field set", text)
    if m:
        score += int(m.group(1)) * 1.2

    return score
