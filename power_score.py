import pandas as pd
import math
import re
from load_cards import load_cards
from text_normalizer import normalize_text

# KEYWORD
STEALTH_MULT = 1.58         # log(1 + 1)/log(1 + 2) cioe garantire un'attivazione e/o attacco 
AGGRESSIVE_MULT = 1.26      # 
IMPULSIVE_MULT = 1.32       # 
PROTECTOR_MULT = 1.29       #
LIFEDRAIN_MULT = 1.1        # basso valore
ALWAYS_SAPPED_MULT = 0.79   # contrario di aggressive / 1/1.26

# BASIC COST
SPELL_CARD_VALUE = -1.0

BOUNCE_ENEMY = +1.0
BOUNCE_ALLY = -0.5

DISCARD_ALL = -2.5          # DA CAPIRE
DISCARD_1 = -0.8            # scartare è voluto, scelgo io la carta, a volte genera risorse a volte toglie roba brutta

DESTROY = 1.0

DAMAGE_1_ALL = 0.7

SACRIFICE_TERRITORY = -1.5
# OTHER
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
    text         = normalize_text(card["card_text"]) if not pd.isna(card["card_text"]) else ""
    
    # dizionario che traccia il contributo di ogni effetto
    contributions = {}

    def _add(name, value):
        # aggiunge il contributo al dizionario e lo restituisce
        # cosi possiamo sommare e tracciare allo stesso tempo
        contributions[name] = round(value, 3)
        return value

    # ── STATISTICHE BASE ────────────────────────────────────────

    # se minion, ritorna atk+def. poi verrà diviso per (costo + 1)^alpha
    def _score_stats(): 
        if card["type_line"] == "Minion":
            atk = card["atk"] if not pd.isna(card["atk"]) else 0
            def_ = card["def"] if not pd.isna(card["def"]) else 0
            return _add("stats", atk + def_)
        return _add("stats", 0)

    def _spell_card_cost():
        # giocare una spell costa una carta dalla mano — card disadvantage implicito
        if card["type_line"] == "Spell":
            return _add("spell_card_cost", SPELL_CARD_VALUE)
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
        if "lifedrain" in text:
            return _add("lifedrain", LIFEDRAIN_MULT)
        return 1.0

    def _score_always_sapped_mult():
        if "always sapped" in text:
            return _add("always_sapped", ALWAYS_SAPPED_MULT)
        return 1.0

    def _score_protector_mult():
        if "protector" in text:
            #check per vedere se un protector è understats per il suo costo
            atk_ref = atk_mean_per_cost[cost]
            def_ = card["def"] if not pd.isna(card["def"]) else 0
            ratio = def_ / atk_ref
            prt_mult = math.log(1 + ratio) / math.log(2)
            if prt_mult <= 1.0:
                print(f"[PROTECTOR WARNING] {card['name']} — prt_mult={prt_mult:.3f} (DEF={def_}, ATK_medio={atk_ref:.2f}, cost={cost})") # check in caso di mult <= 1.0
            return _add("protector", PROTECTOR_MULT)
        return 1.0

    # ── BOUNCE ──────────────────────────────────────────────────

    def _score_bounce():
        # bounce avversario — rimuove temporaneamente una minaccia, valore positivo
        # bounce alleato — può essere un costo o un vantaggio (rigioca ETB)
        score = 0

        if "move target enemy" in text:
            # genera tempo sull'avversario
            score += BOUNCE_ENEMY
        if "move friendly minion" in text:
            # bounce alleato — contestuale, di base perde tempo ma crea nuove giocate
            score += BOUNCE_ALLY

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
            return _add("discard_self_hand", DISCARD_ALL)

        # discard X dalla propria mano — malus scalabile
        match = re.search(r"discard (\d+)", text)
        if match:
            x = int(match.group(1))
            score += x * DISCARD_1 
            return _add("discard_self", score)

        return _add("discard", 0)

    # ── NEGATE ──────────────────────────────────────────────────

    def _score_negate():
        score = 0

        if "negate" not in text:
            return _add("negate", 0)
        
        # negate semplice — massimo valore

        if "negate target card." in text:
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

        return _add("negate", 0)

    # ── SACRIFICE ─────────────────────────────────────────────────

    def _score_sacrifice():
        score = 0

        if "sacrifice" not in text:
            return _add("sacrifice", 0)

        if "sacrifice this" in text:
            return _add("sacrifice", -_score_stats())

        match = re.search(r"sacrifice (\d+) territory card", text)
        if match:
            x = int(match.group(1))
            score += x * SACRIFICE_TERRITORY

        return _add("sacrifice", score)
    # ── DESTROY ─────────────────────────────────────────────────

    def _score_destroy():
        score = 0

        # destroy alleato — malus o costo
        if "destroy target friendly" in text:
            score += 0.5

        if "destroy all friendly" in text:
            score += 1.0

        # destroy face-down — rimuove set cards, valore medio
        if "destroy target enemy face-down" in text:
            score += DESTROY / 3

        if "destroy target face-down" in text:
            score += (DESTROY + DESTROY * 0.1) / 3

        # destroy territory — rimuove risorsa avversaria
        if "destroy target enemy card" in text:
            score += DESTROY + DESTROY * 0.5

        # destroy minion avversario — valore alto
        if "destroy target minion" in text:
            score += (DESTROY + DESTROY*0.1)
        if "destro target enemy minion" in text:
            score += DESTROY

        # destroy all — board wipe, valore molto alto ma simmetrico
        if "destroy all" in text:
            score += (DESTROY + DESTROY*1.5)

        return _add("destroy", score)

############### CONTROLLATO FINO A QUI ################

    # ── DEAL DAMAGE ─────────────────────────────────────────────

    def _score_deal_damage():
        score = 0

        match = re.search(r"deal (\d+) damage to all enemies", text)
        if match:
            x = int(match.group(1))
            score += (DAMAGE_1_ALL * DAMAGE_1_ALL * 0.5) * x
            return _add("deal_damage_all_enemies", score)

        match = re.search(r"deal (\d+) damage to all minions", text)
        if match:
            x = int(match.group(1))
            score += (DAMAGE_1_ALL - DAMAGE_1_ALL * 0.3) * x
            return _add("deal_damage_all_minions", score)

        match = re.search(r"deal (\d+) damage to target opponent", text)
        if match:
            x = int(match.group(1))
            score += (DAMAGE_1_ALL - DAMAGE_1_ALL * 0.3) * x
            return _add("deal_damage_player", score)

        match = re.search(r"deal (\d+) damage to target", text)
        if match:
            x = int(match.group(1))
            score += DAMAGE_1_ALL * x
            return _add("deal_damage_target", score)

        return _add("deal_damage", 0)

    # ── MUST ATTACK ─────────────────────────────────────────────

    def _score_must_attack():
        # limitazione — non puoi scegliere quando attaccare
        if "must attack if able" in text:
            return _add("must_attack", -0.2)
        return _add("must_attack", 0)

    # ── SUMMON FROM GRAVE ───────────────────────────────────────

    def _score_summon_from_grave():
        score = 0

        # summon territory dal cimitero — ramp/recupero
        if "summon" in text and "territory" in text and "grave" in text:
            score += 1.0

        # summon minion dal cimitero — reanimator, valore alto
        if "summon" in text and "minion" in text and "grave" in text:
            score += 1.0
        
        return _add("summon_from_grave", score)

    # ── ATTACH ──────────────────────────────────────────────────

    def _score_attach():
        # attach aggiunge carte a un minion per effetti bonus
        # valore dipende dal contesto, per ora fisso
        if "attach" in text:
            return _add("attach", 0) # decidere contesto e logica
        return _add("attach", 0)

    # ── MANA DISCOUNT ───────────────────────────────────────────

    def _score_mana_discount():
        score = 0

        # costa N meno per ogni carta al cimitero — scala in lategame
        if "costs" in text and "less for each" in text and "grave" in text:
            score += 1.2

        # costa N meno per ogni minion friendly — scala con board
        if "costs" in text and "less for each" in text and "minion" in text:
            score += 0.9

        # costa N meno fisso — semplice sconto
        match = re.search(r"costs? (\d+) less", text)
        if match and "each" not in text:
            x = int(match.group(1))
            score += x * 0.3

        # costo alternativo — sacrifica invece di pagare mana
        if "instead of paying" in text:
            score += 0.8

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
    # ogni mana normalizzato a un generico (M)
    def _score_ramp():
        match = re.search(r"gain (\(M\))+", text)
        if match:
            n = len(re.findall(r"\(M\)", match.group(0)))
            return _add("ramp", n * 0.7)
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
            score += 0.8

        # sap target enemy — rimuove attacco temporaneamente
        if "sap target enemy" in text or "sap target minion" in text:
            score += 0.4

        # sap self — costo o limitazione
        if "sap this" in text:
            score += -0.3

        return _add("sap", score)

    # ── PUMP (+X/+Y) ────────────────────────────────────────────

    def _score_pump():
        score = 0

        # pump positivo su friendly — +X/+Y
        match = re.search(r"gains? \+(\d+)/\+(\d+)", text)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            base = (x + y)
            if "until the end of" not in text:
                score += base
            else:
                score += base * 0.5

        # debuff negativo su enemy — -X/-Y (stesso valore, è rimozione parziale)
        match = re.search(r"gains? -(\d+)/-(\d+)", text)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            base = (x + y)
            if "until the end of" not in text:
                score += base
            else:
                score += base * 0.5

        return _add("pump", score)

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

# PASS 1
MEDIAN_COST = df["cost_total"].median()

df_minions = df[df["type_line"] == "Minion"].copy()

atk_mean_per_cost = (
    df_minions
    .groupby("cost_total")["atk"]
    .mean()
    .fillna(1.0) # caso limite in cui un costo ha solo minion senza atk
    .to_dict()
)
df_minions["ps_temp"] = df_minions.apply(
    lambda c: power_score(c)[0], axis=1
)
P75_MINION = df_minions["ps_temp"].quantile(0.75)
# END PASS 1

if __name__ == "__main__":
    df[["power_score", "contributions"]] = df.apply(
        lambda card: pd.Series(power_score(card)), axis=1
    )
    
    print(f"μ power_score:    {df['power_score'].mean():.3f}")
    print(f"σ power_score: {df['power_score'].var():.3f}")

    top = (df[["name", "type_line", "color", "cost_total", "atk", "def", "power_score", "contributions"]]
           .sort_values("power_score", ascending=False)
           .head(30))
    print()
    print(top[["name", "type_line", "color", "cost_total", "atk", "def", "power_score"]])
    print()
    
    for _, row in top.iterrows():
        nonzero = {k: v for k, v in row["contributions"].items() if v != 0}
        print(f"{row['name']}: {nonzero}")

    