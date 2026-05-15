import pandas as pd
from database.load_cards import load_cards
from efficiency import efficiency

df = load_cards()
df["cost_total"] = df["cost_neutral"].fillna(0) + df["cost_color"].fillna(0)

# PASS 1 — calcola P75 sui soli minion per calibrare
df_minions = df[df["type_line"] == "Minion"].copy()
df_minions["ps_temp"] = df_minions.apply(lambda c: efficiency(c)[0], axis=1)
P75_MINION = df_minions["ps_temp"].quantile(0.75)

# PASS 2 — efficiency su tutto il dataset
df[["efficiency", "contributions"]] = df.apply(
    lambda card: pd.Series(efficiency(card)), axis=1
)

print(f"mean efficiency: {df['efficiency'].mean():.3f}")
print(f"var  efficiency: {df['efficiency'].var():.3f}")

top = (
    df[["name", "type_line", "color", "cost_total", "atk", "def", "efficiency", "contributions"]]
    .sort_values("efficiency", ascending=False)
    
)

print()
print(top[["name", "type_line", "color", "cost_total", "atk", "def", "efficiency"]])
print()

for _, row in top.iterrows():
    nonzero = {k: v for k, v in row["contributions"].items() if v != 0}
    print(f"{row['name']}: {nonzero}")
