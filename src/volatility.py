import requests
import numpy as np

CANDLES_URL = "https://api.exchange.coinbase.com/products/BTC-USD/candles"
MIN_PER_YEAR = 365 * 24 * 60  # BTC trades 24/7


def get_closes(granularity=60):
    """Recent closing prices. granularity = seconds per bar (60 = 1-min). Max 300 bars."""
    r = requests.get(CANDLES_URL, params={"granularity": granularity},
                     headers={"User-Agent": "kalshi-btc-bot"}, timeout=10)
    r.raise_for_status()
    bars = sorted(r.json(), key=lambda b: b[0])  # [time, low, high, open, close, volume]
    return np.array([b[4] for b in bars])


def realized_vol(closes, minutes_per_bar=1):
    """Annualized volatility from log returns."""
    rets = np.diff(np.log(closes))
    return rets.std(ddof=1) * np.sqrt(MIN_PER_YEAR / minutes_per_bar)


if __name__ == "__main__":
    c1 = get_closes(60)
    print(f"BTC: ${c1[-1]:,.2f}")
    print(f"Vol from 1-min bars (last ~{len(c1)/60:.0f}h):  {realized_vol(c1, 1):.1%}")
    c5 = get_closes(300)
    print(f"Vol from 5-min bars (last ~{len(c5)*5/60:.0f}h): {realized_vol(c5, 5):.1%}")