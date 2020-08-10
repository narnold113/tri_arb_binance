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
is_trading = False
balance = 0

### Helper functions ###
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
                    # print(json_content)
                    # balances = [x for x in json_content['balances'] if float(x['free']) > 0]
                    # print(balances)
                    bal_dict = {
                        item['asset']: {
                            'quantity': float(item['free']),
                            'volume': 0
                        }
                        for item in json_content['balances'] if float(item['free']) > 0
                    }
                    return bal_dict
                    # return [float(x['free']) for x in balances if float(x['free']) > 0][0]
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def get_vol_dict():
    bal_dict = await get_balances()
    ticker_info = requests.get('https://api.binance.com/api/v3/ticker/24hr').json()
    for coin in bal_dict:
        if coin != 'USDT':
            pair = coin.upper() + 'USDT'
            try:
                price = [x['lastPrice'] for x in ticker_info if x['symbol'] == pair][0]
            except:
                continue
            # print(price)
            bal_dict[coin]['volume'] = float(price) * bal_dict[coin]['quantity']
        else:
            bal_dict[coin]['volume'] = bal_dict[coin]['quantity']
    return dict(sorted(bal_dict.items(), key=lambda item: item[1]['volume'], reverse=True))

async def find_high_balances():
    vol_dict = await get_vol_dict()
    

async def main():
    vol_dict = await get_vol_dict()
    print(vol_dict)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
