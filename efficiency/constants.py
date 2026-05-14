# KEYWORD MULTIPLIERS
STEALTH_MULT       = 1.33
AGGRESSIVE_MULT    = 1.20
IMPULSIVE_MULT     = 1.22
PROTECTOR_MULT     = 1.20
LIFEDRAIN_MULT     = 1.1
ALWAYS_SAPPED_MULT = 0.8   # contrario di aggressive
SUDDEN_MULT        = 1.2   # spell giocabile in qualsiasi momento

KEYWORDS_MULT = {
    "stealth":    STEALTH_MULT,
    "aggressive": AGGRESSIVE_MULT,
    "protector":  PROTECTOR_MULT,
    "lifedrain":  LIFEDRAIN_MULT,
    "impulsive":  IMPULSIVE_MULT,
}

DRAW_1            = 1.5
MULT_DRAW_DECAY   = 0.9

BOUNCE_ENEMY = +1.0
BOUNCE_ALLY  = -0.2

DISCARD_ALL         = -3.0
DISCARD_1           = -1.5
MULT_DISCARD_BONUS  = 1.05

NEGATE_VALUE = 3.5

DESTROY = 1.0

DAMAGE_ALL_ENEMIES_K = 2.4
DAMAGE_ALL_MINIONS_K = 2.2
DAMAGE_1_TARGET      = 0.7
DAMAGE_1_PLAYER      = 0.2

SACRIFICE_TERRITORY = -2.5
SAC_TER_BONUS       = 1.05

MEDIAN_COST = 1.0
P75_MINION  = 1.0
ALPHA       = 1.3

STATS_DELTA_K = 0.3

TOKEN_COEFFS = {
    "soldier": 1.0,
    "horde":   1.5,
    "ghoul":   2.5,
    "copy":    2.0,
}
