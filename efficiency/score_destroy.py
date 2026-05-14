import re


def score_destroy(text: str) -> float:
    score = 0.0

    def count(pattern):
        return len(re.findall(pattern, text))

    score += count(r"destroy target enemy minion")             *  1.6
    score += count(r"destroy target friendly minion")          * -1.0
    score += count(r"destroy target minion(?! or)(?! with)")   *  1.8

    score += count(r"destroy target enemy face-down")          *  1.0
    score += count(r"destroy target friendly face-down")       * -0.5
    score += count(r"destroy target face-down")                *  1.1

    score += count(r"destroy target minion or face-down")      *  1.8
    score += count(r"destroy target enemy card")               *  2.5

    if "destroy all enemy minions" in text:
        base = 4.5
        m = re.search(r"destroy all enemy minions with (\d+) or less", text)
        if m:
            cap = int(m.group(1))
            base = base * min(cap, 8) / 8
        score += base
    elif "destroy all friendly minions" in text:
        score += -2.5
    elif "destroy all minions" in text:
        score += 4.0

    if "destroy all enemy face-down" in text:
        score += 2.2
    elif "destroy all friendly face-down" in text:
        score += -1.0
    elif "destroy all face-down" in text:
        score += 2.0

    if "banish target minion" in text:
        score += 2.0

    return score
