import os
import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import FancyBboxPatch

from database.load_cards import load_cards
from efficiency import efficiency

FRONTS_DIR = r"C:\Users\gabri\OneDrive\Desktop\Rafflesia\fronts"
OUTPUT_FILE = os.path.join("plots", "tierlist.png")

TIER_COLORS = {
    "S": "#FF7F7F",
    "A": "#FFBF7F",
    "B": "#FFFF7F",
    "C": "#7FBF7F",
    "F": "#7F7FBF",
}

CARD_W = 1.0    # larghezza cella in unità figura
CARD_H = 1.4    # altezza cella
LABEL_W = 0.7   # larghezza colonna tier label
PADDING = 0.08  # padding interno
CARDS_PER_ROW = 12


def assign_tier(score, mu, sigma):
    if score > mu + 2 * sigma:
        return "S"
    if score > mu + sigma:
        return "A"
    if score > mu - sigma:
        return "B"
    if score > mu - 2 * sigma:
        return "C"
    return "F"


def load_png(card_id):
    path = os.path.join(FRONTS_DIR, f"{card_id:03d}.png")
    if os.path.exists(path):
        return mpimg.imread(path)
    return None


def make_tierlist():
    df = load_cards()
    df["cost_total"] = df["cost_neutral"].fillna(0) + df["cost_color"].fillna(0)
    df[["efficiency_score", "contributions"]] = df.apply(
        lambda c: pd.Series(efficiency(c)), axis=1
    )

    mu = df["efficiency_score"].mean()
    sigma = df["efficiency_score"].std()

    df["tier"] = df["efficiency_score"].apply(lambda s: assign_tier(s, mu, sigma))
    df_sorted = df.sort_values("efficiency_score", ascending=False)

    tiers = ["S", "A", "B", "C", "F"]
    tier_groups = {t: df_sorted[df_sorted["tier"] == t] for t in tiers}

    # calcola quante righe servono per ogni tier
    def n_rows(n):
        return max(1, math.ceil(n / CARDS_PER_ROW))

    total_rows = sum(n_rows(len(tier_groups[t])) for t in tiers)
    fig_w = LABEL_W + CARDS_PER_ROW * CARD_W + PADDING * 2
    fig_h = total_rows * CARD_H + PADDING * (len(tiers) + 1)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("#1a1a2e")

    y_cursor = fig_h - PADDING  # partiamo dall'alto

    for tier in tiers:
        cards = tier_groups[tier]
        n = len(cards)
        rows = n_rows(n)
        block_h = rows * CARD_H

        y_cursor -= block_h

        # sfondo tier block
        bg = FancyBboxPatch(
            (PADDING, y_cursor - PADDING * 0.5),
            fig_w - 2 * PADDING,
            block_h + PADDING,
            boxstyle="round,pad=0.02",
            facecolor=TIER_COLORS[tier] + "33",  # 20% alpha via hex
            edgecolor=TIER_COLORS[tier],
            linewidth=1.5,
        )
        ax.add_patch(bg)

        # label tier
        ax.text(
            PADDING + LABEL_W / 2,
            y_cursor + block_h / 2,
            tier,
            ha="center", va="center",
            fontsize=28, fontweight="bold",
            color=TIER_COLORS[tier],
            fontfamily="monospace",
        )

        # PNG carte
        for i, (_, card) in enumerate(cards.iterrows()):
            row_i = i // CARDS_PER_ROW
            col_i = i % CARDS_PER_ROW

            x = PADDING + LABEL_W + col_i * CARD_W
            y = y_cursor + (rows - 1 - row_i) * CARD_H

            img = load_png(int(card["id"]))
            if img is not None:
                ax_img = ax.inset_axes(
                    [x / fig_w, y / fig_h, CARD_W / fig_w, CARD_H / fig_h]
                )
                ax_img.imshow(img)
                ax_img.axis("off")
            else:
                # fallback testo se il PNG manca
                ax.text(
                    x + CARD_W / 2,
                    y + CARD_H / 2,
                    card["name"],
                    ha="center", va="center",
                    fontsize=5, color="white", wrap=True,
                )

        y_cursor -= PADDING

    # titolo e legenda
    mu_str = f"μ={mu:.3f}  σ={sigma:.3f}"
    fig.text(
        0.5, 0.002,
        f"Tier list — {mu_str}  |  S>μ+2σ  A>μ+σ  B>μ-σ  C>μ-2σ  F≤μ-2σ",
        ha="center", color="#aaaaaa", fontsize=8,
    )

    os.makedirs("plots", exist_ok=True)
    plt.tight_layout(pad=0)
    plt.savefig(OUTPUT_FILE, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Salvato: {OUTPUT_FILE}")
    print(f"  mu={mu:.3f}  sigma={sigma:.3f}")
    for t in tiers:
        lo = {"S": mu + 2*sigma, "A": mu + sigma, "B": mu - sigma, "C": mu - 2*sigma, "F": -999}[t]
        hi = {"S": 999, "A": mu + 2*sigma, "B": mu + sigma, "C": mu - sigma, "F": mu - 2*sigma}[t]
        print(f"  {t}: {len(tier_groups[t]):3d} carte  ({lo:.3f}, {hi:.3f}]")


if __name__ == "__main__":
    make_tierlist()
