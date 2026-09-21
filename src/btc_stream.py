import asyncio, json, websockets

URL = "wss://ws-feed.exchange.coinbase.com"


async def stream_btc(on_price):
    sub = {"type": "subscribe", "product_ids": ["BTC-USD"], "channels": ["ticker"]}
    while True:
        try:
            async with websockets.connect(URL, ping_interval=20) as ws:
                await ws.send(json.dumps(sub))
                async for raw in ws:
                    msg = json.loads(raw)
                    if msg.get("type") == "ticker":
                        await on_price(msg["time"], float(msg["price"]))
        except Exception as e:
            print("Stream error, reconnecting in 5s:", e)
            await asyncio.sleep(5)


if __name__ == "__main__":
    async def show(t, p):
        print(t, p)
    asyncio.run(stream_btc(show))