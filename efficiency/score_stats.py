import math
import pandas as pd


def score_stats(card) -> float:
    if card["type_line"] == "Minion":
        atk  = card["atk"]  if not pd.isna(card["atk"])  else 0
        def_ = card["def"]  if not pd.isna(card["def"])  else 0
        cost_neutral = card["cost_neutral"] if not pd.isna(card["cost_neutral"]) else 0
        cost_color   = card["cost_color"]   if not pd.isna(card["cost_color"])   else 0
        cost = cost_neutral + cost_color
        total = atk + def_
        if atk == 0:
            atk = 0.5
        vanilla     = cost * 2
        delta       = total - vanilla
        delta_score = math.copysign(math.sqrt(abs(delta)), delta)
        return delta_score
    return 0.0
