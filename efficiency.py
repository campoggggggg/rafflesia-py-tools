import pandas as pd
import math
import re
from database.load_cards import load_cards
from utility.text_normalizer import normalize_text

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

DRAW_1 = 1.5
MULT_DRAW_DECAY = 0.9            # ogni carta pescata vale il 90% della precedente, scala logaritmica   

BOUNCE_ENEMY = +1.0
BOUNCE_ALLY = -0.2          #scelta attiva e ricercata, non malus puro ma calibrato. leva stat da terra comunque, quindi leggermente negativo

DISCARD_ALL = -3.5          # DA CAPIRE
DISCARD_1 = -1.5            # scartare 1 > draw 1 in proporzione
MULT_DISCARD_BONUS = 1.05   # 5%

NEGATE_VALUE = 3.5

DESTROY = 1.0

DAMAGE_ALL_ENEMIES_K = 2.4
DAMAGE_ALL_MINIONS_K = 2.2
DAMAGE_1_TARGET = 0.7
DAMAGE_1_PLAYER = 0.2

SACRIFICE_TERRITORY = -2.5 # per giocare terr "scarto" una carta, e perdo una risorsa grossa (1.5 + 1.0)
SAC_TER_BONUS = 1.05
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

    STATS_DELTA_K = 0.3

    def _score_stats():
        if card["type_line"] == "Minion":
            atk = card["atk"] if not pd.isna(card["atk"]) else 0
            def_ = card["def"] if not pd.isna(card["def"]) else 0
            total = atk + def_
            if atk == 0:
                atk = 0.5
            balance = 1 - abs(atk - def_) / total
            vanilla = cost * 2
            delta = total - vanilla
            delta_score = math.copysign(math.exp(abs(delta) * STATS_DELTA_K) - 1, delta)
            return _add("stats", delta_score * (balance ** 0.5))
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
            # offset = 0 if card["type_line"] == "Minion" else -1.0
            return _add("draw_topdeck", (DRAW_1 * (1 - MULT_DRAW_DECAY ** netto) / (1 - MULT_DRAW_DECAY)) + bonus ) # + offset forse

        # caso 2: draw condizionale (es. "if it is a spell", "otherwise move it to your hand")
        match = re.search(r"draw (\d+) if condition", text)
        if match:
            x = int(match.group(1))
            return _add("draw_conditional", 0.5 * DRAW_1 * (1 - MULT_DRAW_DECAY ** x) / (1 - MULT_DRAW_DECAY))

        # caso 3: solo draw X
        match = re.search(r"draw (\d+)", text)
        if match:
            x = int(match.group(1))
            return _add("draw", DRAW_1 * (1 - MULT_DRAW_DECAY ** x) / (1 - MULT_DRAW_DECAY)) # draw 1 = 1.5, draw 2 = 2.85, draw 3 = 4.07
            # pescare 1 o 4 carte cambia molto, pescare 12 o 16 carte è quasi uguale.
            # ogni pescata successiva vale il 90% della precedente

        return _add("draw", 0)

    # ── KEYWORD ─────────────────────────────────────────────────

    def _score_grant_keyword_mult():
        mult = 1.0
        for keyword, base_mult in KEYWORDS_MULT.items():
            if re.search(rf"gain\b.*\b{keyword}\b", text):
                if "until end of turn" in text:
                    base_mult *= 0.75
                mult *= base_mult
        if mult != 1.0:
            _add("grant_keyword_mult", mult)
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

    # ── MOVE   ──────────────────────────────────────────────────

    def _score_move():
        score = 0
    # PER ORA non gestisce casi del tipo: move from my grave, bounce enemy.
    # non dovrebbero esserci carte del genere

        # grave → hand (proprio) — recupero carta
        if re.search(r"move\b.*\bfrom your grave\b.*\bto your hand\b", text):
            score += 1.2
        # grave → field set (proprio) — piazza set card gratis
        elif re.search(r"move\b.*\bfrom your grave\b.*\bto the field set\b", text):
            score += 1.2
        # enemy grave → bottom (avversario) — disturbo graveyard
        elif re.search(r"move\b.*\bfrom their grave\b", text):
            score += 0.5
        else:
            # bounce avversario — rimuove temporaneamente una minaccia dal campo
            if "move target enemy" in text:
                score += BOUNCE_ENEMY
            if "move all target enemy" in text:
                score += BOUNCE_ENEMY * 3.0

            # bounce alleato — può essere costo o vantaggio (rigioca ETB)
            if "move friendly minion" in text:
                score += BOUNCE_ALLY
            if "move all friendly minion" in text:
                score += BOUNCE_ALLY * 3.0

        return _add("move", score)

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
            score += DISCARD_1 * (MULT_DISCARD_BONUS ** x - 1)/(MULT_DISCARD_BONUS - 1)
            return _add("discard_self", score)

        return _add("discard", 0)

    # ── NEGATE ──────────────────────────────────────────────────

    def _score_negate():
        score = 0
        
        # negate semplice — massimo valore
        if "negate target card." in text:
            score = NEGATE_VALUE #parto da counterspell in mgt ma mi sembra broken. forse meglio 2.5?

            match = re.search(r"cost of (\d) or less", text)
            if match:
                x = int(match.group(1))
                score *= (1 - math.exp(-x / 3)) # scala decrescente con il costo della carta negata
            if "equal to" in text:
                score *= 0.5 # situazionale
            return _add("negate", score)

        return _add("negate", 0)

    # ── SACRIFICE ─────────────────────────────────────────────────

    def _score_sacrifice():
        score = 0

        if "sacrifice this" in text:
            stats_score = contributions.get("stats", _score_stats())
            return _add("sacrifice", -abs(stats_score))

        match = re.search(r"sacrifice (\d+) territory card", text)
        if match:
            x = int(match.group(1))
            score += SACRIFICE_TERRITORY * (SAC_TER_BONUS ** x - 1) / (SAC_TER_BONUS - 1)

        return _add("sacrifice", score)
    # ── DESTROY ─────────────────────────────────────────────────

    def _score_destroy():
        score = 0

        def count(pattern):
            return len(re.findall(pattern, text))

        # ── target singolo (usa findall per carte con effetti multipli) ─
        score += count(r"destroy target enemy minion")    *  1.6
        score += count(r"destroy target friendly minion") * -1.0
        score += count(r"destroy target minion(?! or)(?! with)") *  1.8

        score += count(r"destroy target enemy face-down")    *  1.0
        score += count(r"destroy target friendly face-down") * -0.3
        score += count(r"destroy target face-down")          *  1.1

        score += count(r"destroy target minion or face-down") * 1.8

        score += count(r"destroy target enemy card") * 2.5

        # ── all ─────────────────────────────────────────────────
        if "destroy all enemy minions" in text:
            score += 4.5
        elif "destroy all friendly minions" in text:
            score += -2.5
        elif "destroy all minions" in text:
            score += 4.0

        if "destroy all enemy face-down" in text:
            score += 2.2
        elif "destroy all friendly face-down" in text:
            score += -1.0
        elif "destroy all face-down" in text:
            score += 2.0

        return _add("destroy", score)

    # ── DEAL DAMAGE ─────────────────────────────────────────────

    # x | all enemies | all minions | target | player
    # 1 |    1.66     |    1.53     |  0.70  |  0.20
    # 2 |    2.64     |    2.42     |  1.40  |  0.40
    # 3 |    3.33     |    3.05     |  2.10  |  0.60
    # 4 |    3.86     |    3.53     |  2.80  |  0.80
    # 5 |    4.29     |    3.93     |  3.50  |  1.00
    # 6 |    4.65     |    4.26     |  4.20  |  1.20
    # 7 |    4.95     |    4.54     |  4.90  |  1.40
    # 8 |    5.23     |    4.79     |  5.60  |  1.60


    def _score_deal_damage():
        score = 0

        # are dmg - YES player 
        match = re.search(r"deal (\d+) damage to all enemies", text)
        if match:
            x = int(match.group(1))
            score += math.log(1 + x) * (DAMAGE_ALL_ENEMIES_K + DAMAGE_1_PLAYER)
            return _add("deal_damage_all_enemies", score)

        # area dmg - NO player
        match = re.search(r"deal (\d+) damage to all minions", text)
        if match:
            x = int(match.group(1))
            score += math.log(1 + x) * DAMAGE_ALL_MINIONS_K
            return _add("deal_damage_all_minions", score)

        # single target dmg - minion or player
        match = re.search(r"deal (\d+) damage to target minion or player", text)
        if match:
            x = int(match.group(1))
            score += (DAMAGE_1_TARGET + DAMAGE_1_PLAYER) * x
            return _add("deal_damage_minion_or_player", score)

        # single target dmg - enemy only
        match = re.search(r"deal (\d+) damage to target enemy", text)
        if match:
            x = int(match.group(1))
            score += DAMAGE_1_TARGET * x
            return _add("deal_damage_target", score)

        # single target dmg - opponent player only
        match = re.search(r"deal (\d+) damage to target opponent", text)
        if match:
            x = int(match.group(1))
            score += DAMAGE_1_PLAYER * x
            return _add("deal_damage_opponent", score)

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

        # summon territory dal cimitero — simmetrico a sacrifice_territory
        if re.search(r"summon\b.{0,40}\bterritory\b.{0,40}\bgrave\b", text):
            score += abs(SACRIFICE_TERRITORY)

        # summon minion dal cimitero — scala con il cap di costo
        if re.search(r"summon\b.{0,40}\bminion\b.{0,40}\bgrave\b", text):
            match = re.search(r"cost of (\d+) or less", text)
            if match:
                cap = int(match.group(1))
                score += math.log(1 + cap) * 1.4
            else:
                score += 3.0  # nessun cap — qualsiasi minion

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

        if re.search(r"costs\b.*\bless for each\b.*\bgrave\b", text):
            score += 3.5
        elif re.search(r"costs\b.*\bless for each\b.*\bminion\b", text):
            score += 3.0
        else:
            match = re.search(r"costs? (\d+) less(?! for each)", text)
            if match:
                x = int(match.group(1))
                score += x * 0.8

        if "instead of paying" in text:
            score += cost_neutral * 0.5

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
        if re.search(r"reveal\b.*\bsummon\b", text) and "grave" not in text:
            match = re.search(r"cost of (\d+) or less", text)
            if match:
                cap = int(match.group(1))
                return _add("reveal_summon", math.log(1 + cap) * 0.4)
            return _add("reveal_summon", 0.5)
        return _add("reveal_summon", 0)

    def _score_reveal_then_draw():
        # rivela e pesca — valore informazione + carta
        if re.search(r"reveal\b.*\b(move|draw)\b.*\btop\b", text):
            return _add("reveal_draw", 0.3)
        return _add("reveal_draw", 0)

    # ── RAMP ────────────────────────────────────────────────────
    # ogni mana normalizzato a un generico (M)
    def _score_ramp():
        match = re.search(r"gain (\(M\))+", text)
        if match:
            n = len(re.findall(r"\(M\)", match.group(0)))
            return _add("ramp", n * 1.0)
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
            return _add("gain_life", math.log(1 + x) * 0.5)
        return _add("gain_life", 0)

    # ── SAP ─────────────────────────────────────────────────────

    def _score_sap():
        score = 0

        # sap all enemy — molto forte
        if "sap all enemy" in text:
            score += 1.5

        # sap target enemy — rimuove attacco temporaneamente
        if "sap target enemy" in text or "sap target minion" in text:
            score += 0.5

        # sap self — costo o limitazione
        if "sap this" in text:
            score += -0.5

        if "sap target ready friendly" in text:
            score += -0.5

        return _add("sap", score)

    # ── PUMP (+X/+Y) ────────────────────────────────────────────

    def _score_pump():
        score = 0
        permanent = "until the end of" not in text

        # pump positivo — target singolo vs tutta la board
        match = re.search(r"gains? \+(\d+)/\+(\d+)", text)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            base = (x + y) * (0.6 if permanent else 0.3)
            if re.search(r"all (friendly )?minion", text):
                base *= 3.0
            score += base

        # debuff negativo su enemy — speculare al pump
        match = re.search(r"gains? -(\d+)/-(\d+)", text)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            base = (x + y) * (0.6 if permanent else 0.3)
            if re.search(r"all (enemy )?minion", text):
                base *= 3.0
            score += base

        return _add("pump", score)

    # ── SUMMON TOKEN ────────────────────────────────────────────

    TOKEN_COEFFS = {
        "soldier": 1.0,
        "horde":   1.5,
        "ghoul":   2.5,
        "copy":    2.0,
    }

    def _score_summon_token():
        match = re.search(r"summon (\d+) \w+ token", text)
        if not match:
            return _add("summon_token", 0)
        n = int(match.group(1))
        for token_type, coeff in TOKEN_COEFFS.items():
            if token_type in text:
                return _add("summon_token", n * coeff)
        return _add("summon_token", 0)

    # ── TRIGGER BONUS ───────────────────────────────────────────

    def _score_trigger():
        score = 0

        # triggered continuo
        if "when this attacks an enemy minion" in text:
            score += 0.3
        elif "when this attacks" in text:
            score += 0.4

        if "when this damages an opponent" in text:
            score += 0.35

        if "when you summon another minion" in text:
            score += 0.5
        if "when you summon an insector minion" in text:
            score += 0.35
        if "when you play a card" in text:
            score += 0.5
        elif "when you play a spell card" in text:
            score += 0.4
        elif "when you play a minion with a cost of 4 or more" in text:
            score += 0.3

        if "when you discard 1" in text:
            score += 0.3
        if "when you sacrifice 1 territory card" in text:
            score += 0.3

        # triggered condizionale / raro
        if "when this is destroyed" in text:
            score += 0.2
        if "when this is damaged" in text:
            score += 0.2
        if "when this is sapped" in text:
            score += 0.2
        if "when this is discarded" in text:
            score += 0.2
        if "when this is moved from the field" in text:
            score += 0.2
        if "when this leaves the field" in text:
            score += 0.2
        if "when this receives 1 or more damage" in text:
            score += 0.2
        if "when another friendly minion is destroyed" in text:
            score += 0.3
        if "when a territory card is moved to your grave" in text:
            score += 0.25
        if "when 1 or more friendly territories are sacrificed" in text:
            score += 0.25

        return _add("trigger", score)

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
    
    #── Legendary debuff ─────────────────────────────────────────
    def _score_leg_debuff(): #come mult
        rarity = card["rarity"] if not pd.isna(card["rarity"]) else ""
        if "legendary" in rarity.lower():
            return _add("legendary_debuff", 0.8)
        return 1.0

    # ── CONDITION MULT ──────────────────────────────────────────
    def _score_condition_mult():
        # tier 0.9 — quasi sempre vera
        if re.search(r"if (it |this )?was(n't)? played", text):
            return _add("condition_mult", 0.9)
        if re.search(r"if (it|this) wasn't played from your hand", text):
            return _add("condition_mult", 0.9)
        if "if this dealt damage this turn" in text:
            return _add("condition_mult", 0.9)
        if re.search(r"if it was summoned by the effect of", text):
            return _add("condition_mult", 0.9)

        # tier 0.75 — abbastanza comune
        if "if this is the only card in your hand" in text:
            return _add("condition_mult", 0.75)
        if "if you have 2 or less cards in hand" in text:
            return _add("condition_mult", 0.75)
        if "if you have less than 1 card in your grave" in text:
            return _add("condition_mult", 0.75)

        # tier 0.5 — restrittiva
        if "if a territory card was moved to your grave this turn" in text:
            return _add("condition_mult", 0.5)
        if "if you have no cards in your hand" in text:
            return _add("condition_mult", 0.5)
        if "if a card was moved from your field to your hand this turn" in text:
            return _add("condition_mult", 0.5)
        if "if you have 6 or more cards in your hand" in text:
            return _add("condition_mult", 0.5)
        if "if you have no minion cards in your grave" in text:
            return _add("condition_mult", 0.5)
        if "if you summoned no territories during this turn" in text:
            return _add("condition_mult", 0.5)
        if "if you have 5 or more spell cards in your grave" in text:
            return _add("condition_mult", 0.5)
        if "if there are no minions on your field" in text:
            return _add("condition_mult", 0.5)
        if "if you had no cards in your grave when this was played" in text:
            return _add("condition_mult", 0.5)
        if "if you have more than 4 cards in your grave" in text:
            return _add("condition_mult", 0.5)
        if "if you have no cards in your deck" in text:
            return _add("condition_mult", 0.5)

        return 1.0

    # ── SOMMA TOTALE ────────────────────────────────────────────

    base_sum = (
        _score_stats()
        + _spell_card_cost()
        + _score_draw()
        + _score_move()
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
        + _score_summon_token()
        + _score_trigger()
    )

    total = (
        base_sum
        * _score_grant_keyword_mult()
        * _score_keywords_mult()
        * _score_always_sapped_mult()
        * _score_leg_debuff()
        * _score_condition_mult()
    )

    return total / (cost + 1) , contributions # se vuoi valutare carte costose di meno fai ** ALPHA

if __name__ == "__main__":
    # PASS 1
    MEDIAN_COST = df["cost_total"].median()

    df_minions = df[df["type_line"] == "Minion"].copy()

    atk_mean_per_cost = (
        df_minions
        .groupby("cost_total")["atk"]
        .mean()
        .fillna(1.0)
        .to_dict()
    )
    df_minions["ps_temp"] = df_minions.apply(
        lambda c: efficiency(c)[0], axis=1
    )
    P75_MINION = df_minions["ps_temp"].quantile(0.75)
    # END PASS 1

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

    