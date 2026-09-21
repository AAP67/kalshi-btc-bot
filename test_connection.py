import os, time, base64, requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

BASE = "https://demo-api.kalshi.co"
PREFIX = "/trade-api/v2"
KEY_ID = os.environ["KALSHI_API_KEY_ID"]
pem = os.environ["KALSHI_PRIVATE_KEY"].replace("\\n", "\n")
private_key = serialization.load_pem_private_key(pem.encode(), password=None)

def auth_headers(method, path):
    ts = str(int(time.time() * 1000))
    msg = (ts + method + PREFIX + path).encode()
    sig = private_key.sign(
        msg,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )
    return {
        "KALSHI-ACCESS-KEY": KEY_ID,
        "KALSHI-ACCESS-TIMESTAMP": ts,
        "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode(),
    }

def get(path, params=None):
    r = requests.get(BASE + PREFIX + path, headers=auth_headers("GET", path),
                     params=params, timeout=10)
    r.raise_for_status()
    return r.json()

# 1. Auth check
print("Balance: $", get("/portfolio/balance")["balance"] / 100)

# 2. Open BTC markets
markets = get("/markets", {"series_ticker": "KXBTCD", "status": "open", "limit": 10})["markets"]
print(f"\n{len(markets)} open BTC markets:")
for m in markets:
    print(m["ticker"], "| yes bid/ask: $", m.get("yes_bid_dollars"), "/ $", m.get("yes_ask_dollars"),
          "| closes:", m.get("close_time"))

print(markets[0].keys())