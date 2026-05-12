# Rafflesia py-tools

A Python toolset for quantitative analysis and balance evaluation of **Rafflesia**, an original trading card game currently in development.

The goal is to assign each card an **efficiency score** — a numerical estimate of how much value a card provides relative to its mana cost — to support data-driven design decisions during development.

---

## What it does

The pipeline loads a card database (JSON), normalizes card text into a canonical form, and runs a scoring function that decomposes each card's value into independent contributions:

- **Base stats** — evaluated as exponential deviation from a cost-adjusted vanilla baseline (`cost × 2`), rewarding overstatted cards and penalizing understatted ones non-linearly
- **Keywords** — multiplicative modifiers (stealth, aggressive, impulsive, protector, lifedrain, always sapped)
- **Effects** — draw, bounce, discard, damage, destroy, negate, ramp, pump, mill, sacrifice, summon from grave, mana discount, and more
- **Conditions** — a tiered multiplier system (0.9 / 0.75 / 0.5) that discounts effects gated behind restrictive conditions
- **Card type** — spells, minions, quests, and territories are handled with type-specific logic

The final score is divided by `(cost + 1)` to normalize efficiency across mana costs, making cheap and expensive cards comparable on the same scale.

---

## Project structure

```
rafflesia-py-tools/
├── efficiency.py          # core scoring engine
├── text_normalizer.py     # regex-based card text normalization pipeline
├── database/
│   ├── db_conn.py
│   ├── load_cards.py      
│   └──rafflesia-cards.json   
├── stats.py               
├── CALIBRATION.md         # design notes and value justifications for each scoring parameter
└── README.md
```

---

## Technical highlights

- **Text normalization pipeline** (`text_normalizer.py`) — rule-based regex system that canonicalizes card text variants into a consistent vocabulary before scoring. Handles synonyms, edge cases, and game-specific phrasing.
- **Pattern matching with ordering constraints** — regex patterns enforce word order (e.g. `summon.*from.*grave` instead of independent `in text` checks) to avoid false positives from unrelated card text fragments.
- **Decomposed scoring with contribution tracking** — each scoring function logs its output to a `contributions` dict, enabling per-card explainability: you can inspect exactly which effects drove the score.
- **Two-pass architecture** — a first pass over minions computes dataset statistics (percentiles, cost-group means) used to calibrate the second pass.
- **Pandas + math + re** — no external ML dependencies; the model is fully interpretable and hand-calibrated.

---

## Skills demonstrated

| Area | Details |
|---|---|
| **Python** | functional decomposition, closures, regex, pandas DataFrames, `math` module, data pipelines |
| **Data analysis** | distribution analysis, percentile-based calibration, scoring model design, diminishing returns modeling (geometric decay, exponential curves) |
| **Software design** | separation of concerns (normalize → score → analyze), maintainability, documented constants, explainable outputs |
| **Domain modeling** | translating informal game design intuitions into formal mathematical functions with tunable parameters |

---

## Example output

```
Vessel of Forsaken Riches: {'negate': 3.5, 'condition_mult': 0.75}
Ancient Lich Lord:         {'stats': 0.0, 'summon_from_grave': 3.0, 'always_sapped': 0.8}
Crimson Hunter:            {'stats': 2.32, 'aggressive': 1.2, 'deal_damage_target': 1.4}
```

Each card's score is fully traceable to its individual contributions.

---

## Status

Active development. The scoring model is being iteratively calibrated against the full card set, with known edge cases tracked in [CALIBRATION.md](CALIBRATION.md).
