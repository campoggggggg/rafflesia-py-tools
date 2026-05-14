import re
from .constants import KEYWORDS_MULT, ALWAYS_SAPPED_MULT, SUDDEN_MULT


def score_keywords_mult(card) -> float:
    mult = 1.0
    for keyword, base_mult in KEYWORDS_MULT.items():
        if keyword in card["keywords_list"]:
            mult *= base_mult
    return mult


def score_grant_keyword_mult(text: str) -> float:
    mult = 1.0
    for keyword, base_mult in KEYWORDS_MULT.items():
        if re.search(rf'gains?\b.*{keyword}', text):
            if "until end of turn" in text:
                base_mult *= 0.75
            mult *= base_mult
    return mult


def score_always_sapped_mult(text: str) -> float:
    if "always sapped" in text:
        return ALWAYS_SAPPED_MULT
    return 1.0


def score_sudden_mult(text: str) -> float:
    if text.startswith("sudden"):
        return SUDDEN_MULT
    return 1.0
