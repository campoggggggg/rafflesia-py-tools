import pandas as pd
import math
import re
from database.load_cards import load_cards
from text_normalizer import normalize_text

# KEYWORD
STEALTH_MULT = 1.33         # 
AGGRESSIVE_MULT = 1.20      # 
IMPULSIVE_MULT = 1.22       # 
PROTECTOR_MULT = 1.20       #
LIFEDRAIN_MULT = 1.1        # basso valore
ALWAYS_SAPPED_MULT = 0.8   # contrario di aggressive / 1/1.26

KEYWORDS_MULT = {
    "stealth":       STEALTH_MULT,
    "aggressive":    AGGRESSIVE_MULT,
    "protector":     PROTECTOR_MULT,
    "lifedrain":     LIFEDRAIN_MULT,
    "impulsive":     IMPULSIVE_MULT,
}

# BASIC COST
SPELL_CARD_VALUE = -0.0     # non ha stats, è già un malus implicito rispetto a un minion.

BOUNCE_ENEMY = +1.0
BOUNCE_ALLY = -0.2          #scelta attiva e ricercata, non malus puro ma calibrato. leva stat da terra comunque, quindi leggermente negativo

DISCARD_ALL = -2.5          # DA CAPIRE
DISCARD_1 = -0.8            # scartare è voluto, scelgo io la carta, a volte genera risorse a volte toglie roba brutta

DESTROY = 1.0

DAMAGE_1_ALL = 1.0
DAMAGE_1_TARGET = 0.7

SACRIFICE_TERRITORY = -2.0
# OTHER
MEDIAN_COST = 1.0           #
P75_MINION = 1.0            # placeholder; dopo introduci df dei minion — 75° percentile stimato
ALPHA = 1.3                 #costante di penalizzazione (costi alti sono meno efficienti, toglie linearità dalla scala)

df = load_cards()
df["cost_total"] = df["cost_neutral"].fillna(0) + df["cost_color"].fillna(0)

def efficiency(card):
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
            total = atk + def_
            if atk == 0:
                atk = 1
            balance = 1 - abs(atk - def_) / total
            return _add("stats", total * (balance ** 0.5))
        return _add("stats", 0)

    def _spell_card_cost():
        # giocare una spell costa una carta dalla mano — card disadvantage implicito
        if card["type_line"] == "Spell":
            return _add("spell_card_cost", SPELL_CARD_VALUE)
        return _add("spell_card_cost", 0)

    # ── DRAW E TOPDECK ──────────────────────────────────────────

    def _score_draw():
        match = re.search(r"draw (\d+).*move (\d+).*top", text)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            netto = x - y
            bonus = math.log(1 + y) * (x / (x + y))
            offset = 0 if card["type_line"] == "Minion" else -1.0
            return _add("draw_topdeck", 1.5 * netto + bonus + offset)

        # caso 2: solo draw X
        match = re.search(r"draw (\d+)", text)
        if match:
            x = int(match.group(1))
            return _add("draw", 1.5 * x)

        return _add("draw", 0)

    # ── KEYWORD ─────────────────────────────────────────────────

    def _score_grant_keyword_mult():
        mult = 1.0
        for keyword, base_mult in KEYWORDS_MULT.items():
            if "gain" in text and keyword in text:
                if "until end of turn" in text:
                    base_mult *= 0.75
                mult *= base_mult
        return mult

    def _score_keywords_mult():
        mult = 1.0
        for keyword, base_mult in KEYWORDS_MULT.items():
            if keyword in card["keywords_list"]:
                mult *= base_mult
                _add(keyword, base_mult)
        return mult
    
    def _score_always_sapped_mult():
        if "always sapped" in text:
            _add("always_sapped", ALWAYS_SAPPED_MULT)
            return ALWAYS_SAPPED_MULT
        return 1.0

    # ── BOUNCE ──────────────────────────────────────────────────

    def _score_bounce():
        # bounce avversario — rimuove temporaneamente una minaccia, valore positivo
        # bounce alleato — può essere un costo o un vantaggio (rigioca ETB)
        score = 0

        if "move target enemy" in text:
            score += BOUNCE_ENEMY
        if "move friendly minion" in text:
            score += BOUNCE_ALLY
        if "move all friendly minion" in text:
            score += BOUNCE_ALLY * 3.0 # creature medie in campo a mid game
        if "move all target enemy" in text:
            score += BOUNCE_ENEMY * 3.0 # creature medie in campo a mid game

        return _add("bounce", score)

    # ── DISCARD ─────────────────────────────────────────────────
    def _score_discard():
        score = 0

        if "banish up to 1 card among those revealed" in text: # bound by darkness
            score += 3.5 #discard 1 -> 1.5; SCELTA ->+ 0.5 -> guarda mano 0.75; banish invece di discard -> 0.75
            return _add("discard_opp", score)

        #non ci sono effetti che scartano all'avversario attualmente

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
        
        # negate semplice — massimo valore
        if "negate target card." in text:
            score = 2.5 #parto da counterspell in mgt ma mi sembra broken. forse meglio 2.5?

            match = re.search(r"cost of (\d) or less", text)
            if match:
                x = int(match.group(1))
                score *= (x + 2) / 8 # solo x/8 mi sembrava troppo punitivo
            if "equal to" in text:
                score *= 0.3
            if "discard" in text:
                score *= 0.5
            return _add("negate", score)

        return _add("negate", 0)

    # ── SACRIFICE ─────────────────────────────────────────────────

    def _score_sacrifice():
        score = 0

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
            score += -1.0

        if "destroy all friendly" in text:
            score += -2.5

        # destroy face-down — rimuove set cards, valore medio
        if "destroy target enemy face-down" in text:
            score += 0.8

        if "destroy target face-down" in text:
            score += 1.0

        # destroy territory — rimuove risorsa avversaria
        if "destroy target enemy card" in text:
            score += 2.0

        # destroy minion avversario — valore alto
        if "destroy target minion" in text:
            score += 1.6
        if "destroy target enemy minion" in text:
            score += 1.5

        # destroy all — board wipe, valore molto alto ma simmetrico
        if "destroy all" in text:
            score += 3.0

        return _add("destroy", score)

    # ── DEAL DAMAGE ─────────────────────────────────────────────

    def _score_deal_damage():
        score = 0

        match = re.search(r"deal (\d+) damage to all enemies", text)
        if match:
            x = int(match.group(1))
            score += (DAMAGE_1_ALL * 1.5) * x
            return _add("deal_damage_all_enemies", score)

        match = re.search(r"deal (\d+) damage to all minions", text)
        if match:
            x = int(match.group(1))
            score += (DAMAGE_1_ALL) * x
            return _add("deal_damage_all_minions", score)

        match = re.search(r"deal (\d+) damage to target opponent", text)
        if match:
            x = int(match.group(1))
            score += (DAMAGE_1_TARGET * 0.5) * x
            return _add("deal_damage_player", score)

        match = re.search(r"deal (\d+) damage to target", text)
        if match:
            x = int(match.group(1))
            score += DAMAGE_1_TARGET * x
            return _add("deal_damage_target", score)

        return _add("deal_damage", 0)

    # ── MUST ATTACK ─────────────────────────────────────────────

    def _score_must_attack():
        # limitazione — non puoi scegliere quando attaccare
        if "must attack if able" in text:
            return _add("must_attack", -0.3)
        return _add("must_attack", 0)

    # ── SUMMON FROM GRAVE ───────────────────────────────────────

    def _score_summon_from_grave():
        score = 0

        # summon territory dal cimitero — ramp/recupero
        if "summon" in text and "territory" in text and "grave" in text:
            score += 1.5

        # summon minion dal cimitero — reanimator, valore alto
        if "summon" in text and "minion" in text and "grave" in text:
            score += 2.5
        
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
            score += 3.5

        # costa N meno per ogni minion friendly — scala con board
        if "costs" in text and "less for each" in text and "minion" in text:
            score += 3.0

        # costa N meno fisso — semplice sconto
        match = re.search(r"costs? (\d+) less", text)
        if match and "each" not in text:
            x = int(match.group(1))
            score += x * 0.8

        # costo alternativo — sacrifica invece di pagare mana
        if "instead of paying" in text:
            score += 2.0

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
            return _add("gain_mana", x)
        return _add("gain_mana", 0)
    
    #── Legendary debuff ─────────────────────────────────────────
    def _score_leg_debuff(): #come mult
        rarity = card["rarity"] if not pd.isna(card["rarity"]) else ""
        if "legendary" in rarity.lower():
            return _add("legendary_debuff", 0.8)
        return 1.0

    # ── SOMMA TOTALE ────────────────────────────────────────────

    base_sum = (
        _score_stats()
        + _spell_card_cost()
        + _score_draw()
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

    total = (
        base_sum 
        * _score_grant_keyword_mult()
        * _score_keywords_mult()
        * _score_always_sapped_mult()
        * _score_leg_debuff()
    )

    return total / (cost + 1) , contributions # se vuoi valutare carte costose di meno fai ** ALPHA

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
    lambda c: efficiency(c)[0], axis=1
)
P75_MINION = df_minions["ps_temp"].quantile(0.75)
# END PASS 1

if __name__ == "__main__":
    df[["efficiency", "contributions"]] = df.apply(
        lambda card: pd.Series(efficiency(card)), axis=1
    )

    print(f"μ efficiency:    {df['efficiency'].mean():.3f}")
    print(f"σ efficiency: {df['efficiency'].var():.3f}")

    top = (df[["name", "type_line", "color", "cost_total", "atk", "def", "efficiency", "contributions"]]
           .sort_values("efficiency", ascending=False)
           .head(20) # top 20 carte
           )
    print()
    print(top[["name", "type_line", "color", "cost_total", "atk", "def", "efficiency"]])
    print()

    for _, row in top.iterrows():
        nonzero = {k: v for k, v in row["contributions"].items() if v != 0}
        print(f"{row['name']}: {nonzero}")

    