import pandas as pd
import math
import re
from load_cards import load_cards

STEALTH_MULT = 1.58         # log(1 + 1)/log(1 + 2) cioe garantire un'attivazione e/o attacco 
AGGRESSIVE_MULT = 1.26      # 
IMPULSIVE_MULT = 1.32       # 
PROTECTOR_MULT = 1.0        # activations_protector = DEF_minion / ATK_medio[costo_minion] || mult_protector = log(1 + activations_protector) / log(2)
LIFEDRAIN_MULT = 1.1        # basso valore
ALWAYS_SAPPED_MULT = 0.79   # contrario di aggressive / 1/1.26

MEDIAN_COST = 1.0           #
P75_MINION = 1.0            # placeholder; dopo introduci df dei minion — 75° percentile stimato
ALPHA = 1.3                 #costante di penalizzazione (costi alti sono meno efficienti, toglie linearità dalla scala)

df = load_cards()
df["cost_total"] = df["cost_neutral"].fillna(0) + df["cost_color"].fillna(0)

def power_score(card):
    cost_neutral = card["cost_neutral"] if not pd.isna(card["cost_neutral"]) else 0
    cost_color   = card["cost_color"]   if not pd.isna(card["cost_color"])   else 0
    cost         = cost_neutral + cost_color
    color        = card["color"].lower() if not pd.isna(card["color"]) else "colorless"
    text         = card["card_text"].lower() if not pd.isna(card["card_text"]) else ""
    
    # dizionario che traccia il contributo di ogni effetto
    contributions = {}

    def _add(name, value):
        # aggiunge il contributo al dizionario e lo restituisce
        # cosi possiamo sommare e tracciare allo stesso tempo
        contributions[name] = round(value, 3)
        return value

    # ── STATISTICHE BASE ────────────────────────────────────────

    def _score_stats():
        if card["type_line"] == "Minion":
            atk = card["atk"] if not pd.isna(card["atk"]) else 0
            def_ = card["def"] if not pd.isna(card["def"]) else 0
            return _add("stats", atk + def_)
        return _add("stats", 0)

    def _spell_card_cost():
        # giocare una spell costa una carta dalla mano — card disadvantage implicito
        if card["type_line"] == "Spell":
            return _add("spell_card_cost", -1)
        return _add("spell_card_cost", 0)

    # ── DRAW E TOPDECK ──────────────────────────────────────────

    def _score_draw():
        # caso 1: draw X e rimetti Y in cima — filtraggio
        # ln(1+x) / sqrt(1+y/2) cattura il valore netto del filtraggio
        match = re.search(r"draw (\d+).*move (\d+).*top", text)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            return _add("draw_topdeck", math.log(1 + x) / math.sqrt(1 + y / 2))

        # caso 2: solo draw X
        match = re.search(r"draw (\d+)", text)
        if match:
            x = int(match.group(1))
            return _add("draw", math.log(1 + x))

        return _add("draw", 0)

    # ── KEYWORD ─────────────────────────────────────────────────

    def _score_stealth_mult():
        # stealth impedisce di essere attaccati e targettati per un turno
        # è volatile ma permette a una carta di fare sicuramente almeno una volta l'effetto
        if "stealth" not in text:
            return 1.0
        if card["type_line"] == "Minion":
            return _add("stealth", STEALTH_MULT)
        return _add("stealth", P75_MINION * STEALTH_MULT)

    def _score_aggressive_mult():
        if "aggressive" in text:
            return _add("aggressive", AGGRESSIVE_MULT)
        return 1.0  # non _add, non serve tracciare i neutri

    def _score_impulsive_mult():
        if "impulsive" in text:
            return _add("impulsive", IMPULSIVE_MULT)
        return 1.0

    def _score_lifedrain_mult():
        if "lifedrain" in text or "life-drain" in text:
            return _add("lifedrain", LIFEDRAIN_MULT)
        return 1.0

    def _score_always_sapped_mult():
        if "always sapped" in text:
            return _add("always_sapped", ALWAYS_SAPPED_MULT)
        return 1.0

    def _score_protector_mult():
        if "protector" in text:
            return _add("protector", PROTECTOR_MULT)
        return 1.0

    # ── BOUNCE ──────────────────────────────────────────────────

    def _score_bounce():
        # bounce avversario — rimuove temporaneamente una minaccia, valore positivo
        # bounce alleato — può essere un costo o un vantaggio (rigioca ETB)
        score = 0

        if "move target enemy" in text and "hand" in text:
            # genera tempo sull'avversario
            score += 0.8
        if "move target minion" in text and "your hand" in text:
            # bounce alleato — contestuale, di base perde tempo ma crea nuove giocate
            score -= 0.2

        return _add("bounce", score)

    # ── DISCARD ─────────────────────────────────────────────────

    def _score_discard():
        score = 0

        # discard avversario — valore positivo, rimuove risorse
        if "target opponent" in text and "discard" in text:
            match = re.search(r"discard (\d+)", text)
            x = int(match.group(1)) if match else 1
            score += math.log(1 + x) * 0.8
            return _add("discard_opp", score)

        # discard your hand — malus pesante
        if "discard your hand" in text:
            return _add("discard_self_hand", -2.0)

        # discard X dalla propria mano — malus scalabile
        match = re.search(r"discard (\d+)", text)
        if match:
            x = int(match.group(1))
            score -= x * 0.8 # scartare è voluto, scelgo io la carta, a volte genera risorse a volte toglie roba brutta
            return _add("discard_self", score)

        return _add("discard", 0)

    # ── NEGATE ──────────────────────────────────────────────────

    def _score_negate():
        score = 0

        if "negate" not in text:
            return _add("negate", 0)
        
        # negate semplice — massimo valore

        if "negate target card.":
            score = 2.0

            match = re.search(r"cost of (\d) or less", text)
            if match:
                x = int(match.group(1))
                score *= x/8
            if "equal to" in text:
                score *= 0.25
            if "additional cost" in text:
                score *= 0.8
            if "discard" in text:
                score *= 0.5
            return _add("negate", score)

    # ── SACRIFICE ─────────────────────────────────────────────────

    def _score_sacrifice():
        score = 0

        if "sacrifice" not in text:
            return _add("sacrifice", 0)
        
        if "sacrifice this" in text:
            return _add("sacrifice", -_score_stats())
        
        match = re.search(r"sacrifice (\d) territory", text)
        if match:
            x = int(match.group(1))
            score += -x * 1.4

        match = re.search(r"sacrifice (\d) minion", text)
        if match:
            x = int(match.group(1))
            score += -x * 1.4
        return _add("sacrifice", score)
###### CONTROLLATO FINO A QUI ######

    # ── DESTROY ─────────────────────────────────────────────────

    def _score_destroy():
        score = 0

        # destroy alleato — malus o costo
        if "destroy target friendly" in text or "destroy all friendly" in text:
            score -= 0.5

        # destroy face-down — rimuove set cards, valore medio
        if "destroy target enemy face-down" in text or "face-down" in text:
            score += 0.5

        # destroy territory — rimuove risorsa avversaria
        if "destroy target" in text and "territory" in text and "friendly" not in text:
            score += 0.6

        # destroy minion avversario — valore alto
        if "destroy target" in text and ("minion" in text or "enemy" in text) and "friendly" not in text:
            score += 1.0

        # destroy all — board wipe, valore molto alto ma simmetrico
        if "destroy all" in text and "friendly" not in text:
            score += 1.5

        return _add("destroy", score)

    # ── DEAL DAMAGE ─────────────────────────────────────────────

    def _score_deal_damage():
        score = 0

        # deal X damage to all — valore alto, colpisce tutto
        if re.search(r"deal \d+ damage to all", text):
            match = re.search(r"deal (\d+) damage to all", text)
            x = int(match.group(1)) if match else 1
            score += math.log(1 + x) * 1.2
            return _add("deal_damage_all", score)

        # deal X damage to target minion or player — flessibile, vale di piu
        if "minion or player" in text or "enemy" in text and "damage" in text:
            match = re.search(r"deal (\d+) damage", text)
            x = int(match.group(1)) if match else 1
            score += math.log(1 + x) * 1.0
            return _add("deal_damage_flexible", score)

        # deal X damage to target minion — solo minion
        if "damage to target minion" in text:
            match = re.search(r"deal (\d+) damage", text)
            x = int(match.group(1)) if match else 1
            score += math.log(1 + x) * 0.8
            return _add("deal_damage_minion", score)

        # deal X damage variabile (es. "deal X damage where X is...")
        if "deal" in text and "damage" in text:
            score += 0.5
            return _add("deal_damage_variable", score)

        return _add("deal_damage", 0)

    # ── MUST ATTACK ─────────────────────────────────────────────

    def _score_must_attack():
        # limitazione — non puoi scegliere quando attaccare
        if "must attack if able" in text:
            return _add("must_attack", -0.4)
        return _add("must_attack", 0)

    # ── SUMMON FROM GRAVE ───────────────────────────────────────

    def _score_summon_from_grave():
        score = 0

        # summon territory dal cimitero — ramp/recupero
        if "summon" in text and "territory" in text and "grave" in text:
            score += 0.6

        # summon minion dal cimitero — reanimator, valore alto
        if "summon" in text and "minion" in text and "grave" in text:
            match = re.search(r"cost of (\d+) or less", text)
            if match:
                cap = int(match.group(1))
                # piu alto il cap, piu forte
                score += math.log(1 + cap) * 0.5
            else:
                score += 1.0

        return _add("summon_from_grave", score)

    # ── ATTACH ──────────────────────────────────────────────────

    def _score_attach():
        # attach aggiunge carte a un minion per effetti bonus
        # valore dipende dal contesto, per ora fisso
        if "attach" in text:
            return _add("attach", 0.4)
        return _add("attach", 0)

    # ── MANA DISCOUNT ───────────────────────────────────────────

    def _score_mana_discount():
        score = 0

        # costa N meno per ogni carta al cimitero — scala in lategame
        if "costs" in text and "less for each" in text and "grave" in text:
            score += 0.8

        # costa N meno per ogni minion friendly — scala con board
        if "costs" in text and "less for each" in text and "minion" in text:
            score += 0.7

        # costa N meno fisso — semplice sconto
        match = re.search(r"costs? (\d+) less", text)
        if match and "each" not in text:
            x = int(match.group(1))
            score += x * 0.3

        # costo alternativo — sacrifica invece di pagare mana
        if "instead of paying" in text:
            score += 0.3

        return _add("mana_discount", score)

    # ── SCRY / REVEAL ───────────────────────────────────────────

    def _score_scry():
        # reveal top X — informazione + selezione parziale
        match = re.search(r"reveal the top (\d+)", text)
        if match:
            x = int(match.group(1))
            return _add("scry", math.log(1 + x) * 0.3)
        return _add("scry", 0)

    def _score_reveal_then_summon():
        # rivela e evoca — valore dipende dal cap di costo
        if "reveal" in text and "summon" in text and "grave" not in text:
            match = re.search(r"cost of (\d+) or less", text)
            if match:
                cap = int(match.group(1))
                return _add("reveal_summon", math.log(1 + cap) * 0.4)
            return _add("reveal_summon", 0.5)
        return _add("reveal_summon", 0)

    def _score_reveal_then_draw():
        # rivela e pesca — valore informazione + carta
        if "reveal" in text and ("move" in text or "draw" in text) and "top" in text:
            return _add("reveal_draw", 0.3)
        return _add("reveal_draw", 0)

    # ── RAMP ────────────────────────────────────────────────────

    def _score_ramp():
        # gain mana color — accelerazione risorse, molto forte
        match = re.search(r"gain \(([BGRUC]+)\)", text)
        if match:
            x = len(match.group(1))  # numero di simboli mana guadagnati
            return _add("ramp", x * 0.7)
        return _add("ramp", 0)

    # ── RECYCLE ─────────────────────────────────────────────────

    def _score_recycle():
        # recycle rimette carte nel mazzo — valore dipende da quante
        match = re.search(r"recycle (\d+)", text)
        if match:
            x = int(match.group(1))
            return _add("recycle", math.log(1 + x) * 0.2)
        if "recycle" in text:
            return _add("recycle", 0.2)
        return _add("recycle", 0)

    # ── GAIN LIFE ───────────────────────────────────────────────

    def _score_gain_life():
        match = re.search(r"gain (\d+) life", text)
        if match:
            x = int(match.group(1))
            # scala logaritmicamente — guadagnare 10 vita non è il doppio di 5
            return _add("gain_life", math.log(1 + x) * 0.3)
        return _add("gain_life", 0)

    # ── SAP ─────────────────────────────────────────────────────

    def _score_sap():
        score = 0

        # sap all enemy — molto forte
        if "sap all enemy" in text:
            score += 1.2

        # sap target enemy — rimuove attacco temporaneamente
        if "sap target enemy" in text or "sap target minion" in text:
            score += 0.6

        # sap self — costo o limitazione
        if "sap this" in text:
            score -= 0.3

        return _add("sap", score)

    # ── PUMP (+X/+Y) ────────────────────────────────────────────

    def _score_pump():
        # +X/+Y a un minion — valore scalabile
        match = re.search(r"\+(\d+)/\+(\d+)", text)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            return _add("pump", (x + y) * 0.3)

        # +X/+0 o +0/+Y — pump parziale
        match = re.search(r"\+(\d+)/\+0|\+0/\+(\d+)", text)
        if match:
            val = int(match.group(1) or match.group(2))
            return _add("pump_partial", val * 0.2)

        return _add("pump", 0)

    # ── MILL ────────────────────────────────────────────────────

    def _score_mill():
        # mill X — manda carte al cimitero (proprio o avversario)
        match = re.search(r"mill (\d+)", text)
        if match:
            x = int(match.group(1))
            # mill avversario vale di piu
            if "opponent" in text:
                return _add("mill", math.log(1 + x) * 0.4)
            # mill proprio — spesso è un costo o setup per grave effects
            return _add("mill", math.log(1 + x) * 0.1)
        return _add("mill", 0)

    # ── GAIN MANA ───────────────────────────────────────────────

    def _score_gain_mana():
        # gain X mana neutro — accelerazione temporanea
        match = re.search(r"gain (\d+) mana", text)
        if match:
            x = int(match.group(1))
            return _add("gain_mana", x * 0.5)
        return _add("gain_mana", 0)

    # ── MINION TO BOTDECK ───────────────────────────────────────

    def _score_minion_to_botdeck():
        # manda minion avversario in fondo al mazzo — rimozione soft
        if ("bottom" in text or "botdeck" in text) and "deck" in text and "enemy" in text:
            return _add("minion_to_botdeck", 0.7)
        return _add("minion_to_botdeck", 0)

    # ── SOMMA TOTALE ────────────────────────────────────────────
    acc = 1 / (1 + math.exp(cost - MEDIAN_COST))

    base_sum = (
        _score_stats()
        + _spell_card_cost()
        + acc * (
            _score_draw()
        + _score_bounce()
        + _score_discard()
        + _score_negate()
        + _score_sacrifice()
        + _score_destroy()
        + _score_deal_damage()
        + _score_must_attack()
        + _score_summon_from_grave()
        + _score_attach()
        + _score_mana_discount()
        + _score_scry()
        + _score_reveal_then_summon()
        + _score_reveal_then_draw()
        + _score_ramp()
        + _score_recycle()
        + _score_gain_life()
        + _score_sap()
        + _score_pump()
        + _score_mill()
        + _score_gain_mana()
        + _score_minion_to_botdeck()
        )
    )

    total = (
        base_sum 
        * _score_stealth_mult()
        * _score_aggressive_mult()
        * _score_protector_mult()
        * _score_impulsive_mult()
        * _score_lifedrain_mult()
        *_score_always_sapped_mult()

    )

    return total / (cost + 1) ** ALPHA, contributions

MEDIAN_COST = df["cost_total"].median()

df_minions = df[df["type_line"] == "Minion"].copy()
df_minions["ps_temp"] = df_minions.apply(
    lambda c: power_score(c)[0], axis=1
)
P75_MINION = df_minions["ps_temp"].quantile(0.75)

print(f"MEDIAN_COST: {MEDIAN_COST}")
print(f"P75_MINION:  {P75_MINION}")

if __name__ == "__main__":
    df[["power_score", "contributions"]] = df.apply(
        lambda card: pd.Series(power_score(card)), axis=1
    )
    print(df[["name", "type_line", "color", "cost_neutral", "cost_color", "atk", "def", "power_score"]]
          .sort_values("power_score", ascending=False)
          .head(30))