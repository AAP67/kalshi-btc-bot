import os, sqlite3

DB_PATH = "data/market.db"


def connect():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE IF NOT EXISTS btc_ticks (ts TEXT NOT NULL, price REAL NOT NULL)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_btc_ts ON btc_ticks(ts)")
    return conn