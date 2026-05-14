import math
import re


def score_recycle(text: str) -> float:
    match = re.search(r"recycle (\d+)", text)
    if match:
        x = int(match.group(1))
        return math.log(1 + x) * 0.2
    if "recycle" in text:
        return 0.2
    return 0.0
