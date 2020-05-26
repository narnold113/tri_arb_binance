import websockets
import asyncio
import time
import sys
import json
from datetime import datetime

PAIRS = [
    'ethusdt',
    'btcusdt'
]
STREAMS = []

for pair in PAIRS:
    STREAMS.append(pair + '@depth@100ms')
# print(STREAMS)

async def subscribe() -> None:
    url = 'wss://stream.binance.com:9443/stream'
    strParams = '''{"method": "SUBSCRIBE","params": "placeholder","id": 1}'''
    params = json.loads(strParams)
    params['params'] = STREAMS
    try:
        async with websockets.client.connect(url) as ws:
            try:
                await ws.send(str(params).replace('\'', '"'))
            except Exception as err:
                print(err)
            while 1:
                res = await ws.recv()
                print(res)
    except Exception as err:
        print(err)


async def main():
    await subscribe()
    # pass

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()