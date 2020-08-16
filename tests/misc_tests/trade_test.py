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
stepSizes = {}

### Helper functions ###
def round_lot_precision(symbol, number):
    stepSize = stepSizes[symbol.upper()]
    precision = int(round(-math.log(stepSize, 10), 0))
    factor = 10 ** precision
    return math.floor(number * factor) / factor

def round_quote_precision(quantity):
    factor = 10 ** 8
    return math.floor(quantity * factor) / factor

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

    # if side == 'BUY':
    #     query_string = 'symbol={}&side={}&type={}&quoteOrderQty={}&recvWindow={}&timestamp={}'.format(symbol, side, type, quantity, recvWindow, timestamp)
    #     signature = hmac.new(bytes(SECRETKEY, 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
    #     return {
    #         'symbol': symbol,
    #         'side': side,
    #         'type': type,
    #         'quoteOrderQty': quantity,
    #         'recvWindow': recvWindow,
    #         'timestamp': timestamp,
    #         'signature': signature
    #     }
    # else: # SELL
    #     # quantity = round_lot_precision(symbol, quantity)
    #     query_string = 'symbol={}&side={}&type={}&quantity={}&recvWindow={}&timestamp={}'.format(symbol, side, type, quantity, recvWindow, timestamp)
    #     signature = hmac.new(bytes(APIKEY, 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
    #     return {
    #         'symbol': symbol,
    #         'side': side,
    #         'type': type,
    #         'quantity': quantity,
    #         'recvWindow': recvWindow,
    #         'timestamp': timestamp,
    #         'signature': signature
    #     }

async def get_stepsizes():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.binance.com/api/v3/exchangeInfo') as resp:
            json_res = await resp.json()
            if json_res is not None:
                symbolsInfo = json_res['symbols']
                symbolsInfo = [x for x in symbolsInfo if x['symbol'].lower() in PAIRS]
                return {
                    symbol['symbol']: float(symbol['filters'][2]['stepSize'])
                    for symbol in symbolsInfo
                }

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
                return round_quote_precision([float(x['free']) for x in balances if x['asset'] == quote][0])

async def ex_trade(pair, side, quantity):
    trade_url = 'https://api.binance.com/api/v3/order'
    api_header = {'X-MBX-APIKEY': APIKEY}
    params = create_signed_params(pair, side, quantity)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=trade_url, headers=api_header, params=params) as resp:
                json_res = await resp.json()
                if json_res is not None:
                    if resp.status != 200:
                        if json_res['code'] == -2010:
                            print("This is where recursion should happen")
                        else:
                            print('This is some other type of error code')
                    else:
                        print("The trade was successful. No recursion")
                # print(resp)
                # print(resp.status)
                # print(json_res)
                # if json_res is not None:
                #     if 'status' not in json_res.keys():
                #         if json_res['code'] == -2010:
                #             logger.info('Trade failed. Insufficient Funds. Recursion yay')
                #             await ex_trade(pair, side, quantity * 0.999)
                #     else:
                #         return {'content': json_res, 'status_code': resp.status, 'params': params}
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def ex_arb(arb, is_regular):
    global is_trading
    global balance
    is_trading = True
    pairs = ['BTCUSDT', arb + 'BTC', arb + 'USDT'] if is_regular else [arb + 'USDT', arb + 'BTC', 'BTCUSDT']
    balances_hash = [str(balance), 0, 0]

    for i, pair in enumerate(pairs):
        if i == 0:
            trade_response = await ex_trade(pair, 'BUY', balances_hash[0])
        elif i == 1:
            trade_response = await ex_trade(pair, 'BUY', balances_hash[1]) if is_regular else await ex_trade(pair, 'SELL', balances_hash[1])
        elif i == 2:
            trade_response = await ex_trade(pair, 'SELL', balances_hash[2])
        log_msg = '{} params : '.format(pair) + str(trade_response['params']) + ' | trade response: ' + str(trade_response['content'])
        logger.info(log_msg)
        if trade_response['status_code'] == 200:
            if i < 2:
                if is_regular == False and pair[-3:] == 'BTC':
                    balances_hash[i + 1] = str(round_lot_precision(pairs[i + 1], float(trade_response['content']['cummulativeQuoteQty'])) * 0.999)
                else:
                    balances_hash[i + 1] = str(round_lot_precision(pairs[i + 1], float(trade_response['content']['executedQty'])) * 0.999)
            else:
                balance = await get_balance('USDT')
                # print(balance)
                # balance = trade_response['content']['cummulativeQuoteQty']
                logger.info('Trades for {} arb were successful'.format(arb))
                is_trading = False
                # print(balance)
                sys.exit()
        else:
            logger.info('Status code error: {}'.format(trade_response['status_code']))
            is_trading = False
            sys.exit()
            break

async def main():
    global balance
    balance = await get_balance('USDT')
    print(balance)

    # pair = input('Pair: ').upper()
    # side = input('Side: ').upper()
    # quantity = str(round_quote_precision(float(input('Quantity: '))))
    # await ex_trade(pair, side, quantity)

    await ex_trade('BTCUSDT', 'BUY', 100)

    # arb = input('Arb: ').upper()
    # is_regular = input('is_regular: ')
    # await ex_arb(arb, is_regular)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
