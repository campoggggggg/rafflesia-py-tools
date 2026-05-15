"""
classifier/classify.py
=======================
Applica il modello addestrato da train.py a tutte le carte e produce:
  - classified_cards.json  — il JSON originale arricchito con il campo "power_class"
  - classification_report.csv — tabella riassuntiva per revisione manuale

USO:
  cd rafflesia-py-tools
  python classifier/classify.py

  # Per specificare un modello diverso:
  python classifier/classify.py --model classifier/model.pkl

  # Per output in path custom:
  python classifier/classify.py --output data/classified_cards.json

  # Per vedere solo le carte "forte" o "debole":
  python classifier/classify.py --filter forte
"""

import sys
import os
import argparse
import pickle
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "efficiency"))
sys.path.insert(0, os.path.join(ROOT, "database"))

import pandas as pd
import numpy as np

from load_cards import load_cards
from features import build_feature_matrix

# ─────────────────────────────────────────────────────────────────────────────
# UTILITÀ
# ─────────────────────────────────────────────────────────────────────────────

LABEL_ICONS = {
    "debole":    "🔴",
    "bilanciata": "🟡",
    "forte":     "🟢",
}

def load_model(path: str):
    """Carica il modello salvato da train.py."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Modello non trovato: {path}\n"
            f"Esegui prima: python classifier/train.py"
        )
    with open(path, "rb") as f:
        payload = pickle.load(f)
    return payload["model"], payload["label_encoder"], payload["thresholds"], payload["feature_names"]


def classify_all(df: pd.DataFrame, rf, le, feature_names: list):
    """
    Applica il modello RF a tutte le carte.
    Restituisce il DataFrame con colonne aggiunte:
      - power_class     : "debole" / "bilanciata" / "forte"
      - power_class_conf: probabilità della classe predetta (0.0 - 1.0)
    """
    X = build_feature_matrix(df)
    probs = rf.predict_proba(X)           # shape (n_carte, 3)
    preds_enc = rf.predict(X)             # shape (n_carte,)
    preds = le.inverse_transform(preds_enc)
    conf = probs.max(axis=1)

    df = df.copy()
    df["power_class"]      = preds
    df["power_class_conf"] = np.round(conf, 3)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(df: pd.DataFrame):
    """Stampa un riassunto della classificazione."""
    print("\n" + "═" * 60)
    print("  RISULTATI CLASSIFICAZIONE")
    print("═" * 60)

    counts = df["power_class"].value_counts()
    total = len(df)
    for label in ["debole", "bilanciata", "forte"]:
        n = counts.get(label, 0)
        pct = n / total * 100
        bar = "█" * int(pct / 2)
        icon = LABEL_ICONS[label]
        print(f"  {icon} {label:12s}  {n:3d} carte  ({pct:.1f}%)  {bar}")

    # Confidenza media per classe
    print("\n  Confidenza media per classe:")
    for label in ["debole", "bilanciata", "forte"]:
        mask = df["power_class"] == label
        if mask.any():
            avg_conf = df.loc[mask, "power_class_conf"].mean()
            print(f"    {LABEL_ICONS[label]} {label:12s}  {avg_conf:.3f}")

    # Carte a bassa confidenza
    low_conf = df[df["power_class_conf"] < 0.55]
    if len(low_conf) > 0:
        print(f"\n  ⚠️  {len(low_conf)} carte con confidenza < 55% (borderline):")
        for _, row in low_conf.sort_values("power_class_conf").iterrows():
            print(f"    {row['name']:<35s}  {LABEL_ICONS[row['power_class']]} {row['power_class']:10s}  conf={row['power_class_conf']:.2f}")


def save_classified_json(df: pd.DataFrame, original_json_path: str, output_path: str):
    """
    Legge il JSON originale delle carte e aggiunge i campi
    'power_class' e 'power_class_conf' a ogni carta.
    """
    with open(original_json_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    # Costruisce un lookup id -> classificazione
    lookup = {}
    for _, row in df.iterrows():
        card_id = row.get("id")
        if card_id is not None:
            lookup[int(card_id)] = {
                "power_class":      row["power_class"],
                "power_class_conf": float(row["power_class_conf"]),
            }

    # Arricchisce ogni carta
    enriched = []
    for card in cards:
        card_id = card.get("id")
        if card_id in lookup:
            card["power_class"]      = lookup[card_id]["power_class"]
            card["power_class_conf"] = lookup[card_id]["power_class_conf"]
        else:
            # Carte non classificate (es. escluse per tipo)
            card["power_class"]      = None
            card["power_class_conf"] = None
        enriched.append(card)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"\n  [OK] JSON classificato salvato in: {output_path}")


def save_csv_report(df: pd.DataFrame, output_path: str):
    """
    Salva una tabella CSV leggibile per revisione manuale.
    Colonne: id, name, type_line, color, cost, atk, def, power_class, conf
    """
    cols = ["id", "name", "type_line", "color", "cost_neutral", "cost_color",
            "atk", "def", "power_class", "power_class_conf"]
    available = [c for c in cols if c in df.columns]
    report = df[available].copy()
    report = report.sort_values(["power_class", "power_class_conf"], ascending=[True, True])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    report.to_csv(output_path, index=False, encoding="utf-8")
    print(f"  [OK] Report CSV salvato in: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Classifica le carte Rafflesia con la RF addestrata")
    parser.add_argument("--model",  type=str,
                        default=os.path.join(os.path.dirname(__file__), "model.pkl"),
                        help="Path al modello .pkl (default: classifier/model.pkl)")
    parser.add_argument("--output", type=str,
                        default=os.path.join(ROOT, "data", "classified_cards.json"),
                        help="Path output JSON (default: data/classified_cards.json)")
    parser.add_argument("--cards",  type=str,
                        default=os.path.join(ROOT, "data", "rafflesia-cards.json"),
                        help="Path al JSON originale delle carte")
    parser.add_argument("--filter", type=str, default=None,
                        choices=["debole", "bilanciata", "forte"],
                        help="Mostra solo le carte di questa classe")
    parser.add_argument("--no-csv", action="store_true",
                        help="Non salvare il report CSV")
    parser.add_argument("--exclude-types", nargs="+", default=["Territory", "Token"],
                        help="Tipi di carta da escludere dal plot (default: Territory Token)")
    args = parser.parse_args()

    # ── Carica modello ────────────────────────────────────────────
    print("Caricamento modello...")
    rf, le, thresholds, feature_names = load_model(args.model)
    print(f"  Modello: {rf.n_estimators} alberi")
    print(f"  Soglie training: debole < {thresholds['low']:.4f} ≤ bilanciata ≤ {thresholds['high']:.4f} < forte")

    # ── Carica carte ──────────────────────────────────────────────
    print("\nCaricamento carte...")
    df = load_cards()
    if args.exclude_types:
        before = len(df)
        df = df[~df["type_line"].isin(args.exclude_types)].copy()
        print(f"  Esclusi tipi {args.exclude_types}: rimaste {len(df)} carte (rimosse {before - len(df)})")
    else:
        print(f"  {len(df)} carte caricate.")

    # ── Classifica ────────────────────────────────────────────────
    print("\nClassificazione in corso...")
    df_classified = classify_all(df, rf, le, feature_names)

    # ── Stampa risultati ──────────────────────────────────────────
    print_summary(df_classified)

    # ── Filtro opzionale per stampa ───────────────────────────────
    if args.filter:
        filtered = df_classified[df_classified["power_class"] == args.filter]
        print(f"\n  Carte classificate come '{args.filter}' ({len(filtered)}):")
        for _, row in filtered.sort_values("power_class_conf", ascending=False).iterrows():
            print(f"    {LABEL_ICONS[args.filter]} {row['name']:<35s}  conf={row['power_class_conf']:.2f}")

    # ── Salva JSON ────────────────────────────────────────────────
    # Cerca il JSON originale in path comuni
    json_candidates = [
        args.cards,
        os.path.join(ROOT, "data", "rafflesia-cards.json"),
        os.path.join(ROOT, "rafflesia-cards.json"),
    ]
    original_json = None
    for candidate in json_candidates:
        if os.path.exists(candidate):
            original_json = candidate
            break

    if original_json:
        save_classified_json(df_classified, original_json, args.output)
    else:
        # Fallback: salva solo il DataFrame come JSON semplice
        print(f"\n  [WARN] JSON originale non trovato. Salvo formato semplificato.")
        cols = ["id", "name", "type_line", "power_class", "power_class_conf"]
        available = [c for c in cols if c in df_classified.columns]
        df_classified[available].to_json(args.output, orient="records",
                                          force_ascii=False, indent=2)
        print(f"  [OK] Salvato in: {args.output}")

    # ── Salva CSV ─────────────────────────────────────────────────
    if not args.no_csv:
        csv_path = args.output.replace(".json", "_report.csv")
        save_csv_report(df_classified, csv_path)

    print("\n" + "═" * 60)
    print("  CLASSIFICAZIONE COMPLETATA")
    print(f"  Output: {args.output}")
    print("═" * 60)


if __name__ == "__main__":
    main()