import re


def normalize_text(raw: str) -> str:
    t = raw.lower().strip()

    # punteggiatura e varianti grafiche
    t = t.replace("\r\n", " ").replace("\n", " ")
    t = t.replace("-", " ")
    t = t.replace('"', "")
    t = t.replace("\u201c", "").replace("\u201d", "")
    t = re.sub(r"\s+", " ", t)

    #--DESTROY--------------------------------------------
    # destroy target minion 
    # destroy target enemy minion 
    # destroy target friendly minion

    # destroy target face-down 
    # destroy target enemy face-down 
    # destroy all friendly face-down
     
    # destroy all minions

    #destroy target enemy card (fa anche territory)


    t = t.replace("destroy all other minions", "destroy all minions")

    t = re.sub(r"destroy up to (\d+) set card", lambda m: 
               ("destroy target face-down " * int(m.group(1))).strip(), t) # up to x set card
    t = re.sub(r"destroy up to (\d+) target minion and/or set card", lambda m: 
               ("destroy target face-down " * int(m.group(1))).strip(), t) # up to x set and/or minion
    t = re.sub(r"destroy up to (\d+) target minion", lambda m: 
               ("destroy target face-down " * int(m.group(1))).strip(), t) # up to x  minion
    
    t = t.replace("move all minions to the bottom", "destroy all minions")
    t = t.replace("move target enemy minion to the bottom", "destroy target enemy minion")

    t = t.replace("sacrifice a minion", "destroy target friendly minion")
    t = t.replace("sacrifice 1 minion", "destroy target friendly minion")
    t = re.sub(r"sacrifice (\d+) other", lambda m: 
               ("destroy target friendly minion" * int(m.group(1))).strip(), t)
    # ----------------------------------------------------------

    # BOUNCE ------ VANNO POI AGGIUNTE "to hand" NELLE _score_*
    # move friendly minion
    # move target enemy
    t = t.replace("return that summoned", "move friendly minion")
    t = t.replace("return those summoned", "move all friendly minion")
    t = t.replace("move this and that attacked minion to the hand", "move friendly minion, move target enemy") # mole
    t = t.replace("move target minion from your field", "move friendly minion")
    t = t.replace("move all other minions from the field to the hand", "move all friendly minion, move all target enemy") # rau

    # sinonimi draw
    t = t.replace("move it to your hand", "draw 1")
    t = t.replace("draw X", "draw 2") #placeholder per dare un valore fittizio a draw X

    # DISCARD
    t = t.replace("discard a minion card", "discard 1")
    t = t.replace("discard 1 minion card", "discard 1")
    t = t.replace("discard a card", "discard 1")

    # SACRIFICE TERRITORY

    t = t.replace("sacrifice a territory", "sacrifice 1 territory card")
    t = re.sub(r"sacrifice (\d+) territory\b(?! card)", r"sacrifice \1 territory card", t)
    t = re.sub(r"sacrifice (\d+) territories\b", r"sacrifice \1 territory card", t)  # mantieni il numero
    t = t.replace("wilderness territory card", "territory card")
    t = t.replace("wilderness territories", "territory card")
    t = t.replace("wilderness territory", "territory card")

    # lifedrain normalizzato (il trattino è già rimosso sopra, ma per sicurezza)
    t = t.replace("life drain", "lifedrain")

    # ── DEAL DAMAGE ─────────────────────────────────────────────
    # "target opponent" come bersaglio → "target player"
    t = re.sub(r"deal (\d+) damage to target player", r"deal \1 damage to target opponent", t)
    # "to a randomly chosen enemy" → tratta come "target enemy" per lo scoring
    t = re.sub(r"deal (\d+) damage to a randomly chosen enemy", r"deal \1 damage to target enemy", t)
    t = t.replace("deal X damage", "deal 3 damage") # placeholder, da pensarci

    # ── SUMMON FROM GRAVE ────────────────────────────────────────
    t = re.sub(
        r"summon a minion with a cost of (\d+) from your grave",
        r"summon target minion from your grave",
        t
    )
    # "summon all minions from your grave" → già canonico
    # "summon up to 1 territory card from your grave" → già canonico

    # ── MANA DISCOUNT (costo carta) ──────────────────────────────
    t = re.sub(r"this costs \(n\)\(n\) less", "this costs 2 less", t)
    t = re.sub(r"this costs \(n\) less", "this costs 1 less", t)
    t = re.sub(r"costs \(n\)less", "costs 1 less", t)   # Otherworldly Slash: no spazio

    # ── RAMP ────────────────────────────────────────────────────
    # "gain (G)", "gain (B)" normalizzati a un mana generico (M)
    t = t.replace("(G)", "(M)")
    t = t.replace("(R)", "(M)")
    t = t.replace("(U)", "(M)")
    t = t.replace("(B)", "(M)")

    # ── GAIN STATS ──────────────────────────────────────────────
    # "gain +X/+Y" senza "s" → "gains +X/+Y"
    t = re.sub(r"(?<!\w)gain \+(\d+)/\+(\d+)", r"gains +\1/+\2", t)
    t = re.sub(r"(?<!\w)gain \+(\d+)/\+0",     r"gains +\1/+0",  t)
    t = re.sub(r"(?<!\w)gain \+0/\+(\d+)",     r"gains +0/+\1",  t)
    t = re.sub(r"(?<!\w)gain \+x/\+x",         r"gains +x/+x",   t)
    t = re.sub(r"(?<!\w)gain \+x/\+0",         r"gains +x/+0",   t)

    return t
