import os, time, base64, requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

URLS = {
    "demo": "https://demo-api.kalshi.co",
    "prod": "https://api.elections.kalshi.com",
}
PREFIX = "/trade-api/v2"


class KalshiClient:
    def __init__(self, env="demo", auth=True):
        self.base = URLS[env]
        self.session = requests.Session()
        self.private_key = None
        if auth:
            self.key_id = os.environ["KALSHI_API_KEY_ID"]
            pem = os.environ["KALSHI_PRIVATE_KEY"].replace("\\n", "\n")
            self.private_key = serialization.load_pem_private_key(pem.encode(), password=None)

    def _headers(self, method, path):
        if not self.private_key:
            return {}
        ts = str(int(time.time() * 1000))
        sig = self.private_key.sign(
            (ts + method + PREFIX + path).encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA256(),
        )
        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-TIMESTAMP": ts,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode(),
        }

    def get(self, path, params=None):
        r = self.session.get(self.base + PREFIX + path,
                             headers=self._headers("GET", path),
                             params=params, timeout=10)
        r.raise_for_status()
        return r.json()

    def get_markets(self, series="KXBTCD", status="open", limit=200):
        return self.get("/markets", {"series_ticker": series,
                                     "status": status, "limit": limit})["markets"]

    def get_balance(self):
        return self.get("/portfolio/balance")["balance"] / 100