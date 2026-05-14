import re


def score_activated_cost(text: str) -> float:
    m = re.search(r"you may pay (\d+) mana", text)
    if m:
        x = int(m.group(1))
        return -0.25 * x
    return 0.0
