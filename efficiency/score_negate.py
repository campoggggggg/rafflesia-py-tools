import math
import re
from .constants import NEGATE_VALUE


def score_negate(text: str) -> float:
    if "negate target card." not in text:
        return 0.0

    score = NEGATE_VALUE

    match = re.search(r"cost of (\d) or less", text)
    if match:
        x = int(match.group(1))
        score *= (1 - math.exp(-x / 3))

    if "equal to" in text:
        score *= 0.5

    return score
