#load_cards.py
import pandas as pd
from database.db_conn import get_client

def load_cards():
    db = get_client()

    #supabase non fa join automatici
    #quindi carico le tabelle e poi le unisco

    res = db.table("cards").select("*").execute()
    df = pd.DataFrame(res.data)

    res_ctc = db.table("card_to_colors").select("card_id, colors(name)").execute()
    colors_df = pd.DataFrame([
        {"card_id": r["card_id"], "color": r["colors"]["name"]}
        for r in res_ctc.data
    ])

    df = df.merge(colors_df, left_on="id", right_on="card_id", how="left")
    df["color"] = df["color"].fillna("colorless")

    res_ktw = db.table("card_to_keywords").select("card_id, keywords(name)").execute()
    keywords_df = pd.DataFrame([
        {"card_id": r["card_id"], "keywords": r["keywords"]["name"]}
        for r in res_ktw.data
        if r["keywords"]  # alcuni potrebbero essere null
    ])

    # raggruppa per card_id — una carta può avere più keyword
    keywords_grouped = (
        keywords_df.groupby("card_id")["keywords"]
        .apply(lambda x: [k.lower() for k in x])
        .reset_index()
        .rename(columns={"keywords": "keywords_list"})
    )

    df = df.merge(keywords_grouped, left_on="id", right_on="card_id", how="left")
    df["keywords_list"] = df["keywords_list"].apply(lambda x: x if isinstance(x, list) else [])

    return df

if __name__ == "__main__":
    df = load_cards()
    print(df[["name", "type_line", "color", "cost_neutral", "cost_color", "atk", "def"]].head(10))
    print(f"\nShape: {df.shape}")
    print(df.columns.tolist())
    print(df.dtypes)