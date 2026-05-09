## draw_1
Valore stimato: `ln(1+1) = 0.6931`
Ragionamento: `_score_draw` usa `log(1+x)` per draw puro. Con x=1 → ln(2) ≈ 0.6931. Il log cattura il diminishing return: draw 2 vale ln(3) ≈ 1.099, non il doppio di draw 1.

## draw_1 + top_1 (filtraggio)
Valore stimato: `ln(1+1) / sqrt(1+1/2) = 0.6931 / 1.2247 ≈ 0.566`
Ragionamento: `_score_draw` caso 1 usa `log(1+x) / sqrt(1+y/2)` con x=1 draw, y=1 rimesso in cima. Il denominatore penalizza il rimettere carte: stai limitando la selezione, quindi vale meno di un draw puro. La radice quadrata rende la penalità sub-lineare.

## hand_to_top_1
Valore stimato: `0.566 - 0.6931 ≈ -0.127`
Ragionamento: Differenza tra draw+top e draw puro. Rimettere 1 carta in cima è quasi neutro (penalità leggera), non -0.3333 come ipotizzato in precedenza — il denominatore `sqrt(1.5) ≈ 1.22` toglie solo ~18% del valore del draw, non 1/3.

## bounce_enemy_1
Valore stimato: `+0.8`
Ragionamento: `_score_bounce` assegna +0.8 per `"move target enemy ... hand"`. Rimbalzare una creatura avversaria genera tempo: l'avversario deve rigiocarla perdendo mana. Valore fisso, non scala — è già contestuale per natura.

## bounce_friendly_1
Valore stimato: `-0.2`
Ragionamento: `_score_bounce` assegna -0.2 per `"move target minion ... your hand"`. Rimbalzare un alleato è quasi neutro: perdi il minion sul campo questo turno, ma puoi rigiocarli per riattivare ETB. Malus leggero perché è quasi sempre una scelta voluta.

## impulsive
Valore stimato: moltiplicatore `×1.32` sullo score base
Ragionamento: `IMPULSIVE_MULT = 1.32`. Impulsive garantisce che la carta giochi comunque anche senza risorse — è un'affidabilità di attivazione. Il moltiplicatore si applica sull'intera somma base (stats + effetti), non come addendo.

## stealth (minion)
Valore stimato: moltiplicatore `×1.58` sullo score base
Ragionamento: `STEALTH_MULT = 1.58 = log(2)/log(3)`. Stealth garantisce almeno un'attivazione sicura: il minion non può essere attaccato né targettato per un turno. Si applica come moltiplicatore perché potenzia il valore di ogni singola statistica e effetto della carta.

## stealth (spell/non-minion)
Valore stimato: `P75_MINION × 1.58`
Ragionamento: Una spell con stealth non ha stats proprie da moltiplicare, quindi si usa il 75° percentile dei minion come proxy del "valore medio protetto". È un'approssimazione conservativa.

## aggressive
Valore stimato: moltiplicatore `×1.26` sullo score base
Ragionamento: `AGGRESSIVE_MULT = 1.26`. Aggressive permette di attaccare subito — accelera la pressione e rende le stats più liquide. Meno forte di stealth perché non garantisce sopravvivenza, solo iniziativa.

## always_sapped
Valore stimato: moltiplicatore `×0.79` sullo score base
Ragionamento: `ALWAYS_SAPPED_MULT = 0.79 = 1/1.26`. È l'inverso di aggressive: il minion non può mai attaccare. Le sue stats diventano solo difensive, quindi valgono meno. Il reciproco di AGGRESSIVE_MULT è il modo più coerente di modellarlo.

## lifedrain
Valore stimato: moltiplicatore `×1.1` sullo score base
Ragionamento: `LIFEDRAIN_MULT = 1.1`. Recupero vita basso valore — guadagnare vita non incide direttamente sullo stato del campo. Il buff è minimo rispetto ad aggressive/stealth.

## discard_opp_1
Valore stimato: `ln(1+1) × 0.8 = 0.6931 × 0.8 ≈ 0.554`
Ragionamento: `_score_discard` usa `log(1+x) * 0.8` per discard avversario. Rimuovere risorse dalla mano dell'opponente vale come un draw scalato: stessa curva logaritmica, ma 0.8× perché è meno diretto di pescare tu stesso.

## discard_self_1
Valore stimato: `-0.8`
Ragionamento: `_score_discard` usa `-x * 0.8` per discard dalla propria mano. Scartare è voluto — scegli la carta, a volte è un costo per un payoff — quindi il malus è lineare e moderato (non logaritmico).

## discard_self_hand
Valore stimato: `-2.0`
Ragionamento: `_score_discard` assegna -2.0 fisso per `"discard your hand"`. Perdere l'intera mano è un malus pesante e non scalato, perché è quasi sempre una condizione di emergenza o un enorme costo.

## sap_all_enemy
Valore stimato: `+1.2`
Ragionamento: `_score_sap` assegna +1.2. Sappare tutti i minion avversari svuota completamente la loro capacità offensiva per un turno — è quasi una board wipe parziale in termini di impatto immediato.

## sap_target_enemy
Valore stimato: `+0.6`
Ragionamento: `_score_sap` assegna +0.6. Metà del valore di sap all, perché rimuovi l'attacco di un solo minion. È comunque forte perché è removal temporanea senza distruggere.

## sap_self
Valore stimato: `-0.3`
Ragionamento: `_score_sap` assegna -0.3. Sappare sé stesso è quasi sempre un costo o una limitazione — perdi l'attacco del tuo minion questo turno.

## destroy_minion
Valore stimato: `+1.0`
Ragionamento: `_score_destroy` assegna +1.0 per destroy target minion/enemy. È removal permanente — il valore più alto nella categoria singola destroy.

## destroy_all
Valore stimato: `+1.5`
Ragionamento: `_score_destroy` assegna +1.5 per `"destroy all"` (no friendly). Board wipe — valore molto alto ma simmetrico, quindi non +2.0.

## destroy_territory
Valore stimato: `+0.6`
Ragionamento: `_score_destroy` assegna +0.6. Rimuovere una risorsa avversaria permanente (territorio) è buono ma meno urgente di rimuovere un minion.

## destroy_face_down
Valore stimato: `+0.5`
Ragionamento: `_score_destroy` assegna +0.5. Rimuovere set cards è utile ma è removal contestuale — non sai sempre cosa stai rimuovendo.

## destroy_friendly
Valore stimato: `-0.5`
Ragionamento: `_score_destroy` assegna -0.5. Distruggere i propri minion/territori è quasi sempre un costo, non un vantaggio.

## deal_damage_all_X
Valore stimato: `ln(1+X) × 1.2`
Ragionamento: `_score_deal_damage` usa `log(1+x) * 1.2`. AoE ha il moltiplicatore più alto perché colpisce più bersagli con un solo effetto. Es: X=2 → ln(3)*1.2 ≈ 1.317.

## deal_damage_flexible_X
Valore stimato: `ln(1+X) × 1.0`
Ragionamento: `_score_deal_damage` usa `log(1+x) * 1.0` per "minion or player" / "enemy". Flessibilità di bersaglio vale il moltiplicatore pieno.

## deal_damage_minion_X
Valore stimato: `ln(1+X) × 0.8`
Ragionamento: `_score_deal_damage` usa `log(1+x) * 0.8`. Solo minion — meno flessibile, malus 0.8×.

## gain_life_X
Valore stimato: `ln(1+X) × 0.3`
Ragionamento: `_score_gain_life` scala logaritmicamente con coefficiente basso (0.3). Guadagnare 10 vita non è il doppio di 5: dopo un certo punto la vita aggiuntiva ha rendimenti decrescenti forti.

## ramp_1 (gain mana color)
Valore stimato: `1 × 0.7 = 0.7`
Ragionamento: `_score_ramp` conta i simboli mana nel gain e li moltiplica per 0.7. Ogni simbolo di mana colorato guadagnato vale 0.7 — accelerazione risorse è molto forte.

## mill_opp_X
Valore stimato: `ln(1+X) × 0.4`
Ragionamento: `_score_mill` usa `log(1+x) * 0.4` per mill avversario. Vale di più del mill proprio perché rimuove risorse future dell'opponente.

## mill_self_X
Valore stimato: `ln(1+X) × 0.1`
Ragionamento: `_score_mill` usa `log(1+x) * 0.1`. Mill proprio è quasi sempre setup per effetti da cimitero, non removal — quindi coefficiente basso.

## pump_XY
Valore stimato: `(X+Y) × 0.3`
Ragionamento: `_score_pump` somma ATK e DEF del pump e moltiplica per 0.3. Coerente con `_score_stats` che somma atk+def direttamente, ma con uno sconto (il pump è temporaneo e condizionale).

## sacrifice_this
Valore stimato: `-stats` del minion
Ragionamento: `_score_sacrifice` restituisce `-_score_stats()` per `"sacrifice this"`. Il costo è esattamente le stats che stai perdendo — simmetrico con come vengono valutate le stats base.

## sacrifice_territory_X / sacrifice_minion_X
Valore stimato: `-X × 1.4`
Ragionamento: `_score_sacrifice` assegna -1.4 per territorio/minion sacrificato. Vale più delle stats pure (1.4 > 1.0 della stat media) perché perdere un permanente ha impatto sia sul campo che sui turni futuri.

## minion_to_botdeck
Valore stimato: `+0.7`
Ragionamento: `_score_minion_to_botdeck` assegna +0.7. È removal soft — il minion non è distrutto, ma è fuori gioco per molti turni. Tra destroy (+1.0) e bounce (-0.2), tende a destroy per permanenza ma meno per irreversibilità.

## must_attack
Valore stimato: `-0.4`
Ragionamento: `_score_must_attack` assegna -0.4. Perdere la scelta di attacco è una limitazione tattica significativa — a volte attaccare è sbagliato e non puoi evitarlo.

## summon_from_grave (minion, capped X)
Valore stimato: `ln(1+X) × 0.5`
Ragionamento: `_score_summon_from_grave` usa `log(1+cap) * 0.5`. Cap più alto = minion più forti reanimabili. Senza cap → +1.0 fisso (massima flessibilità).

## summon_from_grave (territory)
Valore stimato: `+0.6`
Ragionamento: Recuperare un territorio dal cimitero è ramp/recupero risorse, più sicuro ma meno impattante di un minion.

## scry_X (reveal top X)
Valore stimato: `ln(1+X) × 0.3`
Ragionamento: `_score_scry` usa `log(1+x) * 0.3`. Informazione pura — basso coefficiente perché non cambi materialmente lo stato del gioco, solo lo conosci meglio.

## mana_discount_fixed_N
Valore stimato: `N × 0.3`
Ragionamento: `_score_mana_discount` assegna `x * 0.3` per sconto fisso. Ogni mana risparmiato vale 0.3 — meno di ramp (0.7) perché è una tantum e non genera mana nuovo.

## mana_discount_scale (grave/minion)
Valore stimato: `+0.7` o `+0.8`
Ragionamento: Sconto scalabile con minion amici (+0.7) o cimitero (+0.8). Vale di più di uno sconto fisso perché cresce con il gioco.

## gain_mana_X
Valore stimato: `X × 0.5`
Ragionamento: `_score_gain_mana` usa `x * 0.5`. Mana neutro temporaneo vale meno di ramp colorato (0.7) ma più di uno sconto fisso (0.3) — è immediato e flessibile.

## attach
Valore stimato: `+0.4`
Ragionamento: `_score_attach` assegna +0.4 fisso. Valore contestuale — aggiungere carte a un minion per effetti bonus è utile ma dipende dalla sinergia.

## recycle_X
Valore stimato: `ln(1+X) × 0.2` oppure `+0.2` flat
Ragionamento: `_score_recycle` usa `log(1+x) * 0.2`. Rimettere carte nel mazzo è valore molto basso — non pesca, non genera risorse, solo posticipa l'esaurimento del mazzo.

## spell_card_cost
Valore stimato: `-1.0`
Ragionamento: `_spell_card_cost` assegna -1 per tutte le spell. Giocare una spell consuma una carta dalla mano — card disadvantage implicito che non si vede nelle stats. Ogni effetto di una spell deve guadagnare almeno +1 sopra il suo valore per pareggiare questo costo.
