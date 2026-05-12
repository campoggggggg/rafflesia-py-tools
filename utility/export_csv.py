import pandas as pd
from database.load_cards import load_cards
from efficiency import efficiency

df = load_cards()
df["cost_total"] = df["cost_neutral"].fillna(0) + df["cost_color"].fillna(0)

df[["efficiency", "contributions"]] = df.apply(
    lambda card: pd.Series(efficiency(card)), axis=1
)

contrib_df = pd.json_normalize(df["contributions"])

result = pd.concat(
    [df[["name", "type_line", "color", "cost_total", "atk", "def", "efficiency"]], contrib_df],
    axis=1,
)

result = result.sort_values(["color", "name"])
result.to_csv("cards_efficiency.csv", index=False, sep=";")
print(f"Salvato cards_efficiency.csv — {len(result)} carte")
