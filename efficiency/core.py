import pandas as pd
from utility.text_normalizer import normalize_text

from .score_stats          import score_stats
from .score_draw           import score_draw
from .score_keywords       import score_keywords_mult, score_grant_keyword_mult, score_always_sapped_mult, score_sudden_mult
from .score_move           import score_move
from .score_discard        import score_discard
from .score_negate         import score_negate
from .score_destroy        import score_destroy
from .score_deal_damage    import score_deal_damage
from .score_sacrifice      import score_sacrifice
from .score_summon         import score_summon_from_grave, score_summon_token
from .score_sap            import score_sap
from .score_pump           import score_pump
from .score_change_attack  import score_change_attack
from .score_must_attack    import score_must_attack
from .score_disruptive     import score_disruptive
from .score_scry           import score_scry, score_reveal_then_summon, score_reveal_then_draw
from .score_ramp           import score_ramp
from .score_recycle        import score_recycle
from .score_gain_life      import score_gain_life
from .score_mill           import score_mill
from .score_attach         import score_attach
from .score_mana_discount  import score_mana_discount
from .score_activated_cost import score_activated_cost
from .score_trigger        import score_trigger
from .score_condition      import score_condition_mult, score_leg_debuff


def efficiency(card):
    cost_neutral = card["cost_neutral"] if not pd.isna(card["cost_neutral"]) else 0
    cost_color   = card["cost_color"]   if not pd.isna(card["cost_color"])   else 0
    cost         = cost_neutral + cost_color
    text         = normalize_text(card["card_text"]) if not pd.isna(card["card_text"]) else ""

    contributions = {}

    def add(name, value):
        rounded = round(value, 3)
        if rounded != 0:
            contributions[name] = rounded
        return value

    s_stats = score_stats(card)
    add("stats", s_stats)

    base_sum = (
        s_stats
        + add("draw",               score_draw(text))
        + add("move",               score_move(text))
        + add("discard",            score_discard(text))
        + add("negate",             score_negate(text))
        + add("sacrifice",          score_sacrifice(text, s_stats))
        + add("destroy",            score_destroy(text))
        + add("deal_damage",        score_deal_damage(text))
        + add("must_attack",        score_must_attack(text))
        + add("disruptive",         score_disruptive(text))
        + add("summon_from_grave",  score_summon_from_grave(text))
        + add("summon_token",       score_summon_token(text))
        + add("attach",             score_attach(text))
        + add("mana_discount",      score_mana_discount(text, cost_neutral))
        + add("scry",               score_scry(text))
        + add("reveal_summon",      score_reveal_then_summon(text))
        + add("reveal_draw",        score_reveal_then_draw(text))
        + add("ramp",               score_ramp(text))
        + add("recycle",            score_recycle(text))
        + add("gain_life",          score_gain_life(text))
        + add("sap",                score_sap(text))
        + add("pump",               score_pump(text))
        + add("mill",               score_mill(text))
        + add("change_attack",      score_change_attack(text))
        + add("activated_cost",     score_activated_cost(text))
        + add("trigger",            score_trigger(text))
    )

    kw_mult      = score_grant_keyword_mult(text) * score_keywords_mult(card) * score_sudden_mult(text)
    penalty_mult = score_always_sapped_mult(text) * score_leg_debuff(card) * score_condition_mult(text)

    for keyword in ("stealth", "aggressive", "protector", "lifedrain", "impulsive"):
        if keyword in card["keywords_list"]:
            contributions[keyword] = contributions.get(keyword, round(kw_mult, 3))

    if kw_mult != 1.0:
        contributions["keyword_mult"] = round(kw_mult, 3)
    if penalty_mult != 1.0:
        contributions["penalty_mult"] = round(penalty_mult, 3)

    SHIFT = 100
    shifted = (base_sum + SHIFT) * kw_mult * penalty_mult
    total = shifted / (cost + 1)
    
    return total, contributions
