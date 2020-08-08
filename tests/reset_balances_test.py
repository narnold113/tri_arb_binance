import asyncio
import websockets
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
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method="GET",
                                       url=url,
                                       headers=header,
                                       params=params) as resp:
                json_content = await resp.json()
                if json_content is not None and resp.status == 200:
                    print(json_content)
                    balances = [x for x in json_content['balances'] if float(x['free']) != 0]
                    print(balances)
                    # return [float(x['free']) for x in balances if float(x['free']) > 0][0]
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def main():
    global balance
    balance = await get_balance('USDT')
    print(balance)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
