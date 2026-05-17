# rafflesia-py-tools

A Python toolset for quantitative analysis, balance evaluation, and power classification of **Rafflesia**, an original trading card game in development.

The goal is to assign each card a numerical **efficiency score** — an estimate of how much value a card provides relative to its mana cost — and to train a machine learning classifier that labels cards as *debole*, *bilanciata*, or *forte* to support data-driven design decisions.

---

## What it does

### Efficiency scoring engine (`efficiency/`)

The pipeline loads the card database from Supabase, normalizes card text into a canonical form, then runs a decomposed scoring function that evaluates each card's value from independent contributions:

- **Base stats** — exponential deviation from a cost-adjusted vanilla baseline (`cost × 2`), rewarding overstatted cards and penalizing understatted ones non-linearly via `copysign(sqrt(|delta|), delta)`
- **Keywords** — multiplicative modifiers applied to the base sum: `stealth ×1.33`, `aggressive ×1.20`, `impulsive ×1.22`, `protector ×1.20`, `lifedrain ×1.10`, `always sapped ×0.80`
- **Effects** — draw, bounce, discard, negate, destroy, deal damage, sacrifice, summon from grave, ramp, pump, mill, sap, and more, each with individually calibrated coefficients documented in `CALIBRATION.md`
- **Conditions** — a tiered multiplier system (`×0.9 / ×0.75 / ×0.5`) that discounts effects gated behind restrictive conditions, matched via regex patterns on normalized text
- **Card type modifiers** — spells, minions, quests, and territories handled with type-specific logic; Legendary rarity applies a `×0.8` penalty for reduced consistency

The raw sum is shifted, multiplied by keyword and condition multipliers, then divided by `(cost + 1)` to normalize efficiency across the mana curve.

Each scoring function logs its output to a `contributions` dict, so every card's final score is fully traceable to individual components:

```
Vessel of Forsaken Riches: {'draw': 1.5, 'condition_mult': 0.9}
Ancient Lich Lord:         {'stats': -2.506, 'always_sapped': 0.8}
Crimson Hunter:            {'stats': -1.192, 'aggressive': 1.2, 'pump': 1.2}
```

### ML classifier (`classifier/`)

A Random Forest classifier trained to label cards as *debole / bilanciata / forte*:

- **Training set** — all red cards (scoring model fully calibrated on them) plus a curated set of trusted cards from other colors and manual overrides in `labels-override.json`
- **Label assignment** — percentile-based thresholds (P33 / P67) computed exclusively on red cards, ensuring color-consistent calibration
- **Feature matrix** — 18 features combining structural card data (cost, stats, type, color, rarity) and the computed `power_score`
- **Cross-validation** — 5-fold stratified CV with F1-macro scoring; confusion matrix and per-class confidence reported at training time
- **Output** — enriched JSON (`data/classified_cards.json`) and a CSV report; low-confidence cards (< 55%) flagged for manual review

### Statistical analysis (`stats.py`)

Distribution analysis across the full card pool: boxplots and KDE by color and rarity, mana curve histograms (full pool / minions only / spells only), ATK vs DEF scatter, efficiency vs cost scatter with polynomial trendline, and modified Z-score outlier detection.

---

## Project structure

```
rafflesia-py-tools/
├── efficiency/
│   ├── core.py                  # orchestrates the full scoring pipeline
│   ├── constants.py             # all tunable coefficients
│   ├── score_stats.py           # stat deviation from vanilla baseline
│   ├── score_draw.py            # draw with geometric decay model
│   ├── score_deal_damage.py     # single-target, AoE, variable X damage
│   ├── score_destroy.py         # targeted and sweeper removal
│   ├── score_discard.py         # self-discard, hand discard, opponent discard
│   ├── score_move.py            # bounce, grave-to-hand, field-set placement
│   ├── score_negate.py          # counterspells with cost-cap scaling
│   ├── score_summon.py          # summon from grave, token generation
│   ├── score_mana_discount.py   # fixed and scaling cost reduction
│   ├── score_keywords.py        # keyword and grant-keyword multipliers
│   ├── score_condition.py       # condition tiers and legendary debuff
│   └── ...                      # sacrifice, sap, pump, ramp, mill, etc.
│
├── classifier/
│   ├── train.py                 # RF training with CV and threshold calibration
│   ├── classify.py              # batch classification of all cards
│   ├── features.py              # feature extraction (structural + power_score)
│   ├── plot_classified.py       # visual output: card images by class and color
│   └── labels-override.json     # manual ground-truth overrides
│
├── database/
│   ├── db_conn.py               # Supabase client
│   ├── load_cards.py            # loads cards + keywords + colors via joins
│   └── rafflesia-cards.json     # full card database (227 cards, set 1)
│
├── utility/
│   ├── text_normalizer.py       # regex normalization pipeline for card text
│   └── tierlist.py              # tier list visualization (S/A/B/C/F by σ distance)
│
├── data/
│   ├── classified_cards.json    # cards enriched with power_class + confidence
│   └── classified_cards_report.csv
│
├── stats.py                     # full statistical analysis and plotting
├── export_csv.py                # exports efficiency scores to CSV
├── main_efficiency.py           # two-pass efficiency computation
├── run_classifier.py            # runs train → classify → plot in sequence
├── _check_card.py               # CLI tool: inspect score breakdown for one card
└── CALIBRATION.md               # design notes and value justifications
```

---

## Technical highlights

**Text normalization pipeline** (`utility/text_normalizer.py`) — a rule-based regex system that canonicalizes card text variants into a consistent vocabulary before scoring. Handles synonyms, structural patterns (e.g. "set card" → "face-down", "return that summoned" → "move friendly minion"), edge cases, and game-specific phrasing. Pattern matching enforces word order (e.g. `summon.*from.*grave`) to avoid false positives from unrelated text fragments.

**Decomposed scoring with contribution tracking** — each scoring function logs its output independently, enabling per-card explainability. The `_check_card.py` CLI tool lets you inspect exactly which effects drove any card's score.

**Two-pass architecture** — a first pass over minions computes dataset statistics (percentiles, cost-group means) used to calibrate the second pass. The RF classifier reuses the same `power_score` as a feature alongside structural card attributes.

**Calibration-first design** — all coefficients are documented and justified in `CALIBRATION.md` with explicit reasoning (e.g. draw uses geometric decay with `DRAW_1=1.5` and `DECAY=0.9`; negate uses `3.5 × (1 - exp(-cost/3))` for cost-capped variants). Known edge cases and pending design fixes are tracked in the same file.

---

## Usage

```bash
# Check score breakdown for a specific card
python _check_card.py "lightning bolt"

# Run full efficiency export
python main_efficiency.py

# Train classifier, classify all cards, generate plots
python run_classifier.py

# Statistical analysis and plots
python stats.py
```

---

## Stack

| Area | Details |
|---|---|
| **Language** | Python 3 |
| **Database** | Supabase (PostgreSQL) via `supabase-py` |
| **ML** | scikit-learn (Random Forest, stratified CV, label encoding) |
| **Data** | pandas, numpy |
| **Statistics** | scipy (skew, kurtosis, MAD, modified Z-score) |
| **Visualization** | matplotlib, seaborn |
| **Text processing** | re (regex), custom normalization pipeline |
| **IDE integration** | Claude Code + MCP (`.claude/`) |

---

## Status

Active development. The scoring model is being iteratively calibrated against the full 227-card set. Known balance issues and pending fixes are tracked in `CALIBRATION.md`. The classifier training set is intentionally conservative — expanding trusted cards and override coverage is an ongoing process.
