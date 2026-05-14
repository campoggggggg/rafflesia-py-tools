import math
import re
from .constants import SACRIFICE_TERRITORY, TOKEN_COEFFS


def score_summon_from_grave(text: str) -> float:
    score = 0.0

    # TERRITORY
    if re.search(r"summon\b.{0,40}\bterritory\b.{0,40}\bgrave\b", text):
        score += abs(SACRIFICE_TERRITORY)

    # MINION dal grave
    if re.search(r"summon\b.{0,40}\bminion\b.{0,40}\bgrave\b", text):
        match = re.search(r"cost of (\d+) or less", text)
        if match:
            cap = int(match.group(1))
            score += math.log(1 + cap) * 1.4
        else:
            score += 3.0
        return score

    # conjured grave effect (es. Vino) — banish dalla grave per evocare dalla mano
    if re.search(r"while this is in your grave.*banish this.*summon a minion from your hand", text):
        return score + 3.0

    # summon this (sapped) — solo se non è il risultato di un costo "banish this"
    if re.search(r"summon this", text) and "banish this" not in text:
        if re.search(r"summon this sapped", text):
            score += 2.0
        else:
            score += 3.0

    return score


def score_summon_token(text: str) -> float:
    match = re.search(r"summon (\d+) \w+ token", text)
    if not match:
        return 0.0
    n = int(match.group(1))
    for token_type, coeff in TOKEN_COEFFS.items():
        if token_type in text:
            return n * coeff
    return 0.0
