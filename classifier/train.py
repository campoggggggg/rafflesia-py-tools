"""
classifier/train.py
====================
Addestra una Random Forest per classificare le carte Rafflesia in:
  - "debole"
  - "bilanciata"
  - "forte"

Training set (ground truth affidabile):
  1. Tutte le carte ROSSE  — power_score calibrato correttamente
  2. Carte di altri colori con power_score noto come corretto (TRUSTED_CARDS)
  3. Override manuali in labels-override.json

Le carte non incluse nel training set vengono classificate da classify.py.

USO:
  python classifier/train.py
  python classifier/train.py --show-thresholds
  python classifier/train.py --low 1.2 --high 2.8
"""

import sys
import os
import argparse
import pickle
import json
import warnings
warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "efficiency"))
sys.path.insert(0, os.path.join(ROOT, "database"))

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

from load_cards import load_cards
from features import build_feature_matrix, FEATURE_NAMES

# ─────────────────────────────────────────────────────────────────────────────
# 1. POWER SCORE
# ─────────────────────────────────────────────────────────────────────────────

try:
    from efficiency.core import efficiency as power_score
    POWER_SCORE_AVAILABLE = True
    print("[OK] power_score importato da efficiency/")
except ImportError as e:
    POWER_SCORE_AVAILABLE = False
    print(f"[WARN] power_score non trovato: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. CARTE CON POWER SCORE NOTO COME CORRETTO (oltre alle rosse)
# ─────────────────────────────────────────────────────────────────────────────

TRUSTED_CARDS = {
    "Bound by Darkness",
    "Brain Fog",
    "Invasive Architect",
    "Fried, Lightning Blade",
    "Lightning Bolt in a Bottle",
    "Endless Research",
    "Awaken the Elders",
    "Aimless One",
}

LABEL_MAP = {0: "debole", 1: "bilanciata", 2: "forte"}
LABEL_COLORS = {"debole": "🔴", "bilanciata": "🟡", "forte": "🟢"}


# ─────────────────────────────────────────────────────────────────────────────
# 3. LABELING
# ─────────────────────────────────────────────────────────────────────────────

def compute_power_scores(df: pd.DataFrame) -> pd.Series:
    if POWER_SCORE_AVAILABLE:
        return df.apply(lambda card: power_score(card)[0], axis=1)
    raise RuntimeError("power_score non disponibile — necessario per il training")


def assign_labels(scores: pd.Series, low: float = None, high: float = None):
    """Assegna etichette da percentili P33/P67 calcolati solo sulle carte rosse."""
    if low is None:
        low = scores.quantile(0.33)
    if high is None:
        high = scores.quantile(0.67)

    labels = pd.cut(
        scores,
        bins=[-np.inf, low, high, np.inf],
        labels=["debole", "bilanciata", "forte"]
    )
    return labels, low, high


def show_label_distribution(labels: pd.Series, scores: pd.Series, df: pd.DataFrame):
    print("\n" + "═" * 60)
    print("  DISTRIBUZIONE ETICHETTE (training set)")
    print("═" * 60)
    counts = labels.value_counts()
    for label in ["debole", "bilanciata", "forte"]:
        n = counts.get(label, 0)
        pct = n / len(labels) * 100
        bar = "█" * int(pct / 2)
        print(f"  {LABEL_COLORS[label]} {label:12s}  {n:3d} carte  ({pct:.1f}%)  {bar}")

    print("\n  Esempi per classe (5 per classe, ordinati per score):")
    for label in ["debole", "bilanciata", "forte"]:
        mask = labels == label
        sample = df[mask].copy()
        sample["_score"] = scores[mask]
        sample = sample.sort_values("_score", ascending=(label == "debole")).head(5)
        print(f"\n  {LABEL_COLORS[label]} {label.upper()}")
        for _, row in sample.iterrows():
            s = scores[row.name]
            trusted = " [trusted]" if row["name"] in TRUSTED_CARDS else ""
            override = " [override]" if row.get("_overridden") else ""
            print(f"    {row['name']:<40s}  score={s:.3f}{trusted}{override}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. TRAINING
# ─────────────────────────────────────────────────────────────────────────────

def train_classifier(X: pd.DataFrame, y: pd.Series, n_estimators: int = 300):
    le = LabelEncoder()
    le.fit(["debole", "bilanciata", "forte"])
    y_enc = le.transform(y)

    rf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=None,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(rf, X, y_enc, cv=cv, scoring="f1_macro")

    print("\n" + "═" * 60)
    print("  CROSS-VALIDATION (5-fold, F1 macro)")
    print("═" * 60)
    for i, s in enumerate(cv_scores):
        bar = "█" * int(s * 20)
        print(f"  Fold {i+1}:  {s:.4f}  {bar}")
    print(f"  Media:   {cv_scores.mean():.4f}  ±  {cv_scores.std():.4f}")

    rf.fit(X, y_enc)
    return rf, le, cv_scores


# ─────────────────────────────────────────────────────────────────────────────
# 5. REPORT
# ─────────────────────────────────────────────────────────────────────────────

def print_report(rf, le, X, y_enc, df, scores):
    y_pred = rf.predict(X)

    print("\n" + "═" * 60)
    print("  CLASSIFICATION REPORT (training set)")
    print("  [NB: ottimistico — la CV sopra è la stima reale]")
    print("═" * 60)
    print(classification_report(y_enc, y_pred, target_names=le.classes_))

    print("\n  CONFUSION MATRIX  (righe=reale, colonne=predetto)")
    cm = confusion_matrix(y_enc, y_pred)
    header = "       " + "  ".join(f"{c:10s}" for c in le.classes_)
    print(header)
    for i, row in enumerate(cm):
        print(f"  {le.classes_[i]:6s} " + "  ".join(f"{v:10d}" for v in row))

    print("\n" + "═" * 60)
    print("  FEATURE IMPORTANCE (top 15)")
    print("═" * 60)
    importances = pd.Series(rf.feature_importances_, index=FEATURE_NAMES)
    top = importances.nlargest(15)
    max_imp = top.max()
    for feat, imp in top.items():
        bar = "█" * int(imp / max_imp * 30)
        print(f"  {feat:<25s}  {imp:.4f}  {bar}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. SALVATAGGIO
# ─────────────────────────────────────────────────────────────────────────────

def save_model(rf, le, low_thr, high_thr, path: str):
    payload = {
        "model":         rf,
        "label_encoder": le,
        "thresholds":    {"low": low_thr, "high": high_thr},
        "feature_names": FEATURE_NAMES,
    }
    with open(path, "wb") as f:
        pickle.dump(payload, f)
    print(f"\n  [OK] Modello salvato in: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Addestra il classificatore Rafflesia")
    parser.add_argument("--low",             type=float, default=None)
    parser.add_argument("--high",            type=float, default=None)
    parser.add_argument("--show-thresholds", action="store_true")
    parser.add_argument("--estimators",      type=int, default=300)
    parser.add_argument("--output",          type=str,
                        default=os.path.join(os.path.dirname(__file__), "model.pkl"))
    parser.add_argument("--overrides",       type=str,
                        default=os.path.join(os.path.dirname(__file__), "labels-override.json"))
    args = parser.parse_args()

    # ── Carica tutte le carte (escluse Territory e Token) ────────────
    print("Caricamento carte...")
    df_all = load_cards()
    df_all = df_all[~df_all["type_line"].isin(["Territory", "Token"])].copy()
    print(f"  {len(df_all)} carte totali (esclusi Territory e Token)")

    # ── Calcola power_score su tutte ─────────────────────────────────
    print("\nCalcolo power_score...")
    scores_all = compute_power_scores(df_all)
    df_all["_power_score"] = scores_all

    # ── Seleziona il training set: rosse + trusted + override ────────
    mask_red     = df_all["color"] == "red"
    mask_trusted = df_all["name"].isin(TRUSTED_CARDS)
    df_train = df_all[mask_red | mask_trusted].copy()
    scores_train = scores_all[df_train.index]

    print(f"\n  Training set:")
    print(f"    Carte rosse:   {mask_red.sum()}")
    print(f"    Trusted extra: {mask_trusted.sum()} ({', '.join(df_train[mask_trusted]['name'].tolist())})")

    # ── Mostra soglie (calcolate solo sulle rosse per coerenza) ──────
    scores_red = scores_all[mask_red]
    if args.show_thresholds:
        print("\n  Distribuzione power_score (carte rosse):")
        for p in [10, 25, 33, 50, 67, 75, 90]:
            print(f"    P{p:2d}: {scores_red.quantile(p/100):.4f}")
        print(f"    min: {scores_red.min():.4f}   max: {scores_red.max():.4f}")
        low, high = scores_red.quantile(0.33), scores_red.quantile(0.67)
        print(f"\n  Soglie automatiche:  low={low:.4f}  high={high:.4f}")
        return

    # ── Etichette dal power_score (soglie calibrate sulle rosse) ─────
    print("\nAssegnazione etichette...")
    labels, low_thr, high_thr = assign_labels(scores_red, args.low, args.high)

    # Estendi le etichette al training set completo (trusted incluse)
    all_labels = pd.cut(
        scores_train,
        bins=[-np.inf, low_thr, high_thr, np.inf],
        labels=["debole", "bilanciata", "forte"]
    )
    df_train["label"] = all_labels.values
    df_train["_overridden"] = False
    df_train = df_train[df_train["label"].notna()].copy()
    scores_train = scores_train[df_train.index]

    print(f"  Soglie (da carte rosse):  debole < {low_thr:.4f}  ≤  bilanciata  ≤  {high_thr:.4f} < forte")

    # ── Override manuali ──────────────────────────────────────────────
    if args.overrides and os.path.exists(args.overrides):
        with open(args.overrides, "r", encoding="utf-8") as f:
            overrides = json.load(f)

        n_applied = 0
        for entry in overrides:
            # Aggiorna se già nel training set
            mask = df_train["name"] == entry["name"]
            if mask.any():
                df_train.loc[mask, "label"] = entry["power_class"]
                df_train.loc[mask, "_overridden"] = True
                n_applied += 1
            else:
                # Aggiunge la carta al training set se non era né rossa né trusted
                card_row = df_all[df_all["name"] == entry["name"]]
                if not card_row.empty:
                    card_row = card_row.copy()
                    card_row["label"] = entry["power_class"]
                    card_row["_overridden"] = True
                    df_train = pd.concat([df_train, card_row])
                    scores_train = pd.concat([scores_train, scores_all[card_row.index]])
                    n_applied += 1
                else:
                    print(f"  [WARN] override non trovato: {entry['name']!r}")

        print(f"  Override applicati: {n_applied}/{len(overrides)}")

    show_label_distribution(df_train["label"], scores_train, df_train)

    # ── Feature matrix ────────────────────────────────────────────────
    print("\nCostruzione feature matrix...")
    X = build_feature_matrix(df_train)
    y = df_train["label"]
    print(f"  Carte nel training set: {len(X)}  |  Feature: {X.shape[1]}")

    # ── Training ──────────────────────────────────────────────────────
    print("\nTraining Random Forest...")
    rf, le, cv_scores = train_classifier(X, y, n_estimators=args.estimators)

    # ── Report ────────────────────────────────────────────────────────
    y_enc = le.transform(y)
    print_report(rf, le, X, y_enc, df_train, scores_train)

    # ── Salva ─────────────────────────────────────────────────────────
    save_model(rf, le, low_thr, high_thr, args.output)

    print("\n" + "═" * 60)
    print("  PROSSIMO PASSO:")
    print("  python classifier/classify.py")
    print("═" * 60)


if __name__ == "__main__":
    main()
