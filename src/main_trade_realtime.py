import asyncio
import websockets
import aiohttp
import requests
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
import get_arbs
from datetime import datetime

logger = logging.getLogger('tri_arb_binance')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logHandler = logging.FileHandler('tri_arb_binance.log', mode='a')
# logHandler = logging.StreamHandler()
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

APIKEY = str(os.environ["BIN_API"])
SECRETKEY = str(os.environ["BIN_SECRET"])
trade_url = 'https://api.binance.com/api/v3/order'
api_header = {'X-MBX-APIKEY': APIKEY}
is_trading = False
balance = 0

# ARBS = ['eth']
ARBS = get_arbs.get_arbs()
PAIRS = []
for arb in ARBS:
    PAIRS.append(arb + 'usdt')
    PAIRS.append(arb + 'btc')
PAIRS.insert(0, 'btcusdt')
STREAMS = []
for pair in PAIRS:
    STREAMS.append(pair + '@bookTicker')
SIDES = [
    'a',
    'b'
]

btc_book = [[0,0,0], [0,0,0]] # [price, quantity, volume] Bid side is in first array
arbitrage_book = {
    arb: {
        pair: [[0,0,0], [0,0,0]] # [price, quantity, volume] Bid side is in first array
        for pair in PAIRS if pair[0:len(arb)] == arb
    }
    for arb in ARBS
}
for arb in ARBS:
    arbitrage_book[arb]['triangles'] = [[0,0], [0,0]] # [value, volume] Regular is in first array



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




async def updateBook(payload):
    global arbitrage_book
    global btc_book
    try:
        json_payload = json.loads(payload)
        if 'stream' in json_payload.keys():
            pair = json_payload['data']['s'].lower()
            if pair[-3:] == 'btc':
                arb = pair[0:len(pair) - 3]
            elif pair[-4:] == 'usdt':
                arb = pair[0:len(pair) - 4]

            if pair == 'btcusdt':
                btc_book[0][0] = float(json_payload['data']['b'])
                btc_book[0][1] = float(json_payload['data']['B'])
                btc_book[0][2] = btc_book[0][0] * btc_book[0][1]

                btc_book[1][0] = float(json_payload['data']['a'])
                btc_book[1][1] = float(json_payload['data']['A'])
                btc_book[1][2] = btc_book[1][0] * btc_book[1][1]
            else:
                arbitrage_book[arb][pair][0][0] = float(json_payload['data']['b'])
                arbitrage_book[arb][pair][0][1] = float(json_payload['data']['B'])
                arbitrage_book[arb][pair][0][2] = arbitrage_book[arb][pair][0][0] * arbitrage_book[arb][pair][0][1]

                arbitrage_book[arb][pair][1][0] = float(json_payload['data']['a'])
                arbitrage_book[arb][pair][1][1] = float(json_payload['data']['A'])
                arbitrage_book[arb][pair][1][2] = arbitrage_book[arb][pair][1][0] * arbitrage_book[arb][pair][1][1]
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def populateArb():
    global arbitrage_book
    global btc_book
    global is_trading
    global balance
    await asyncio.sleep(10)
    while 1:
        try:
            await asyncio.sleep(0.001)
            reg_volume_hash = []
            rev_volume_hash = []
            for arb in ARBS:
                pair_iterator = [pair for pair in PAIRS if pair[:len(arb)] == arb]
                for pair in sorted(pair_iterator, reverse=True):
                    pass
                reg_synth_price = np.multiply(btc_book[1][0], arbitrage_book[arb][arb + 'btc'][1][0])
                arbitrage_book[arb]['triangles'][0][0] = np.divide(np.subtract(arbitrage_book[arb][arb + 'usdt'][0][0], reg_synth_price), reg_synth_price)
                reg_volume_hash.append(btc_book[1][2])
                reg_volume_hash.append(arbitrage_book[arb][arb + 'btc'][1][2] * btc_book[1][0])
                reg_volume_hash.append(arbitrage_book[arb][arb + 'usdt'][0][2])
                arbitrage_book[arb]['triangles'][0][1] = min(reg_volume_hash)

                rev_synth_price = np.divide(arbitrage_book[arb][arb + 'usdt'][1][0], arbitrage_book[arb][arb + 'btc'][0][0])
                arbitrage_book[arb]['triangles'][1][0] = np.divide(np.subtract(btc_book[0][0], rev_synth_price), rev_synth_price)
                rev_volume_hash.append(btc_book[0][2])
                rev_volume_hash.append(arbitrage_book[arb][arb + 'btc'][0][2] * btc_book[0][0])
                rev_volume_hash.append(arbitrage_book[arb][arb + 'usdt'][1][2])
                arbitrage_book[arb]['triangles'][1][1] = min(rev_volume_hash)

                if arbitrage_book[arb]['triangles'][0][0] > 0.01 and is_trading == False: # Regular
                    if arbitrage_book[arb]['triangles'][0][1] >= 11:
                        logger.info('Executing regular {}. Arb value is {} | Weighted Prices: {}'.format(arb, arbitrage_book[arb]['triangles'][0][0], [btc_book[1][0], arbitrage_book[arb][arb + 'btc'][1][0], arbitrage_book[arb][arb + 'usdt'][0][0]]))
                        await ex_arb(
                            arb.upper(),
                            arbitrage_book[arb]['triangles'][0][1] if arbitrage_book[arb]['triangles'][0][1] <= balance else balance,
                            False,
                            [
                                btc_book[1][0],
                                arbitrage_book[arb][arb + 'btc'][1][0],
                                arbitrage_book[arb][arb + 'usdt'][0][0]
                            ]
                        )
                elif arbitrage_book[arb]['triangles'][1][0] > 0.01 and is_trading == False: # Reverse
                    if arbitrage_book[arb]['triangles'][1][1] >= 11:
                        logger.info('Executing reverse {}. Arb value is {} | Weighted Prices: {}'.format(arb, arbitrage_book[arb]['triangles'][1][0], [btc_book[0][0], arbitrage_book[arb][arb + 'btc'][0][0], arbitrage_book[arb][arb + 'usdt'][1][0]]))
                        await ex_arb(
                            arb.upper(),
                            arbitrage_book[arb]['triangles'][1][1] if arbitrage_book[arb]['triangles'][1][1] <= balance else balance,
                            True,
                            [
                                btc_book[0][0],
                                arbitrage_book[arb][arb + 'btc'][0][0],
                                arbitrage_book[arb][arb + 'usdt'][1][0]
                            ]
                        )
        except Exception as err:
            logger.exception(err)
            sys.exit()

async def ex_trade(pair, side, quantity, recvWindow):
    global trade_url
    global api_header
    params = create_signed_params(pair, side, quantity, recvWindow)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=trade_url, headers=api_header, params=params) as resp:
                json_res = await resp.json()
                if json_res is not None:
                    if resp.status == 200:
                        return {'content': json_res, 'params': params}
                    else:
                        if json_res['code'] == -2010:
                            logger.info('Trade failed. Insufficient Funds. Recursion yay')
                            return await ex_trade(pair, side, str(round_quote_precision(float(quantity) * 0.999)), recvWindow)
                        else:
                            logger.info('Some other type of error occurred: {}'.format(json_res))
                            sys.exit()
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def ex_arb(arb, bal, is_regular, weighted_prices):
    global is_trading
    global balance
    global arbitrage_book
    global btc_book
    is_trading = True
    quantity_hash = [str(bal), 0, 0]
    leakage_hash = {}
    slippage_hash = {}

    for i, pair in enumerate(['BTCUSDT', arb + 'BTC', arb + 'USDT'] if is_regular else [arb + 'USDT', arb + 'BTC', 'BTCUSDT']):
        start_time = time.time()
        if i == 0:
            trade_response = await ex_trade(pair, 'BUY', quantity_hash[i], 100)
        elif i == 1:
            trade_response = await ex_trade(pair, 'BUY' if is_regular else 'SELL', quantity_hash[i], 10_000)
        elif i == 2:
            trade_response = await ex_trade(pair, 'SELL', quantity_hash[i], 10_000)
        logger.info('Trade Params: {} | Trade Response: {} | Trade Latency: {}'.format(str(trade_response['params']), str(trade_response['content']), time.time() - start_time))
        try:
            if i == 0:
                if is_regular:
                    quantity_hash[i + 1] = str(round_quote_precision(float(trade_response['content']['executedQty'])))
                    leakage_hash['btc'] = float(trade_response['content']['executedQty'])
                    slippage_hash['BTCUSDT'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[0]) / weighted_prices[0]) * 100, 3)
                else:
                    wp = arbitrage_book[arb.lower()][arb.lower() + 'btc'][0][0]
                    quantity_hash[i + 1] = str(round_quote_precision(float(trade_response['content']['executedQty']) * wp))
                    leakage_hash[arb] = float(trade_response['content']['executedQty'])
                    slippage_hash[arb + 'USDT'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[2]) / weighted_prices[2]) * 100, 3)
                    logger.info('Weighted Price for next quantity hash: {}'.format(wp))
            elif i == 1:
                if is_regular:
                    wp = arbitrage_book[arb.lower()][arb.lower() + 'usdt'][0][0]
                    quantity_hash[i + 1] = str(round_quote_precision(float(trade_response['content']['executedQty']) * wp))
                    leakage_hash['btc'] = leakage_hash['btc'] - float(trade_response['content']['cummulativeQuoteQty'])
                    leakage_hash[arb] = float(trade_response['content']['executedQty'])
                    slippage_hash[arb + 'BTC'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[1]) / weighted_prices[1]) * 100, 3)
                    logger.info('Weighted Price for next quantity hash: {}'.format(wp))
                else:
                    wp = btc_book[0][0]
                    quantity_hash[i + 1] = str(round_quote_precision(float(trade_response['content']['cummulativeQuoteQty']) * wp))
                    leakage_hash[arb] = leakage_hash[arb] - float(trade_response['content']['executedQty'])
                    leakage_hash['btc'] = float(trade_response['content']['cummulativeQuoteQty'])
                    slippage_hash[arb + 'BTC'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[1]) / weighted_prices[1]) * -100, 3)
                    logger.info('Weighted Price for next quantity hash: {}'.format(wp))
            else:
                if is_regular:
                    leakage_hash[arb] = leakage_hash[arb] - float(trade_response['content']['executedQty'])
                    slippage_hash[arb + 'USDT'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[2]) / weighted_prices[2]) * -100, 3)
                else:
                    leakage_hash['btc'] = leakage_hash['btc'] - float(trade_response['content']['executedQty'])
                    slippage_hash['BTCUSDT'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[0]) / weighted_prices[0]) * -100, 3)

                balance = round_quote_precision(float(trade_response['content']['cummulativeQuoteQty']))
                logger.info(
                    str(
                        'Trades for {} arb were successful\n'
                        'USDT balance before: {} and after: {}\n'
                        'BTC Leakage: {} ({} USDT) and {} Leakage: {} ({} USDT)\n'
                        'Slippage Percentages: {}\n'
                    ).format(
                        arb,
                        quantity_hash[0],
                        balance,
                        leakage_hash['btc'],
                        leakage_hash['btc'] * weighted_prices[0],
                        arb, leakage_hash[arb],
                        leakage_hash[arb] * weighted_prices[2],
                        slippage_hash
                    )
                )
                is_trading = False
                # sys.exit()
        except Exception as err:
            logger.exception(err)
            sys.exit()


async def subscribe() -> None:
    url = 'wss://stream.binance.com:9443/stream'
    strParams = '''{"method": "SUBSCRIBE","params": "placeholder","id": 1}'''
    params = json.loads(strParams)
    params['params'] = STREAMS
    try:
        async with websockets.client.connect(url, max_queue=None) as ws:
            try:
                await ws.send(str(params).replace('\'', '"'))
            except Exception as err:
                logger.exception(err)
                sys.exit()
            while 1:
                try:
                    res = await ws.recv()
                    await updateBook(res)
                except Exception as err:
                    logger.exception(err)
                    sys.exit()
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def get_balance(isHigh):
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
                if isHigh:
                    bal_dict = {
                        item['asset']: {
                            'quantity': float(item['free']),
                            'volume': 0
                        }
                        for item in json_content['balances'] if float(item['free']) > 0
                    }
                    return bal_dict
                else:
                    balances = [x for x in json_content['balances'] if float(x['free']) != 0]
                    return round_quote_precision([float(x['free']) for x in balances if x['asset'] == 'USDT'][0])


async def trade_high_balances():
    try:
        bal_dict = await get_balance(True)
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

        if high_bal_dict:
            for item in high_bal_dict:
                try:
                    trade_respone = await ex_trade(item + 'USDT', 'SELL', str(round_quote_precision(high_bal_dict[item])), 10_000)
                    logger.info('Trade Response for high_balance: {}'.format(trade_respone['content']))
                    logger.info('{} balance converted to USDT'.format(item))
                except Exception as err:
                    print(err)
            return 'At least one crypto balance was over $10'
        else:
            return 'No high balances'
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def main():
    global balance
    high_bal = await trade_high_balances()
    logger.info(high_bal)
    balance = await get_balance(False)
    logger.info('USDT Balance: {}'.format(balance))
    if balance < 10:
        logger.info('USDT balance is less than $10')
        sys.exit()
    coroutines = []
    coroutines.append(subscribe())
    coroutines.append(populateArb())
    await asyncio.wait(coroutines)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
