from collections import defaultdict
from statistics import median
from src.kalshi_client import KalshiClient
from src.pricing import prob_above, years_until
from src.volatility import get_spot, get_closes, realized_vol


def num(x):
    return float(x) if x not in (None, "") else None


def implied_vol(price, spot, strike, years, lo=0.05, hi=3.0, iters=60):
    """Find the vol that makes the model's probability equal the market price."""
    f = lambda v: prob_above(spot, strike, years, v) - price
    f_lo = f(lo)
    if f_lo * f(hi) > 0:
        return None  # no vol in range reproduces this price
    for _ in range(iters):
        mid = (lo + hi) / 2
        f_mid = f(mid)
        if f_lo * f_mid <= 0:
            hi = mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


if __name__ == "__main__":
    spot = get_spot()
    vol_short = realized_vol(get_closes(60), 1)
    vol_long = realized_vol(get_closes(300), 5)

    by_expiry = defaultdict(lambda: {"below": [], "above": []})
    for m in KalshiClient("prod", auth=False).get_markets(limit=1000):
        strike, bid, ask = num(m.get("floor_strike")), num(m.get("yes_bid_dollars")), num(m.get("yes_ask_dollars"))
        if strike is None or not bid or not ask:
            continue
        mid = (bid + ask) / 2
        # skip extremes (noisy) and coin-flips (price barely depends on vol)
        if not (0.10 <= mid <= 0.90) or 0.40 < mid < 0.60:
            continue
        years = years_until(m["close_time"])
        if years <= 0:
            continue
        iv = implied_vol(mid, spot, strike, years)
        if iv:
            side = "below" if strike < spot else "above"
            by_expiry[m["close_time"]][side].append(iv)

    print(f"BTC ${spot:,.2f} | realized vol: short {vol_short:.1%}, long {vol_long:.1%}\n")
    print(f"{'expiry (UTC)':<18}{'hours':>7}{'implied':>9}{'below':>8}{'above':>8}")
    for close in sorted(by_expiry):
        b, a = by_expiry[close]["below"], by_expiry[close]["above"]
        allv = b + a
        if not allv:
            continue
        hours = years_until(close) * 365 * 24
        fmt = lambda v: f"{median(v):.1%}" if v else "-"
        print(f"{close[:16]:<18}{hours:>7.1f}{fmt(allv):>9}{fmt(b):>8}{fmt(a):>8}")