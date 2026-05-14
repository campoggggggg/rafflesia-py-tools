import math
import re


def score_mill(text: str) -> float:
    match = re.search(r"mill (\d+)", text)
    if match:
        x = int(match.group(1))
        if "opponent" in text:
            return math.log(1 + x) * 0.4
        return math.log(1 + x) * 0.1
    return 0.0
