"""
classifier/features.py
=======================
Estrae un vettore di feature numeriche da ogni carta Rafflesia.

Feature:
  A) Strutturali  — costo, stats, tipo, colore, rarity
  B) power_score  — valore aggregato da efficiency/core.py
"""

import sys
import os
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from efficiency.core import efficiency as _power_score

# ─────────────────────────────────────────────────────────────────────────────
# UTILITA'
# ─────────────────────────────────────────────────────────────────────────────

def _safe_int(card, col, default=0):
    v = card.get(col, default)
    return int(v) if not pd.isna(v) else default

def _color(card):
    c = card.get("color", "colorless")
    return c.lower() if isinstance(c, str) else "colorless"

def _type(card):
    t = card.get("type_line", "")
    return t if isinstance(t, str) else ""


# ─────────────────────────────────────────────────────────────────────────────
# GRUPPO A - Feature strutturali
# ─────────────────────────────────────────────────────────────────────────────

def feat_cost_neutral(card):
    return _safe_int(card, "cost_neutral")

def feat_cost_color(card):
    return _safe_int(card, "cost_color")

def feat_cost_total(card):
    return feat_cost_neutral(card) + feat_cost_color(card)

def feat_cost_color_ratio(card):
    total = feat_cost_total(card)
    if total == 0:
        return 0.0
    return feat_cost_color(card) / total

def feat_atk(card):
    return _safe_int(card, "atk")

def feat_def(card):
    return _safe_int(card, "def")

def feat_stats_total(card):
    return feat_atk(card) + feat_def(card)

def feat_stats_per_cost(card):
    return feat_stats_total(card) / (feat_cost_total(card) + 1)

def feat_is_minion(card):
    return int(_type(card) == "Minion")

def feat_is_spell(card):
    return int(_type(card) == "Spell")

def feat_is_quest(card):
    return int(_type(card) == "Quest")

def feat_is_legendary(card):
    return int(card.get("rarity", "") == "Legendary")

def feat_color_black(card):
    return int(_color(card) == "black")

def feat_color_blue(card):
    return int(_color(card) == "blue")

def feat_color_red(card):
    return int(_color(card) == "red")

def feat_color_green(card):
    return int(_color(card) == "green")

def feat_color_colorless(card):
    return int(_color(card) == "colorless")


# ─────────────────────────────────────────────────────────────────────────────
# GRUPPO B - power_score
# ─────────────────────────────────────────────────────────────────────────────

def feat_power_score(card):
    try:
        score, _ = _power_score(pd.Series(card))
        return float(score)
    except Exception:
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# LISTA FEATURE ORDINATA
# ─────────────────────────────────────────────────────────────────────────────

FEATURE_NAMES = [
    # A - strutturali
    "cost_neutral", "cost_color", "cost_total", "cost_color_ratio",
    "atk", "def", "stats_total", "stats_per_cost",
    "is_minion", "is_spell", "is_quest",
    "is_legendary",
    "color_black", "color_blue", "color_red", "color_green", "color_colorless",
    # B - power score
    "power_score",
]

_FEAT_FN = {
    "cost_neutral":     feat_cost_neutral,
    "cost_color":       feat_cost_color,
    "cost_total":       feat_cost_total,
    "cost_color_ratio": feat_cost_color_ratio,
    "atk":              feat_atk,
    "def":              feat_def,
    "stats_total":      feat_stats_total,
    "stats_per_cost":   feat_stats_per_cost,
    "is_minion":        feat_is_minion,
    "is_spell":         feat_is_spell,
    "is_quest":         feat_is_quest,
    "is_legendary":     feat_is_legendary,
    "color_black":      feat_color_black,
    "color_blue":       feat_color_blue,
    "color_red":        feat_color_red,
    "color_green":      feat_color_green,
    "color_colorless":  feat_color_colorless,
    "power_score":      feat_power_score,
}


def extract_features(card: dict) -> dict:
    return {name: _FEAT_FN[name](card) for name in FEATURE_NAMES}


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, card in df.iterrows():
        rows.append(extract_features(card.to_dict()))
    return pd.DataFrame(rows, index=df.index, columns=FEATURE_NAMES)


# ─────────────────────────────────────────────────────────────────────────────
# DEBUG rapido
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from load_cards import load_cards

    df = load_cards()
    X = build_feature_matrix(df)
    print(f"Feature matrix: {X.shape[0]} carte x {X.shape[1]} feature")
    print("\nPrime 5 carte:")
    print(X.head())
    print("\nStatistiche descrittive:")
    print(X.describe().T[["mean", "min", "max"]].to_string())
