from datetime import datetime
from src.kalshi_client import KalshiClient
from src.pricing import prob_above, years_until
from src.volatility import get_spot, get_closes, realized_vol

FEE_RATE = 0.07      # Kalshi taker fee ~ 0.07 * P * (1 - P) per contract
MIN_EDGE = 0.02      # flag gaps of 2c or more after fees
SHORT_HOURS = 6      # contracts closing within this use short-window vol


def num(x):
    return float(x) if x not in (None, "") else None


def fee(p):
    return FEE_RATE * p * (1 - p)


spot = get_spot()
vol_short = realized_vol(get_closes(60), 1)    # last ~5h
vol_long = realized_vol(get_closes(300), 5)    # last ~25h


def vol_for(years):
    return vol_short if years * 365 * 24 <= SHORT_HOURS else vol_long


markets = KalshiClient("prod", auth=False).get_markets(limit=1000)

rows = []
for m in markets:
    strike, bid, ask = num(m.get("floor_strike")), num(m.get("yes_bid_dollars")), num(m.get("yes_ask_dollars"))
    if strike is None or not bid or not ask or bid < 0.05 or ask > 0.95:
        continue
    years = years_until(m["close_time"])
    if years <= 0:
        continue
    p = prob_above(spot, strike, years, vol_for(years))
    edge_yes = p - ask - fee(ask)
    edge_no = bid - p - fee(bid)
    signal = "BUY YES" if edge_yes >= MIN_EDGE else "BUY NO" if edge_no >= MIN_EDGE else ""
    rows.append((m["close_time"], strike, bid, ask, p, edge_yes, edge_no, signal))

print(f"BTC ${spot:,.2f} | short vol {vol_short:.1%} (<= {SHORT_HOURS}h) | long vol {vol_long:.1%}\n")
print(f"{'closes (UTC)':<13}{'strike':>11}{'bid':>6}{'ask':>6}{'model':>7}{'edgeY':>7}{'edgeN':>7}  signal")
for close, strike, bid, ask, p, ey, en, sig in sorted(rows):
    t = datetime.fromisoformat(close.replace("Z", "+00:00")).strftime("%m-%d %H:%M")
    print(f"{t:<13}{strike:>11,.0f}{bid:>6.2f}{ask:>6.2f}{p:>7.2f}{ey:>+7.2f}{en:>+7.2f}  {sig}")