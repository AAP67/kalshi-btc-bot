import asyncio, time
from src.db import connect
from src.btc_stream import stream_btc

conn = connect()
buffer = []
last_flush = time.time()


async def save(ts, price):
    global last_flush
    buffer.append((ts, price))
    if time.time() - last_flush >= 5:
        conn.executemany("INSERT INTO btc_ticks VALUES (?, ?)", buffer)
        conn.commit()
        print(f"Saved {len(buffer)} ticks | last: {price}")
        buffer.clear()
        last_flush = time.time()


if __name__ == "__main__":
    asyncio.run(stream_btc(save))