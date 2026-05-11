#db_conn.py
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

def get_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

if __name__ == "__main__":
    db = get_client()
    res = db.table("cards").select("id", count="exact").execute()
    print(f"Connessione risucita. Carte: {res.count}")