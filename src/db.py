import os, sqlite3

DB_PATH = "data/market.db"


def connect():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    # BTC prices from Coinbase
    conn.execute("CREATE TABLE IF NOT EXISTS btc_ticks (ts TEXT NOT NULL, price REAL NOT NULL)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_btc_ts ON btc_ticks(ts)")

    # Kalshi contract snapshots
    conn.execute("""CREATE TABLE IF NOT EXISTS kalshi_quotes (
        ts TEXT NOT NULL, ticker TEXT NOT NULL, event_ticker TEXT,
        strike REAL, close_time TEXT,
        yes_bid REAL, yes_ask REAL, bid_size REAL, ask_size REAL)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_kq ON kalshi_quotes(ticker, ts)")

    # Multi-exchange index price
    conn.execute("""CREATE TABLE IF NOT EXISTS index_ticks (
        ts TEXT NOT NULL, idx REAL NOT NULL,
        coinbase REAL, kraken REAL, bitstamp REAL)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_index_ts ON index_ticks(ts)")

    return conn