import re


def score_mana_discount(text: str, cost_neutral: float) -> float:
    score = 0.0

    if re.search(r"costs\b[^.]*\bless for each\b[^.]*\.", text):
        n = int(cost_neutral)
        score += min(0.8 * n, 3.0)
    else:
        m = re.search(r"costs? (\d+) less(?! for each)", text)
        if m:
            score += int(m.group(1)) * 0.8

    if "instead of paying" in text or "you may play this for free" in text:
        score += cost_neutral * 0.5

    return score
