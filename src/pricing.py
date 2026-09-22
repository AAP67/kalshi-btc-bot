import math
from datetime import datetime, timezone, timedelta

SECONDS_PER_YEAR = 365 * 24 * 3600


def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def prob_above(spot, strike, years, vol):
    """Probability BTC finishes above `strike` after `years`, given annualized `vol`."""
    if years <= 0:
        return 1.0 if spot > strike else 0.0
    sd = vol * math.sqrt(years)                      # expected spread of outcomes
    d2 = (math.log(spot / strike) - 0.5 * sd * sd) / sd
    return norm_cdf(d2)


def years_until(close_time_iso):
    close = datetime.fromisoformat(close_time_iso.replace("Z", "+00:00"))
    secs = (close - datetime.now(timezone.utc)).total_seconds()
    return max(secs, 0) / SECONDS_PER_YEAR


if __name__ == "__main__":
    from src.volatility import get_closes, realized_vol

    closes = get_closes(300)
    spot, vol = closes[-1], realized_vol(closes, 5)

    # Next 5pm ET settlement (21:00 UTC)
    now = datetime.now(timezone.utc)
    close = now.replace(hour=21, minute=0, second=0, microsecond=0)
    if close <= now:
        close += timedelta(days=1)
    years = years_until(close.isoformat())

    print(f"BTC ${spot:,.2f} | vol {vol:.1%} | {years*365*24:.1f}h to {close:%b %d %H:%M} UTC\n")
    base = round(spot / 250) * 250
    for offset in range(-3000, 3001, 500):
        strike = base + offset - 0.01
        print(f"  above ${strike:>10,.2f}:  {prob_above(spot, strike, years, vol):6.1%}")