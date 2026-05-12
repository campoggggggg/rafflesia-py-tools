# design da aggiustare
- dare stealth a haunting woods per allinearlo al resto del set invece di indistruttibile
- giant cocoon ha stealth e basta, bear totem ha aggressive scritto tra ""
- la keyword è lifedrain o life-drain?
- mysterious shade e relenteless hunter sono due carte simili. ma secondo me bilanciate male l'un l'altra
- submit to will e cruel ritual mettere il punto dopo "negate target card" per facilitare il conto con pytools
- laios rotten king ha una s di troppo in minions
- scegliere tra: set card | face-down card
- Otherworldly Slash: no spazio dopo il mana
- see red: da scrivere - gain (R)(R)(R)
- otherwordly slash e rot away stesso effetto con stessa meccanica (sconto mana)
- gnome dice "target player", altre carte "target opponent"; penso siano uguali. poi enemy si riferisce solo ai minion e "minion or player" è entrambi.

# modifiche da controllare
- controlla disflora e realm walker, prendono bonus che non dovrebbero

---

## stats (minion)
Valore stimato: `copysign(exp(|delta| × 0.3) - 1, delta) × balance^0.5`
Ragionamento: Le stat vengono valutate come scostamento dal vanilla (`cost × 2`). Delta positivo = sopra vanilla, negativo = sotto. La curva è esponenziale: vicino al vanilla cambia poco, alle code cresce/cala rapidamente. Il fattore `balance^0.5` penalizza minion molto sbilanciati (es. 0/6 o 6/0).
- 1/1 costo 1 → delta=0, stats=0
- 3/3 costo 1 → delta=+4, stats≈+2.32
- 2/2 costo 3 → delta=-2, stats≈-0.82
- 5/5 costo 5 → delta=0, stats=0
- 8/8 costo 5 → delta=+6, stats≈+5.05
- 10/10 costo 5 → delta=+10, stats≈+19.1

`STATS_DELTA_K = 0.3`

## draw
Valore stimato: `DRAW_1 × (1 - 0.9^x) / (1 - 0.9)`
Ragionamento: Draw scala con decay geometrico — ogni carta pescata vale il 90% della precedente. `DRAW_1 = 1.5`.
- draw 1 → 1.5
- draw 2 → 2.85
- draw 3 → 4.07

`DRAW_1 = 1.5`, `MULT_DRAW_DECAY = 0.9`

## draw_condizionale
Valore stimato: `0.5 × draw_score`
Ragionamento: Draw condizionale su tipo carta (es. "if it is a spell, move it to your hand") vale metà del draw puro — la condizione non è sempre soddisfatta.

## draw + topdeck
Valore stimato: `draw_netto + log(1+y) × x/(x+y)`
Ragionamento: Caso "draw X, move Y to top" — il netto è draw puro sul delta, con un bonus per il filtraggio (rimettere in cima significa aver visto più carte).

## bounce_enemy
Valore stimato: `+1.0`
Ragionamento: `BOUNCE_ENEMY = 1.0`. Rimbalzare una creatura avversaria genera tempo — l'avversario deve rigiocarla perdendo mana.

## bounce_ally
Valore stimato: `-0.2`
Ragionamento: `BOUNCE_ALLY = -0.2`. Rimbalzare un alleato è quasi neutro: perdi il minion sul campo ma puoi riattivare ETB. Malus leggero perché è quasi sempre una scelta voluta.

## bounce_all (×3.0)
Valore stimato: `BOUNCE_ENEMY × 3.0` o `BOUNCE_ALLY × 3.0`
Ragionamento: Stimato ~3 creature medie in campo a midgame.

## move_grave_to_hand
Valore stimato: `+1.2`
Ragionamento: Recuperare una carta dal proprio cimitero in mano — come un draw ma da un pool ridotto (il graveyard). Valore fisso.

## move_grave_to_field_set
Valore stimato: `+1.2`
Ragionamento: Piazzare una set card dal cimitero direttamente in campo — stesso valore di grave→hand, risparmia anche il costo di giocarla set.

## move_enemy_grave
Valore stimato: `+0.5`
Ragionamento: Spostare una carta dal cimitero avversario al fondo del mazzo — disturbo graveyard, impedisce recuperi futuri.

## discard_opp (bound by darkness)
Valore stimato: `+3.5`
Ragionamento: Caso specifico: rivela mano avversaria, banish 1 carta a scelta. Valore alto per la combinazione scelta + banish + informazione.

## discard_self_hand
Valore stimato: `-3.5`
Ragionamento: `DISCARD_ALL = -3.5`. Perdere l'intera mano è un malus pesante.

## discard_self_X
Valore stimato: `DISCARD_1 × (1.05^x - 1) / 0.05`
Ragionamento: `DISCARD_1 = -1.5`. Scartare scala con leggero bonus composto — scartare 2 vale leggermente più del doppio di scartare 1.

## negate
Valore stimato: `3.5 × (1 - exp(-costo/3))` se con cap di costo, `×0.5` se situazionale
Ragionamento: `NEGATE_VALUE = 3.5`. Controstrega pura vale 3.5. Con cap di costo scala decrescente: negare carte care è più forte. Con condizione "equal to" dimezza il valore.

## sacrifice_this
Valore stimato: `-abs(stats)`
Ragionamento: Sacrificare se stesso è un malus proporzionale al valore assoluto delle stats perdute. Il `abs` evita che carte sotto vanilla generino un valore positivo.

## sacrifice_territory_X
Valore stimato: `SACRIFICE_TERRITORY × (1.05^x - 1) / 0.05`
Ragionamento: `SACRIFICE_TERRITORY = -2.5`. Perdere un territorio è perdere sia la carta che la risorsa. Scala con leggero composto.

## destroy_friendly
Valore stimato: `-1.0`

## destroy_all_friendly
Valore stimato: `-2.5`

## destroy_face_down
Valore stimato: `+1.0`

## destroy_face_down_flexible
Valore stimato: `+1.1`

## destroy_enemy_card (territory)
Valore stimato: `+2.5`

## destroy_enemy_minion
Valore stimato: `+1.6`

## destroy_minion (flexible)
Valore stimato: `+1.8`

## destroy_all
Valore stimato: `+4.5`
Ragionamento: Board wipe — valore molto alto ma simmetrico.

## deal_damage_all_enemies_X
Valore stimato: `log(1+x) × 2.4`
Ragionamento: `DAMAGE_ALL_ENEMIES_K = 2.4`. AoE su tutti i nemici incluso il giocatore.

## deal_damage_all_minions_X
Valore stimato: `log(1+x) × 2.2`
Ragionamento: `DAMAGE_ALL_MINIONS_K = 2.2`. AoE simmetrico solo minion.

## deal_damage_minion_or_player_X
Valore stimato: `(DAMAGE_1_TARGET + DAMAGE_1_PLAYER) × x = 0.9 × x`
Ragionamento: Target flessibile minion o giocatore — somma dei due coefficienti.

## deal_damage_target_enemy_X
Valore stimato: `DAMAGE_1_TARGET × x = 0.7 × x`
Ragionamento: `DAMAGE_1_TARGET = 0.7`. Danno singolo a minion.

## deal_damage_opponent_X
Valore stimato: `DAMAGE_1_PLAYER × x = 0.2 × x`
Ragionamento: `DAMAGE_1_PLAYER = 0.2`. Danno diretto al giocatore — basso valore.

## must_attack
Valore stimato: `-0.3`
Ragionamento: Perdere la scelta di attacco è una limitazione tattica.

## summon_from_grave_minion (con cap X)
Valore stimato: `log(1+cap) × 1.4`
Ragionamento: Cap più alto = minion più forti reanimabili. Senza cap → `+3.0`.

## summon_from_grave_territory
Valore stimato: `+2.5`
Ragionamento: Simmetrico a `SACRIFICE_TERRITORY` in positivo — recuperare un territorio equivale a non averlo perso.

## mana_discount_grave (scalabile)
Valore stimato: `+3.5`
Ragionamento: Sconto che cresce con le carte al cimitero — scala in lategame, valore alto.

## mana_discount_minion (scalabile)
Valore stimato: `+3.0`
Ragionamento: Sconto che cresce con i minion amici — scala con la board.

## mana_discount_fixed_N
Valore stimato: `N × 0.8`
Ragionamento: Ogni mana risparmiato fisso vale 0.8.

## mana_discount_instead_of_paying
Valore stimato: `cost_neutral × 0.5`
Ragionamento: Costo alternativo (sacrifica invece di pagare) — vale metà del costo neutro evitato.

## scry_X (reveal top X)
Valore stimato: `log(1+x) × 0.3`
Ragionamento: Informazione pura — basso coefficiente.

## reveal_then_summon (con cap X)
Valore stimato: `log(1+cap) × 0.4`
Ragionamento: Rivela e evoca — valore dipende dal cap. Senza cap → `+0.5`.

## reveal_then_draw
Valore stimato: `+0.3`
Ragionamento: Rivela e pesca — valore informazione + carta, fisso basso.

## ramp_N (gain mana color)
Valore stimato: `N × 1.0`
Ragionamento: Ogni simbolo di mana colorato guadagnato vale 1.0.

## recycle_X
Valore stimato: `log(1+x) × 0.2` oppure `+0.2` flat
Ragionamento: Rimettere carte nel mazzo — valore molto basso, non pesca né genera risorse.

## gain_life_X
Valore stimato: `log(1+x) × 0.5`
Ragionamento: Scala logaritmicamente — guadagnare 10 vita non è il doppio di 5.

## sap_all_enemy
Valore stimato: `+1.5`

## sap_target_enemy / sap_target_minion
Valore stimato: `+0.5`

## sap_self / sap_target_ready_friendly
Valore stimato: `-0.5`

## pump +X/+Y (permanente, singolo)
Valore stimato: `(x+y) × 0.6`
Ragionamento: Permanente vale il doppio del temporaneo.

## pump +X/+Y (temporaneo, singolo)
Valore stimato: `(x+y) × 0.3`

## pump +X/+Y (all minions ×3.0)
Valore stimato: `base × 3.0`
Ragionamento: ~3 creature medie in campo a midgame.

## mill_opp_X
Valore stimato: `log(1+x) × 0.4`

## mill_self_X
Valore stimato: `log(1+x) × 0.1`

## spell_card_cost
Valore stimato: `0.0`
Ragionamento: `SPELL_CARD_VALUE = -0.0`. Attualmente non applicato — le spell non ricevono penalità esplicita per il card disadvantage implicito.

## legendary_debuff
Valore stimato: moltiplicatore `×0.8`
Ragionamento: Le carte leggendarie sono limitate a 1 copia per mazzo — minore consistenza, quindi malus sul valore complessivo.

## condition_mult
Valore stimato: moltiplicatore `×0.9 / ×0.75 / ×0.5`
Ragionamento: Tre tier di restrittività delle condizioni:
- `×0.9` — quasi sempre vera (es. "if it was played", "if this dealt damage this turn")
- `×0.75` — abbastanza comune (es. "if you have 2 or less cards in hand", "if this is the only card in your hand")
- `×0.5` — restrittiva (es. "if a territory card was moved to your grave this turn", "if you have 6 or more cards in your hand")

## keyword_mult
- `stealth`: `×1.33`
- `aggressive`: `×1.20`
- `protector`: `×1.20`
- `lifedrain`: `×1.10`
- `impulsive`: `×1.22`
- `always_sapped`: `×0.80`

## grant_keyword_mult
Valore stimato: stesso moltiplicatore della keyword, `×0.75` se "until end of turn"
Ragionamento: Dare una keyword a un alleato vale come averla — se temporanea vale il 75%.
