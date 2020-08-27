import aiohttp
import asyncio
import hmac
import hashlib
import os
import time
import math
from statistics import mean
APIKEY = str(os.environ["BIN_API"])
SECRETKEY = str(os.environ["BIN_SECRET"])

def round_quote_precision(quantity):
    factor = 10 ** 8
    return math.floor(quantity * factor) / factor

def create_signed_params(symbol, side, quantity, recvWindow):
    timestamp = int(round(time.time() * 1000))
    query_string = 'symbol={}&side={}&type={}&quoteOrderQty={}&recvWindow={}&timestamp={}'.format(symbol, side, 'MARKET', quantity, recvWindow, timestamp)
    signature = hmac.new(bytes(SECRETKEY, 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
    return {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quoteOrderQty': quantity,
        'recvWindow': recvWindow,
        'timestamp': timestamp,
        'signature': signature
    }

async def ex_trade(pair, side, quantity, recvWindow, leg, wait_time):
    trade_url = 'https://api.binance.com/api/v3/order'
    api_header = {'X-MBX-APIKEY': APIKEY}
    if leg == 1:
        pass
    elif leg == 2:
        await asyncio.sleep(wait_time)
        # pass
    elif leg == 3:
        await asyncio.sleep(wait_time * 2)
        # pass
    params = create_signed_params(pair, side, quantity, recvWindow)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=trade_url, headers=api_header, params=params) as resp:
                json_res = await resp.json()
                if json_res is not None:
                    if resp.status == 200:
                        print({'content': json_res, 'params': params})
                    else:
                        if json_res['code'] == -2010:
                            print('Trade failed. Insufficient Funds. Recursion yay')
                            return await ex_trade(pair, side, str(round_quote_precision(float(quantity) * 0.999)), recvWindow, 1)
                        else:
                            print('Some other type of error occurred: {}'.format(json_res))
    except Exception as err:
        print(err)

async def tests():
    # coroutines = [ex_trade('BTCUSDT', 'BUY', '20', 5_000, 1), ex_trade('ETHBTC', 'BUY', '0.00177', 5_000, 2)]
    wait_time = float(input('Wait time: '))
    coroutines = [
        ex_trade('BTCUSDT', 'BUY', '20', 5_000, 1, wait_time),
        ex_trade('ETHBTC', 'BUY', '0.00177', 5_000, 2, wait_time),
        ex_trade('ETHUSDT', 'SELL', '19.7', 5_000, 3, wait_time)
    ]
    await asyncio.wait(coroutines)


async def main():
    await tests()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
