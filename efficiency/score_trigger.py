### WHEN CONDITION
### ONCE PER TURN OR MORE

def score_trigger(text: str) -> float:
    score = 0.0

    if "once per turn" in text:
        score += 0.0 # 0.3
    if "twice per turn" in text:   
        score += 0.6
    if "thrice per turn" in text:
        score += 0.9

    if "when this attacks an enemy minion" in text:
        score += 0.3
    elif "when this attacks" in text:
        score += 0.4
    elif "When this is summoned or attacks" in text:
        score += 0.4

    if "when this damages an opponent" in text:
        score += 0.35
    if "when this is in your grave" in text:
        score += 0.3
    if "when you summon another minion" in text:
        score += 0.5
    if "when you summon an insector minion" in text:
        score += 0.35

    if "when you play a card" in text:
        score += 0.5
    elif "when you play a spell card" in text:
        score += 0.4
    elif "when you play a minion with a cost of 4 or more" in text:
        score += 0.3

    if "when you discard 1" in text:
        score += 0.3
    if "when you sacrifice 1 territory card" in text:
        score += 0.3

    if "when this is destroyed" in text:
        score += 0.2
    if "when this is damaged" in text:
        score += 0.2
    if "when this is sapped" in text:
        score += 0.2
    if "when this is discarded" in text:
        score += 0.2
    if "while this is in your hand, you may discard this" in text:
        score += 2.0
    if "when this is moved from the field" in text:
        score += 0.2
    if "when this leaves the field" in text:
        score += 0.2
    if "when this receives 1 or more damage" in text:
        score += 0.2
    if "when another friendly minion is destroyed" in text:
        score += 0.3
    if "when a territory card is moved to your grave" in text:
        score += 0.25
    if "when 1 or more friendly territories are sacrificed" in text:
        score += 0.25

    return score
