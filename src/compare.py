from datetime import datetime
from src.kalshi_client import KalshiClient
from src.pricing import prob_above, years_until
from src.volatility import get_closes, realized_vol

FEE_RATE = 0.07   # Kalshi taker fee ~ 0.07 * P * (1 - P) per contract
MIN_EDGE = 0.02   # flag gaps of 2c or more after fees


def num(x):
    return float(x) if x not in (None, "") else None


def fee(p):
    return FEE_RATE * p * (1 - p)


closes = get_closes(300)
spot, vol = closes[-1], realized_vol(closes, 5)
markets = KalshiClient("prod", auth=False).get_markets(limit=1000)

rows = []
for m in markets:
    strike, bid, ask = num(m.get("floor_strike")), num(m.get("yes_bid_dollars")), num(m.get("yes_ask_dollars"))
    if strike is None or not bid or not ask or bid < 0.05 or ask > 0.95:
        continue  # skip empty and extreme contracts
    years = years_until(m["close_time"])
    if years <= 0:
        continue
    p = prob_above(spot, strike, years, vol)
    edge_yes = p - ask - fee(ask)    # buy Yes at the ask
    edge_no = bid - p - fee(bid)     # buy No (= sell Yes at the bid)
    signal = "BUY YES" if edge_yes >= MIN_EDGE else "BUY NO" if edge_no >= MIN_EDGE else ""
    rows.append((m["close_time"], strike, bid, ask, p, edge_yes, edge_no, signal))

print(f"BTC ${spot:,.2f} | vol {vol:.1%}\n")
print(f"{'closes (UTC)':<13}{'strike':>11}{'bid':>6}{'ask':>6}{'model':>7}{'edgeY':>7}{'edgeN':>7}  signal")
for close, strike, bid, ask, p, ey, en, sig in sorted(rows):
    t = datetime.fromisoformat(close.replace("Z", "+00:00")).strftime("%m-%d %H:%M")
    print(f"{t:<13}{strike:>11,.0f}{bid:>6.2f}{ask:>6.2f}{p:>7.2f}{ey:>+7.2f}{en:>+7.2f}  {sig}")