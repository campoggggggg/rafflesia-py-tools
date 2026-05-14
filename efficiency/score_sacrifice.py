import re
from .constants import SACRIFICE_TERRITORY, SAC_TER_BONUS


def score_sacrifice(text: str, stats_score: float) -> float:
    if "sacrifice this" in text:
        return -abs(stats_score)

    score = 0.0
    match = re.search(r"sacrifice (\d+) territory card", text)
    if match:
        x = int(match.group(1))
        score += SACRIFICE_TERRITORY * (SAC_TER_BONUS ** x - 1) / (SAC_TER_BONUS - 1)

    return score
