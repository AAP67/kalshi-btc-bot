import sqlite3

c = sqlite3.connect("data/market.db")

n, t0, t1 = c.execute("SELECT COUNT(*), MIN(ts), MAX(ts) FROM btc_ticks").fetchone()
print(f"BTC ticks:     {n:,} | {t0} -> {t1}")

n, k, t0, t1 = c.execute(
    "SELECT COUNT(*), COUNT(DISTINCT ticker), MIN(ts), MAX(ts) FROM kalshi_quotes").fetchone()
print(f"Kalshi quotes: {n:,} rows, {k} contracts | {t0} -> {t1}")

# Match the latest Kalshi snapshot to the BTC price at that moment
ts = c.execute("SELECT MAX(ts) FROM kalshi_quotes").fetchone()[0]
btc = c.execute(
    "SELECT ts, price FROM btc_ticks WHERE ts <= ? ORDER BY ts DESC LIMIT 1", (ts,)).fetchone()

print(f"\nSnapshot at {ts}")
print(f"BTC price then: ${btc[1]:,.2f}" if btc else "No BTC tick before this snapshot")

print("\nNear-the-money contracts (priced 20-80c):")
rows = c.execute("""SELECT close_time, strike, yes_bid, yes_ask FROM kalshi_quotes
                    WHERE ts = ? AND yes_bid >= 0.2 AND yes_ask <= 0.8
                    ORDER BY close_time, strike""", (ts,)).fetchall()
for close, strike, bid, ask in rows:
    print(f"  closes {close} | strike ${strike:,.0f} | bid {bid:.2f} / ask {ask:.2f}")