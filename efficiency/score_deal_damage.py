import math
import re
from .constants import DAMAGE_ALL_ENEMIES_K, DAMAGE_ALL_MINIONS_K, DAMAGE_1_TARGET, DAMAGE_1_PLAYER


def score_deal_damage(text: str) -> float:
    # area dmg — colpisce anche il giocatore
    match = re.search(r"deal (\d+) damage to all enemies", text)
    if match:
        x = int(match.group(1))
        return math.log(1 + x) * (DAMAGE_ALL_ENEMIES_K + DAMAGE_1_PLAYER)

    # area dmg — solo minion
    match = re.search(r"deal (\d+) damage to all minions", text)
    if match:
        x = int(match.group(1))
        return math.log(1 + x) * DAMAGE_ALL_MINIONS_K

    # single target — minion o player
    match = re.search(r"deal (\d+) damage to target minion or player", text)
    if match:
        x = int(match.group(1))
        return (DAMAGE_1_TARGET + DAMAGE_1_PLAYER) * x

    # single target — solo enemy
    match = re.search(r"deal (\d+) damage to target enemy", text)
    if match:
        x = int(match.group(1))
        return DAMAGE_1_TARGET * x

    # single target — solo opponent player
    match = re.search(r"deal (\d+) damage to target opponent", text)
    if match:
        x = int(match.group(1))
        return DAMAGE_1_PLAYER * x

    # single target — X variabile (scala con board o altro)
    if re.search(r"deal x damage to target", text):
        return 2.0

    return 0.0
