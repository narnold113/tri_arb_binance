import aiohttp
import requests
import asyncio
import hmac
import hashlib
import os
import sys
from statistics import mean
import time
APIKEY = str(os.environ["BIN_API"])
SECRETKEY = str(os.environ["BIN_SECRET"])
trade_url = 'https://api.binance.com/api/v3/order'
api_header = {'X-MBX-APIKEY': APIKEY}

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

def test_order(pair, side, quantity, price):
    global trade_url
    global api_header
    params = create_signed_params(pair, side, quantity, price)
    try:
        res = requests.post(url=trade_url, headers=api_header, params=params)
        # print(res.status_code)
        if res.status_code == 200:
            return res.json()
    except Exception as err:
        print(err)

def cancel_orders(symbol):
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
        res = requests.delete(url, headers=header, params=params)
        if res.status_code == 200:
            return res.json()
    except Exception as err:
        print(err)

def tests():
    order_latency = []
    delete_latency = []
    for i in range(1, 11):
        time.sleep(2)

        now = time.time()
        print(test_order('XRPUSDT', 'buy', '50', '0.2'))
        order_latency.append(time.time() - now)

        time.sleep(2)

        now = time.time()
        print(cancel_orders('XRPUSDT'))
        delete_latency.append(time.time() - now)
    return {
        'order_latency': {
            'list': order_latency,
            'average': mean(order_latency)
        },
        'delete_latency': {
            'list': delete_latency,
            'average': mean(delete_latency)
        }
    }


def requests_main():
    print(tests())






















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

async def aiohttp_cancel_orders(symbol):
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

async def aiohttp_tests():
    order_latency = []
    delete_latency = []
    for i in range(1, 11):
        await asyncio.sleep(1)

        now = time.time()
        print(await ex_limitorder('XRPUSDT', 'BUY', '50', '0.2'))
        order_latency.append(time.time() - now)

        await asyncio.sleep(1)

        now = time.time()
        print(await aiohttp_cancel_orders('XRPUSDT'))
        delete_latency.append(time.time() - now)
    return {
        'order_latency': {
            'list': order_latency,
            'average': mean(order_latency)
        },
        'delete_latency': {
            'list': delete_latency,
            'average': mean(delete_latency)
        }
    }

async def aiohttp_main():
    print(await aiohttp_tests())







if __name__ == '__main__':
    type = input("Requests or Aiohttp (r or a)? ")
    if type.lower() == 'r':
        print("performing tests with requests lib")
        requests_main()
    else:
        print("performing tests with aiohttp lib")
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(aiohttp_main())
        except:
            pass
        finally:
            loop.close()
