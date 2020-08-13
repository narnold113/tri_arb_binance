import aiohttp
import asyncio
import hmac
import hashlib
import os
import time
from statistics import mean
APIKEY = str(os.environ["BIN_API"])
SECRETKEY = str(os.environ["BIN_SECRET"])

def create_signed_params(symbol, side, quantity, price):
    timestamp = int(round(time.time() * 1000))
    query_string = 'symbol={}&side={}&type={}&timeInForce={}&quantity={}&price={}&recvWindow={}&timestamp={}'.format(symbol, side, 'LIMIT', 'GTC', quantity, price, 10_000, timestamp)
    return {
        'symbol': symbol,
        'side': side,
        'type': 'LIMIT',
        'timeInForce': 'GTC',
        'quantity': quantity,
        'price': price,
        'recvWindow': 10_000,
        'timestamp': timestamp,
        'signature': hmac.new(bytes(SECRETKEY, 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
    }

async def cancel_orders(symbol):
    global APIKEY
    global SECRETKEY
    url = 'https://api.binance.com/api/v3/openOrders'
    header = {'X-MBX-APIKEY': APIKEY}
    timestamp = int(round(time.time() * 1000))
    query_string = 'symbol={}&timestamp={}'.format(symbol, timestamp)
    params = {
        'symbol': symbol,
        'timestamp': timestamp,
        'signature': hmac.new(bytes(SECRETKEY, 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url=url,
                                      headers=header,
                                      params=params) as resp:
                json_content = await resp.json()
                # print(json_content)
                if json_content is not None and resp.status == 200:
                    return json_content
    except Exception as err:
        print(err)

async def get_balance(quote):
    global APIKEY
    global SECRETKEY
    url = "https://api.binance.com/api/v3/account"
    header = {'X-MBX-APIKEY': APIKEY}
    timestamp = int(round(time.time() * 1000))
    recvWindow = 10_000
    query_string = 'recvWindow={}&timestamp={}'.format(recvWindow, timestamp)
    signature = hmac.new(bytes(SECRETKEY, 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
    params = {
        'recvWindow': recvWindow,
        'timestamp': timestamp,
        'signature': signature
    }
    async with aiohttp.ClientSession() as session:
        async with session.request(method="GET",
                                   url=url,
                                   headers=header,
                                   params=params) as resp:
            json_content = await resp.json()
            if json_content is not None and resp.status == 200:
                balances = [x for x in json_content['balances'] if float(x['free']) != 0]
                return [float(x['free']) for x in balances if x['asset'] == quote][0]

async def get_market_data():
    url = 'https://api.binance.com/api/v3/ticker/price'
    async with aiohttp.ClientSession() as session:
        async with session.request(method="GET",
                                   url=url) as resp:
            json_content = await resp.json()
            if json_content is not None and resp.status == 200:
                return json_content[0]

async def ex_limitorder(symbol, side, quantity, price):
    trade_url = 'https://api.binance.com/api/v3/order'
    api_header = {'X-MBX-APIKEY': APIKEY}
    params = create_signed_params(symbol, side, quantity, price)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=trade_url, headers=api_header, params=params) as resp:
                json_res = await resp.json()
                if json_res is not None:
                    return {'content': json_res, 'status_code': resp.status, 'params': params}
    except Exception as err:
        print(err)


async def tests():
    order_latency = []
    delete_latency = []
    for i in range(1, 61):
        await asyncio.sleep(5)

        now = time.time()
        print(await ex_limitorder('XRPUSDT', 'BUY', '100', '0.199'))
        order_latency.append(time.time() - now)

        await asyncio.sleep(.2)

        now = time.time()
        print(await cancel_orders('XRPUSDT'))
        delete_latency.append(time.time() - now)
    return {
        'order_latency': order_latency,
        'delete_latency': delete_latency
    }



async def main():
    # try:
    #     print(await cancel_orders('XRPUSDT'))
    # except Exception as err:
    #     print(err)
    method = input("Balance, Market or order? ").upper()
    try:
        if method == 'B':
            now = time.time()
            balance = await get_balance('USDT')
            print(time.time() - now)
            print(balance)
        elif method == 'M':
            now = time.time()
            mdata = await get_market_data()
            print(time.time() - now)
            print(mdata)
        elif method == 'O':
            latency_dict = await tests()
            print('Order latency average: {}\nDelete latency average: {}'.format(mean(latency_dict['order_latency']), mean(latency_dict['delete_latency'])))
    except Exception as err:
        print(err)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
