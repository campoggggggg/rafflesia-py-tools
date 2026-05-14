import sys
from database.load_cards import load_cards
from efficiency.core import efficiency

name_query = sys.argv[1].lower()
df = load_cards()
df["cost_total"] = df["cost_neutral"].fillna(0) + df["cost_color"].fillna(0)
matches = df[df["name"].str.lower().str.contains(name_query, na=False)]
if matches.empty:
    print("Carta non trovata:", name_query)
    sys.exit(1)
card = matches.iloc[0]
print("name:    ", card["name"])
print("type:    ", card["type_line"])
print("cost:    ", card["cost_neutral"], "neutral +", card["cost_color"], "color")
print("stats:   ", card["atk"], "/", card["def"])
print("keywords:", card["keywords_list"])
print("text:")
print(card["card_text"])
print()
eff, contrib = efficiency(card)
print("efficiency:", round(eff, 4))
for k, v in contrib.items():
    print(" ", k, ":", v)
