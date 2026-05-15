"""
classifier/plot_classified.py
==============================
Genera un PNG per ogni colore con le immagini delle carte (da fronts/)
disposte in tre sezioni: forte | bilanciata | debole.
4 carte per riga all'interno di ogni sezione.

USO:
  cd rafflesia-py-tools
  python classifier/plot_classified.py
"""

import os
import argparse
import math

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

FRONTS_DIR = r"C:\Users\gabri\OneDrive\Desktop\Rafflesia\fronts"

COLOR_BG = {
    "black":     "#0d0d1a",
    "blue":      "#0a0f20",
    "green":     "#0a1a0a",
    "red":       "#1a0a0a",
    "colorless": "#141414",
}
COLOR_ACCENT = {
    "black":     "#8b5cf6",
    "blue":      "#3b82f6",
    "green":     "#22c55e",
    "red":       "#ef4444",
    "colorless": "#94a3b8",
}
CLASS_COLOR = {
    "forte":      "#fbbf24",
    "bilanciata": "#60a5fa",
    "debole":     "#f87171",
}
CLASS_LABEL = {
    "forte":      "FORTE",
    "bilanciata": "BILANCIATA",
    "debole":     "DEBOLE",
}
COLUMN_ORDER = ["forte", "bilanciata", "debole"]

COLS_PER_CLASS = 4   # card images per row within each class section
CARD_W_IN = 1.4      # inches per card
CARD_H_IN = 1.95
H_GAP     = 0.06     # gap between cards (inches)
V_GAP     = 0.08
SEP_GAP   = 0.45     # gap between the 3 sections
MARGIN    = 0.25
HDR_H     = 0.55     # header height per section (title row)
TITLE_H   = 0.50     # top title bar


def card_image_path(card_id):
    return os.path.join(FRONTS_DIR, f"{int(card_id):03d}.png")


def plot_color(df_color: pd.DataFrame, color_name: str, out_path: str):
    sections = {cls: df_color[df_color["power_class"] == cls].reset_index(drop=True)
                for cls in COLUMN_ORDER}

    def n_rows(cards):
        return max(1, math.ceil(len(cards) / COLS_PER_CLASS)) if len(cards) > 0 else 0

    section_rows = {cls: n_rows(sections[cls]) for cls in COLUMN_ORDER}
    max_rows = max(section_rows.values(), default=0)

    sec_w = COLS_PER_CLASS * CARD_W_IN + (COLS_PER_CLASS - 1) * H_GAP
    fig_w = MARGIN * 2 + 3 * sec_w + 2 * SEP_GAP
    fig_h = MARGIN + TITLE_H + HDR_H + max_rows * (CARD_H_IN + V_GAP) + MARGIN

    fig = plt.figure(figsize=(fig_w, fig_h), facecolor=COLOR_BG.get(color_name, "#111"))

    bg = COLOR_BG.get(color_name, "#111")
    accent = COLOR_ACCENT.get(color_name, "#aaa")

    # Title text via figure text
    fig.text(0.5, 1 - (MARGIN + TITLE_H * 0.5) / fig_h,
             color_name.upper(),
             fontsize=22, fontweight="bold", color=accent,
             ha="center", va="center", fontfamily="monospace")

    for ci, cls in enumerate(COLUMN_ORDER):
        cards = sections[cls]
        cls_color = CLASS_COLOR[cls]

        sec_x0 = MARGIN + ci * (sec_w + SEP_GAP)  # inches from left
        sec_y0_cards = MARGIN  # inches from bottom, where cards start

        # Section header via figure text (convert to figure fraction)
        hdr_y_in = MARGIN + max_rows * (CARD_H_IN + V_GAP) + HDR_H * 0.55
        fig.text(
            (sec_x0 + sec_w / 2) / fig_w,
            hdr_y_in / fig_h,
            f"{CLASS_LABEL[cls]}  ({len(cards)})",
            fontsize=11, fontweight="bold", color=cls_color,
            ha="center", va="center", fontfamily="monospace",
        )

        # Underline via a thin axes spanning section width
        line_y_in = MARGIN + max_rows * (CARD_H_IN + V_GAP) + HDR_H * 0.25
        ax_line = fig.add_axes([
            sec_x0 / fig_w,
            line_y_in / fig_h,
            sec_w / fig_w,
            0.002,
        ])
        ax_line.set_facecolor(cls_color)
        ax_line.axis("off")

        for idx, (_, card) in enumerate(cards.iterrows()):
            row = idx // COLS_PER_CLASS
            col = idx % COLS_PER_CLASS

            # Bottom-left of this card in inches
            x_in = sec_x0 + col * (CARD_W_IN + H_GAP)
            # rows go top-to-bottom: row 0 is at the top
            y_in = MARGIN + (max_rows - row - 1) * (CARD_H_IN + V_GAP)

            # Convert to figure fractions
            left   = x_in / fig_w
            bottom = y_in / fig_h
            width  = CARD_W_IN / fig_w
            height = CARD_H_IN / fig_h

            ax_card = fig.add_axes([left, bottom, width, height])

            img_path = card_image_path(card["id"])
            if os.path.exists(img_path):
                img = mpimg.imread(img_path)
                ax_card.imshow(img, aspect="auto")
            else:
                ax_card.set_facecolor("#222233")
                ax_card.text(0.5, 0.5, f"#{int(card['id'])}",
                             transform=ax_card.transAxes,
                             color="#555", ha="center", va="center", fontsize=8)

            # Coloured border
            for spine in ax_card.spines.values():
                spine.set_edgecolor(cls_color)
                spine.set_linewidth(2.0)
            ax_card.set_xticks([])
            ax_card.set_yticks([])

    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=COLOR_BG.get(color_name, "#111"))
    plt.close(fig)
    print(f"  Salvato: {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  default="data/classified_cards_report.csv")
    parser.add_argument("--outdir", default="plots")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    os.makedirs(args.outdir, exist_ok=True)

    colors = sorted(df["color"].dropna().unique())
    print(f"{len(df)} carte, {len(colors)} colori: {colors}")

    for color in colors:
        subset = df[df["color"] == color].copy()
        out_path = os.path.join(args.outdir, f"cards_{color}.png")
        print(f"\n[{color}]  {len(subset)} carte")
        plot_color(subset, color, out_path)

    print("\nFatto.")


if __name__ == "__main__":
    main()
