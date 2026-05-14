import math
import re
from .constants import DRAW_1, MULT_DRAW_DECAY


def score_draw(text: str) -> float:
    # draw X poi topdeck Y
    match = re.search(r"draw (\d+).*move (\d+).*top", text)
    if match:
        x, y = int(match.group(1)), int(match.group(2))
        netto = x - y
        bonus = math.log(1 + y) * (x / (x + y))
        return (DRAW_1 * (1 - MULT_DRAW_DECAY ** netto) / (1 - MULT_DRAW_DECAY)) + bonus

    # draw condizionale
    match = re.search(r"draw (\d+) if condition", text)
    if match:
        x = int(match.group(1))
        return 0.5 * DRAW_1 * (1 - MULT_DRAW_DECAY ** x) / (1 - MULT_DRAW_DECAY)

    # draw X
    match = re.search(r"draw (\d+)", text)
    if match:
        x = int(match.group(1))
        return DRAW_1 * (1 - MULT_DRAW_DECAY ** x) / (1 - MULT_DRAW_DECAY)

    return 0.0
