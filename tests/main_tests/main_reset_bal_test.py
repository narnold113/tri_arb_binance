import asyncio
import websockets
import requests
import aiohttp
import numpy as np
import json
import logging
import traceback as tb
import time
import sys
import os
import hmac
import hashlib
import math
from datetime import datetime

logger = logging.getLogger('tri_arb_binance')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logHandler = logging.FileHandler('trade_testing.log', mode='a')
logHandler = logging.StreamHandler()
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

APIKEY = str(os.environ["BIN_API"])
SECRETKEY = str(os.environ["BIN_SECRET"])
trade_url = 'https://api.binance.com/api/v3/order'
api_header = {'X-MBX-APIKEY': APIKEY}
is_trading = False
balance = 0

### Helper functions ###
def create_signed_params(symbol, side, quantity):
    timestamp = int(round(time.time() * 1000))
    query_string = 'symbol={}&side={}&type={}&quoteOrderQty={}&recvWindow={}&timestamp={}'.format(symbol, side, 'MARKET', quantity, 10_000, timestamp)
    signature = hmac.new(bytes(SECRETKEY, 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
    return {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quoteOrderQty': quantity,
        'recvWindow': 10_000,
        'timestamp': timestamp,
        'signature': signature
    }

def round_quote_precision(quantity):
    factor = 10 ** 8
    return math.floor(quantity * factor) / factor

async def get_balances():
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
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method="GET",
                                       url=url,
                                       headers=header,
                                       params=params) as resp:
                json_content = await resp.json()
                if json_content is not None and resp.status == 200:
                    bal_dict = {
                        item['asset']: {
                            'quantity': float(item['free']),
                            'volume': 0
                        }
                        for item in json_content['balances'] if float(item['free']) > 0
                    }
                    return bal_dict
    except Exception as err:
        logger.exception(err)
        sys.exit()

# async def find_high_balances():
#     bal_dict = await get_balances()
#     ticker_info = requests.get('https://api.binance.com/api/v3/ticker/24hr').json()
#     for coin in bal_dict:
#         if coin != 'USDT':
#             pair = coin.upper() + 'USDT'
#             try:
#                 price = [x['lastPrice'] for x in ticker_info if x['symbol'] == pair][0]
#             except:
#                 continue
#             bal_dict[coin]['volume'] = float(price) * bal_dict[coin]['quantity']
#         else:
#             bal_dict[coin]['volume'] = bal_dict[coin]['quantity']
#     vol_dict = dict(sorted(bal_dict.items(), key=lambda item: item[1]['volume'], reverse=True))
#     high_bal_dict = {}
#     for item in vol_dict:
#         if item not in ['USDT', 'BNB'] and vol_dict[item]['volume'] > 10.1:
#             high_bal_dict[item] = vol_dict[item]['volume']
#     return high_bal_dict

async def trade_high_balances():
    bal_dict = await get_balances()
    ticker_info = requests.get('https://api.binance.com/api/v3/ticker/24hr').json()
    for coin in bal_dict:
        if coin != 'USDT':
            pair = coin.upper() + 'USDT'
            try:
                price = [x['lastPrice'] for x in ticker_info if x['symbol'] == pair][0]
            except:
                continue
            bal_dict[coin]['volume'] = float(price) * bal_dict[coin]['quantity']
        else:
            bal_dict[coin]['volume'] = bal_dict[coin]['quantity']
    vol_dict = dict(sorted(bal_dict.items(), key=lambda item: item[1]['volume'], reverse=True))

    high_bal_dict = {}
    for item in vol_dict:
        if item not in ['USDT', 'BNB'] and vol_dict[item]['volume'] > 10.1:
            high_bal_dict[item] = vol_dict[item]['volume']

    print(high_bal_dict)
    if high_bal_dict:
        for item in high_bal_dict:
            try:
                params = create_signed_params(item + 'USDT', 'SELL', round_quote_precision(high_bal_dict[item]))
                res = requests.post(url=trade_url, headers=api_header, params=params)
                logger.info(res.json())
                if res.status_code == 200:
                    print('{} balance converted to USDT'.format(item))
            except Exception as err:
                print(err)
        return 'At least one crypto balance was over $10'
    else:
        return 'No high balances'


async def main():
    print(await trade_high_balances())
    # return await trade_high_balances()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
