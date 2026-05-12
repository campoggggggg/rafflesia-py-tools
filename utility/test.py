import pandas as pd
from database.load_cards import load_cards
from utility.text_normalizer import normalize_text


df = load_cards()
df_m = df[df["type_line"] == "Minion"].copy()
df_m["total"] = df_m["atk"].fillna(0) + df_m["def"].fillna(0)
print(df_m["total"].describe())


df = load_cards()
df["cost_total"] = df["cost_neutral"].fillna(0) + df["cost_color"].fillna(0)
df["text_norm"] = df["card_text"].apply(lambda t: normalize_text(t) if not pd.isna(t) else "")
cond = df[df["text_norm"].str.contains(r"\bif\b", regex=True)]
print(f"Carte con condizione: {len(cond)}/{len(df)}")
print()
for _, row in cond.iterrows():
    print(f"{row['name']} ({row['type_line']}, cost {row['cost_total']}): {row['id']}")