import sqlite3, sys
from datetime import datetime, timezone
from statistics import mean
from src.pricing import prob_above

LEAD_MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 30   # minutes before close to score
VOLS = [0.30, 0.35, 0.40, 0.45, 0.50]                      # candidate model vols

c = sqlite3.connect("data/market.db")
now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# Contracts whose close time has passed
expiries = [r[0] for r in c.execute(
    "SELECT DISTINCT close_time FROM kalshi_quotes WHERE close_time < ? ORDER BY close_time", (now,))]

samples = []
for close in expiries:
    # BTC price at settlement
    settle = c.execute("SELECT price FROM btc_ticks WHERE ts <= ? ORDER BY ts DESC LIMIT 1", (close,)).fetchone()
    if not settle:
        continue
    settle = settle[0]

    # Target snapshot time: LEAD_MIN before close
    close_dt = datetime.fromisoformat(close.replace("Z", "+00:00"))
    target = (close_dt.timestamp() - LEAD_MIN * 60)
    target_iso = datetime.fromtimestamp(target, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    ts = c.execute("SELECT MAX(ts) FROM kalshi_quotes WHERE close_time = ? AND ts <= ?",
                   (close, target_iso)).fetchone()[0]
    if not ts:
        continue
    spot = c.execute("SELECT price FROM btc_ticks WHERE ts <= ? ORDER BY ts DESC LIMIT 1", (ts,)).fetchone()
    if not spot:
        continue
    spot = spot[0]
    years = LEAD_MIN * 60 / (365 * 24 * 3600)

    for strike, bid, ask in c.execute(
            """SELECT strike, yes_bid, yes_ask FROM kalshi_quotes
               WHERE close_time = ? AND ts = ? AND yes_bid > 0 AND yes_ask < 1""", (close, ts)):
        if strike is None:
            continue
        mkt = (bid + ask) / 2
        outcome = 1.0 if settle > strike else 0.0
        samples.append((spot, strike, years, mkt, outcome))

if not samples:
    print("No settled contracts logged yet. Let the loggers run longer.")
    raise SystemExit

def brier(preds):
    return mean((p - o) ** 2 for p, o in preds)

print(f"{len(samples)} contract outcomes, scored {LEAD_MIN} min before close")
print("(lower Brier score = better prediction)\n")
print(f"  market             {brier([(s[3], s[4]) for s in samples]):.4f}")
for v in VOLS:
    preds = [(prob_above(s[0], s[1], s[2], v), s[4]) for s in samples]
    print(f"  model vol {v:.0%}      {brier(preds):.4f}")