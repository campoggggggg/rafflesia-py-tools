import re
import pandas as pd


def score_condition_mult(text: str) -> float:
    mult = 1.0

    # tier 0.9 — quasi sempre vera
    if re.search(r"if (it|this) wasn't played from your hand", text):
        mult *= 0.9
    elif re.search(r"if (it |this )?was(n't)? played", text):
        mult *= 0.9
    if "if this dealt damage this turn" in text:
        mult *= 0.9
    if re.search(r"if it was summoned by the effect of", text):
        mult *= 0.9

    # tier 0.75 — abbastanza comune
    if "if this is the only card in your hand" in text:
        mult *= 0.75
    if "if you have 2 or less cards in hand" in text:
        mult *= 0.75
    if "if you have less than 1 card in your grave" in text:
        mult *= 0.75

    # tier 0.5 — restrittiva
    if "if a territory card was moved to your grave this turn" in text:
        mult *= 0.5
    if "if you have no cards in your hand" in text:
        mult *= 0.5
    if "if a card was moved from your field to your hand this turn" in text:
        mult *= 0.5
    if "if you have 6 or more cards in your hand" in text:
        mult *= 0.5
    if "if you have no minion cards in your grave" in text:
        mult *= 0.5
    if "if you summoned no territories during this turn" in text:
        mult *= 0.5
    if "if you have 5 or more spell cards in your grave" in text:
        mult *= 0.5
    if "if there are no minions on your field" in text:
        mult *= 0.5
    if "if you had no cards in your grave when this was played" in text:
        mult *= 0.5
    if "if you have more than 4 cards in your grave" in text:
        mult *= 0.5
    if "if you have no cards in your deck" in text:
        mult *= 0.5

    return mult


def score_leg_debuff(card) -> float:
    rarity = card["rarity"] if not pd.isna(card["rarity"]) else ""
    if "legendary" in rarity.lower():
        return 0.8
    return 1.0
