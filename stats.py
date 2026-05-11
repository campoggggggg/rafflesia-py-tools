# stats.py
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import skew, kurtosis, median_abs_deviation
import matplotlib.pyplot as plt
import seaborn as sns

from power_score import df, power_score  # df già ha cost_total, color, etc.

# add power_score al df

df[["power_score", "contributions"]] = df.apply(
    lambda card: pd.Series(power_score(card)), axis=1
)

# feature
# vanilla rate è il rapporto stats/cost, ignorando l'effetto

df["stat_sum"] = df["atk"].fillna(0) + df["def"].fillna(0) # fillna riempie con 0 se il valore è null

df["vanilla_rate"] = np.where(
    df["type_line"] == "Minion",
    df["stat_sum"] / (df["cost_total"] + 1),
    np.nan
)

# escludi token e territory dal df. USA df_play PER LE STAT!
df_play = df[~df["type_line"].isin(["Territory", "Token"])].copy()
# nuovi df per pool ridotti
df_minions = df_play[df_play["type_line"] == "Minion"]
df_spells  = df_play[df_play["type_line"] == "Spell"]

# funzione che riceve il df e cols, per evitare ripetizione di codice
def describe_pool(df, cols, label=""):
    stats = df[cols].describe() # describe fa le stat più comuni mean, std, percentiles non ricordo quali
    skewness = pd.DataFrame(df[cols].skew()).T
    kurt = pd.DataFrame(df[cols].kurtosis()).T
    skewness.index = ["skewness"]
    kurt.index = ["kurtosis"]
    result = pd.concat([stats, skewness, kurt])
    print(f"\n--- {label} ---")
    return result


def describe_by_color(df, cols, label=""):
    result = (
        df.groupby("color")[cols]
        .agg(["mean", "median", "std", 
              ("skewness", lambda x: x.skew()),
              ("kurtosis", lambda x: x.kurtosis())])
    )
    print(f"\n--- {label} ---")
    return result

describe_pool(df_play, ["cost_total", "power_score"], label="Pool intero")
describe_pool(df_minions, ["atk", "def", "stat_sum", "vanilla_rate"], label="Solo Minion")
describe_pool(df_spells, ["cost_total", "power_score"], label="Solo Spell")

describe_by_color(df_play, ["cost_total", "power_score"], label="Pool intero x colore")
describe_by_color(df_minions, ["atk", "def", "stat_sum", "vanilla_rate"], label="Solo Minion x colore")
describe_by_color(df_spells, ["cost_total", "power_score"], label="Solo Spell x colore")

# boxplot 4 colori
data = df_play

palette = {"blue": "#336699",
           "red": "#8A0000",
           "green": "#385400",
           "black": "#262B2F",
           "colorless": "#A19993"}

fig, ax = plt.subplots()
sns.boxplot(data=data, x="color", y="power_score", hue="color", palette=palette, legend=False, ax=ax)
ax.set_title("Power Score per Colore")
ax.set_xlabel("colors")
ax.set_ylabel("power_score")

#kde colori
fig, ax = plt.subplots()
for c in palette:
    df_color = df_play[df_play["color"] == c]
    sns.kdeplot(data=df_color, x="power_score", color=palette[c], ax=ax)

#kde rarity
rarity_palette = {
    "Legendary": "#ffdd55",
    "Normal": "#aaaaaa"
}

fig, ax = plt.subplots()
for r in df_play["rarity"].unique():
    df_rarity = df_play[df_play["rarity"] == r]
    sns.kdeplot(data=df_rarity, x="power_score", color=rarity_palette[r], label=r, ax=ax)

ax.legend()

# mana curve
#pool intero
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()  # trasforma la griglia 2x3 in una lista piatta di 6 axes

for i, c in enumerate(palette):
    df_color = df_play[df_play["color"] == c]
    axes[i].bar(
        df_color["cost_total"].value_counts().sort_index().index,
        df_color["cost_total"].value_counts().sort_index().values,
        color=palette[c]
    )
    axes[i].set_title(c)
    axes[i].set_xlabel("Costo")
    axes[i].set_ylabel("# carte")

axes[5].set_visible(False)  # nasconde il sesto subplot vuoto
plt.suptitle("Mana Curve per Colore — Pool Intero")
plt.tight_layout()

#solo minion
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()  # trasforma la griglia 2x3 in una lista piatta di 6 axes

for i, c in enumerate(palette):
    df_color = df_minions[df_minions["color"] == c]
    axes[i].bar(
        df_color["cost_total"].value_counts().sort_index().index,
        df_color["cost_total"].value_counts().sort_index().values,
        color=palette[c]
    )
    axes[i].set_title(c)
    axes[i].set_xlabel("Costo")
    axes[i].set_ylabel("# carte")

axes[5].set_visible(False)  # nasconde il sesto subplot vuoto
plt.suptitle("Mana Curve per Colore — Solo minions")
plt.tight_layout()

#solo spell
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()  # trasforma la griglia 2x3 in una lista piatta di 6 axes

for i, c in enumerate(palette):
    df_color = df_spells[df_spells["color"] == c]
    axes[i].bar(
        df_color["cost_total"].value_counts().sort_index().index,
        df_color["cost_total"].value_counts().sort_index().values,
        color=palette[c]
    )
    axes[i].set_title(c)
    axes[i].set_xlabel("Costo")
    axes[i].set_ylabel("# carte")

axes[5].set_visible(False)  # nasconde il sesto subplot vuoto
plt.suptitle("Mana Curve per Colore — Solo spells")
plt.tight_layout()

# scatter plot ATK - DEF
fig, ax = plt.subplots()
sns.scatterplot(
    data=df_minions,
    x="atk",
    y="def",
    hue="color",
    palette=palette,
    ax=ax
)
ax.set_title("ATK vs DEF — Minion")
ax.set_xlabel("ATK")
ax.set_ylabel("DEF")

# scatter plot power_score - cost_total
fig, ax = plt.subplots()
sns.scatterplot(
    data=df_play,
    x="cost_total",
    y="power_score",
    hue="color",
    palette=palette,
    ax=ax
)
ax.set_title("power_score VS cost_total — Pool intero")
ax.set_xlabel("cost")
ax.set_ylabel("power score")
coeff = np.polyfit(df_play["cost_total"], df_play["power_score"], 2)
p = np.poly1d(coeff)
xs = np.linspace(df_play["cost_total"].min(), df_play["cost_total"].max(), 20)
ax.plot(xs, p(xs), "--", color="#ffdd55")

#outlier
mad = median_abs_deviation(df_play["power_score"], scale="normal")
med = df_play["power_score"].median()

df_play["modified_z"] = 0.6745 * (df_play["power_score"] - med) / mad
df_play["is_outlier"] = df_play["modified_z"].abs() > 1.5

print(df_play[df_play["is_outlier"]][["name", "type_line", "color", "cost_total", "atk", "def", "power_score", "modified_z"]]
      .sort_values("modified_z", ascending=False))

#main
if __name__ == "__main__":
    if __name__ == "__main__":
    # statistiche descrittive
        print(describe_pool(df_play, ["cost_total", "power_score"], label="Pool intero"))
        print(describe_pool(df_minions, ["atk", "def", "stat_sum", "vanilla_rate"], label="Solo Minion"))
        print(describe_pool(df_spells, ["cost_total", "power_score"], label="Solo Spell"))

        print(describe_by_color(df_play, ["cost_total", "power_score"], label="Pool intero x colore"))
        print(describe_by_color(df_minions, ["atk", "def", "stat_sum", "vanilla_rate"], label="Solo Minion x colore"))
        print(describe_by_color(df_spells, ["cost_total", "power_score"], label="Solo Spell x colore"))

        # outlier
        print(df_play[df_play["is_outlier"]][["name", "type_line", "color", "cost_total", "atk", "def", "power_score", "modified_z"]]
            .sort_values("modified_z", ascending=False))

        # plot
        #plt.show()