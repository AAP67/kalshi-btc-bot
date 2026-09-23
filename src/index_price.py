import requests

HEADERS = {"User-Agent": "kalshi-btc-bot"}

SOURCES = {
    "coinbase": ("https://api.exchange.coinbase.com/products/BTC-USD/ticker",
                 lambda j: float(j["price"])),
    "kraken":   ("https://api.kraken.com/0/public/Ticker?pair=XBTUSD",
                 lambda j: float(next(iter(j["result"].values()))["c"][0])),
    "bitstamp": ("https://www.bitstamp.net/api/v2/ticker/btcusd/",
                 lambda j: float(j["last"])),
}


def fetch_all(timeout=5):
    """Return {exchange: price} for whichever sources respond."""
    out = {}
    for name, (url, parse) in SOURCES.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            out[name] = parse(r.json())
        except Exception as e:
            print(f"  {name} failed: {e}")
    return out


def index_price(prices):
    """Median across exchanges - resistant to one bad quote."""
    vals = sorted(prices.values())
    if not vals:
        return None
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2


if __name__ == "__main__":
    prices = fetch_all()
    for name, p in prices.items():
        print(f"{name:<10} ${p:,.2f}")
    idx = index_price(prices)
    print(f"{'index':<10} ${idx:,.2f}" if idx else "No sources responded")