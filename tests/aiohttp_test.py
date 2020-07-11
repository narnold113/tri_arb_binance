import aiohttp
import asyncio
import requests

ARBS = [
    'eth' # OK
    ,'ltc' # OK
    ,'xrp' # OK
    ,'bch' # OK
    ,'eos' # OK
    ,'xmr' # OK
    ,'etc' # OK
    ,'zrx' # OK
    ,'trx'
]
PAIRS = []
for arb in ARBS:
    PAIRS.append(arb + 'usdt')
    PAIRS.append(arb + 'btc')
PAIRS.insert(0, 'btcusdt')

async def getSnap(pair):
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.binance.com/api/v3/depth?symbol={}&limit=500'.format(pair.upper())) as response:

            json_snapshot = await response.json()
            print("Status:", response.status)

            # print("Content-type:", response.headers['content-type'])
            #
            # html = await response.text()
            # print("Body:", html[:15], "...")

# async def getSnap2(pair):
#     raw_snapshot = requests.get('https://www.binance.com/api/v3/depth?symbol={}&limit=500'.format(pair.upper()))
#     if raw_snapshot.status_code == 200:
#         snapshot = raw_snapshot.json()
#         print('Filled', pair, 'orderbook successfully')
#     else:
#         print(raw_snapshot.status_code)


async def main():
    # coroutines = [
    #     getSnap(pair)
    #     for pairs in PAIRS
    # ]
    # print('\n\n\n\nsomething')
    await asyncio.wait([getSnap(pair) for pair in PAIRS])



if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
