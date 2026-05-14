import math
import re


def score_gain_life(text: str) -> float:
    match = re.search(r"gain (\d+) life", text)
    if match:
        x = int(match.group(1))
        return math.log(1 + x) * 0.5
    return 0.0
