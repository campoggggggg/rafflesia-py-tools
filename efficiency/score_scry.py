import math
import re


def score_scry(text: str) -> float:
    match = re.search(r"reveal the top (\d+)", text)
    if match:
        x = int(match.group(1))
        return math.log(1 + x) * 0.3
    return 0.0


def score_reveal_then_summon(text: str) -> float:
    if re.search(r"reveal\b.*\bsummon\b", text) and "grave" not in text:
        match = re.search(r"cost of (\d+) or less", text)
        if match:
            cap = int(match.group(1))
            return math.log(1 + cap) * 0.4
        return 0.5
    return 0.0


def score_reveal_then_draw(text: str) -> float:
    if re.search(r"reveal\b.*\b(move|draw)\b.*\btop\b", text):
        return 0.3
    return 0.0
