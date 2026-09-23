import sqlite3, sys
from datetime import datetime, timedelta

START = sys.argv[1] if len(sys.argv) > 1 else "2026-09-23T14:09"
MINUTES = int(sys.argv[2]) if len(sys.argv) > 2 else 20

c = sqlite3.connect("data/market.db")
start = datetime.fromisoformat(START)
end = start + timedelta(minutes=MINUTES)
iso = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

# BTC at the start, to pick a near-the-money contract
spot0 = c.execute("SELECT price FROM btc_ticks WHERE ts >= ? ORDER BY ts LIMIT 1", (iso(start),)).fetchone()
if not spot0:
    print("No BTC data in that window."); raise SystemExit
spot0 = spot0[0]

# The contract closest to the money at that moment, from the nearest expiry still open
row = c.execute("""SELECT ticker, strike, close_time FROM kalshi_quotes
                   WHERE ts >= ? AND close_time > ? AND strike IS NOT NULL
                     AND yes_bid > 0.15 AND yes_ask < 0.85
                   ORDER BY close_time, ABS(strike - ?) LIMIT 1""",
                (iso(start), iso(end), spot0)).fetchone()
if not row:
    print("No near-the-money contract found in that window."); raise SystemExit
ticker, strike, close_time = row

print(f"BTC ${spot0:,.0f} at {START} | tracking {ticker}")
print(f"strike ${strike:,.0f}, expires {close_time[:16]}\n")
print(f"{'time':<10}{'BTC':>10}{'d BTC':>9}{'bid':>7}{'ask':>7}{'d mid':>8}")

prev_btc = prev_mid = None
for ts, bid, ask in c.execute(
        """SELECT ts, yes_bid, yes_ask FROM kalshi_quotes
           WHERE ticker = ? AND ts BETWEEN ? AND ? ORDER BY ts""",
        (ticker, iso(start), iso(end))):
    btc = c.execute("SELECT price FROM btc_ticks WHERE ts <= ? ORDER BY ts DESC LIMIT 1", (ts,)).fetchone()
    if not btc:
        continue
    btc, mid = btc[0], (bid + ask) / 2
    d_btc = f"{btc - prev_btc:>+9.0f}" if prev_btc else f"{'':>9}"
    d_mid = f"{mid - prev_mid:>+8.3f}" if prev_mid else f"{'':>8}"
    print(f"{ts[11:19]:<10}{btc:>10,.0f}{d_btc}{bid:>7.2f}{ask:>7.2f}{d_mid}")
    prev_btc, prev_mid = btc, mid