import json
import asyncio
import websockets
import aiohttp
import requests
import numpy as np
import logging
import traceback as tb
import helper_test as helper
import random
import time
import sys
import os
from datetime import datetime
from statistics import mean as fmean

logger = logging.getLogger('tri_arb_binance')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logHandler = logging.FileHandler('tri_arb_binance.log', mode='a')
# logHandler = logging.StreamHandler()
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# balances = [1_000, 10_000, 25_000, 50_00]
balances = [1_000]
APIKEY = str(os.environ["BIN_API"])
SECRETKEY = str(os.environ["BIN_SECRET"])

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
    ,'bnb'
    ,'ada'
    ,'vet'
    # ,'link'
    ,'zil'
    ,'neo'
    ,'xlm'
    ,'zec'
    # ,'dash'
]
SIDES = [
    'a',
    'b'
]
PAIRS = []
for arb in ARBS:
    PAIRS.append(arb + 'usdt')
    PAIRS.append(arb + 'btc')
PAIRS.insert(0, 'btcusdt')

STREAMS = []
for pair in PAIRS:
    STREAMS.append(pair + '@depth@100ms')

btc_book = {
    'orderbook': {
        'lastUpdateId': 0,
        'a': np.array([[np.nan, np.nan]]),
        'b': np.array([[np.nan, np.nan]])
    },
    'weighted_prices': {
        'regular': 0,
        'reverse': 0
    },
    'amount_if_bought': 0
}
arbitrage_book = {
    arb: {
        'orderbooks': {
            pair: {
                'lastUpdateId': 0,
                'a': np.array([[np.nan, np.nan]]),
                'b': np.array([[np.nan, np.nan]])
            }
            for pair in PAIRS if pair[:3] == arb
        },
        'regular': { ### Regular arbitrage order: buy BTC/USD, buy ALT/BTC and sell ALT/USD. For buys, we calculate weighted price on the "ask" side ###
            'weighted_prices': {
                pair: 0
                for pair in PAIRS if pair[:3] == arb # or pair == 'BTCUSD'
            },
            'triangle_values': []
        },
        'reverse': { ### Reverse arbitrage order: sell BTC/USD, sell ALT/BTC and buy ALT/USD. For sells, we consume the "bid" side of the orderbook ###
            'weighted_prices': {
                pair: 0
                for pair in PAIRS if pair[:3] == arb # or pair == 'BTCUSD'
            },
            'triangle_values': [],
            'amount_if_bought': 0
        }
    }
    for arb in ARBS
}
threshold_keep = {
    arb: {
        'regular': [],
        'reverse': []
    }
    for arb in ARBS
}
build_list = []

symbolsInfo = requests.get('https://api.binance.com/api/v3/exchangeInfo').json()['symbols']
symbolsInfo = [x for x in symbolsInfo if x['symbol'].lower() in PAIRS]
stepSizes = {
    symbol['symbol']: float(symbol['filters'][2]['stepSize'])
    for symbol in symbolsInfo
}
# print(stepSizes)

trade_url = 'https://api.binance.com/api/v3/order'
api_header = {'X-MBX-APIKEY': str(os.environ["BIN_API"])}

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
    recvWindow = 10_000
    timestamp = int(round(time.time() * 1000))
    type = 'MARKET'
    if side == 'BUY':
        query_string = 'symbol={}&side={}&type={}&quoteOrderQty={}&recvWindow={}&timestamp={}'.format(symbol, side, type, quantity, recvWindow, timestamp)
        signature = hmac.new(bytes(os.environ["BIN_SECRET"], 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
        return {
            'symbol': symbol,
            'side': side,
            'type': type,
            'quoteOrderQty': quantity,
            'recvWindow': recvWindow,
            'timestamp': timestamp,
            'signature': signature
        }
    else: # SELL
        quantity = round_lot_precision(symbol, quantity)
        query_string = 'symbol={}&side={}&type={}&quantity={}&recvWindow={}&timestamp={}'.format(symbol, side, type, quantity, recvWindow, timestamp)
        signature = hmac.new(bytes(os.environ["BIN_SECRET"], 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
        return {
            'symbol': symbol,
            'side': side,
            'type': type,
            'quantity': quantity,
            'recvWindow': recvWindow,
            'timestamp': timestamp,
            'signature': signature
        }

def getWeightedPrice(orders, balance, reverse=False):
    weightedPrices = []
    for bal in balance:
        volume = 0
        price = 0
        wp = 0
        remainder = 0
        if reverse:
            for order in orders:
                volume += order[1]
                wp += order[0] * (order[1] / bal)
                if volume >= bal:
                    remainder = volume - bal
                    wp -= order[0] * (remainder / bal)
                    weightedPrices.append(wp)
                    break
        else:
            for order in orders:
                volume += order[0] * order[1]
                wp += order[0] * ((order[0] * order[1]) / bal)
                if volume >= bal:
                    remainder = volume - bal
                    wp -= order[0] * (remainder / bal)
                    weightedPrices.append(wp)
                    break
    return np.array(weightedPrices, np.float64)







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
            try:
                sub_coros = [
                    buildBook(pair)
                    for pair in PAIRS
                ]
                await asyncio.wait(sub_coros)
            except Exception:
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

async def fullBookTimer():
    global build_list
    while 1:
        await asyncio.sleep(1)
        try:
            check = all(item in build_list for item in PAIRS)
            if check:
                logger.info('Awaiting populateArb and arb_monitor')
                await asyncio.wait([populateArb(), arb_monitor(), stillAlive()])
                # await asyncio.wait([populateArb(), arb_monitor(), stillAlive(), printBook()])
            else:
                continue
        except Exception as err:
            logger.exception(err)
            sys.exit()
        else:
            continue


async def buildBook(pair):
    arb = pair[:3]
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.binance.com/api/v3/depth?symbol={}&limit=500'.format(pair.upper())) as response:
            if response.status == 200:
                json_snapshot = await response.json()
                if pair == 'btcusdt':
                    btc_book['orderbook']['lastUpdateId'] = json_snapshot['lastUpdateId']
                    btc_book['orderbook']['a'] = np.array(json_snapshot['asks'], np.float64)
                    btc_book['orderbook']['b'] = np.array(json_snapshot['bids'], np.float64)
                    build_list.append(pair)
                    logger.info('Filled btc_book successfully')
                else:
                    arbitrage_book[arb]['orderbooks'][pair]['lastUpdateId'] = json_snapshot['lastUpdateId']
                    arbitrage_book[arb]['orderbooks'][pair]['a'] = np.array(json_snapshot['asks'], np.float64)
                    arbitrage_book[arb]['orderbooks'][pair]['b'] = np.array(json_snapshot['bids'], np.float64)
                    build_list.append(pair)
                    # print('Filled', pair, 'orderbook successfully')
                    log_msq = 'Filled ' + pair + ' orderbook successfully'
                    logger.info(log_msq)
            else:
                logger.info('Failed to get snapshot response. Here is the http-response status code', response.status)
                sys.exit()
                # print('Failed to get snapshot response. Here is the http-response status code', response.status)


async def updateBook(res):
    global arbitrage_book
    global btc_book
    try:
        json_res = json.loads(res)
        if 'stream' in json_res.keys():
            pair = json_res['data']['s'].lower()
            arb = pair[:3]
            firstUpdateId = json_res["data"]["U"]
            finalUpdateId = json_res["data"]["u"]

            if pair == 'btcusdt':
                if finalUpdateId > btc_book['orderbook']['lastUpdateId']: ### See Binance API documentation for details on this condition ###
                    for side in SIDES:
                        uos = np.array(json_res["data"][side], np.float64)
                        btc_ob = btc_book['orderbook'][side]
                        if uos.size == 0:
                            continue
                        else:
                            not_in_index = np.in1d(uos[:,0], btc_ob[:,0], invert=True)
                            ss_index = np.searchsorted(btc_ob[:,0], uos[not_in_index,0]) if side == 'a' else np.searchsorted(-btc_ob[:,0], -uos[not_in_index,0])
                            btc_ob = np.insert(btc_ob, ss_index, uos[not_in_index], axis=0)

                            inter, orders_ind, updateorders_ind = np.intersect1d(btc_ob[:,0], uos[:,0], return_indices=True)
                            btc_ob[orders_ind] = uos[updateorders_ind]

                            delete_ind = np.where(btc_ob == 0)[0]
                            btc_ob = np.delete(btc_ob, delete_ind, axis=0)
                            btc_book['orderbook'][side] = btc_ob
                else:
                    pass
            else:
                if finalUpdateId > arbitrage_book[arb]['orderbooks'][pair]['lastUpdateId']:
                    for side in SIDES:
                        uos = np.array(json_res["data"][side], np.float64)
                        arb_ob = arbitrage_book[arb]['orderbooks'][pair][side]
                        if uos.size == 0:
                            continue
                        else:
                            not_in_index = np.in1d(uos[:,0], arb_ob[:,0], invert=True)
                            ss_index = np.searchsorted(arb_ob[:,0], uos[not_in_index,0]) if side == 'a' else np.searchsorted(-arb_ob[:,0], -uos[not_in_index,0])
                            arb_ob = np.insert(arb_ob, ss_index, uos[not_in_index], axis=0)

                            inter, orders_ind, updateorders_ind = np.intersect1d(arb_ob[:,0], uos[:,0], return_indices=True)
                            arb_ob[orders_ind] = uos[updateorders_ind]

                            delete_ind = np.where(arb_ob == 0)[0]
                            arb_ob = np.delete(arb_ob, delete_ind, axis=0)
                            arbitrage_book[arb]['orderbooks'][pair][side] = arb_ob
                else:
                    pass
        else:
            pass
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def populateArb():
    global arbitrage_book
    global btc_book
    global balances
    threshold_values = {
        arb: {
            type: list()
            for type in ['regular', 'reverse']
        }
        for arb in ARBS
    }
    threshold_dict = {
        arb: {
            type: dict()
            for type in ['regular', 'reverse']
        }
        for arb in ARBS
    }

    while 1:
        await asyncio.sleep(0.005)
        try:
            btc_book['weighted_prices']['regular'] = helper.getWeightedPrice(btc_book['orderbook']['a'], balances, reverse=False)
            btc_book['weighted_prices']['reverse'] = helper.getWeightedPrice(btc_book['orderbook']['b'], balances, reverse=False)
            btc_book['amount_if_bought'] = np.divide(balances, btc_book['weighted_prices']['regular'])

            for arb in ARBS:
                pair_iterator = [pair for pair in PAIRS if pair[:3] == arb]
                for pair in sorted(pair_iterator, reverse=True):
                    arb_ob = arbitrage_book[arb]['orderbooks'][pair]
                    if pair[-4:] == 'usdt':
                        arbitrage_book[arb]['regular']['weighted_prices'][pair] = helper.getWeightedPrice(arb_ob['b'], balances, reverse=False)
                        arbitrage_book[arb]['reverse']['weighted_prices'][pair] = helper.getWeightedPrice(arb_ob['a'], balances, reverse=False)
                        arbitrage_book[arb]['reverse']['amount_if_bought'] = np.divide(balances, arbitrage_book[arb]['reverse']['weighted_prices'][pair])
                    else:
                        arbitrage_book[arb]['regular']['weighted_prices'][pair] = helper.getWeightedPrice(arb_ob['a'], btc_book['amount_if_bought'], reverse=False)
                        arbitrage_book[arb]['reverse']['weighted_prices'][pair] = helper.getWeightedPrice(arb_ob['b'], arbitrage_book[arb]['reverse']['amount_if_bought'], reverse=True)

                regular_arb_price = np.multiply(btc_book['weighted_prices']['regular'], arbitrage_book[arb]['regular']['weighted_prices'][arb + 'btc'])
                reverse_arb_price = np.divide(arbitrage_book[arb]['reverse']['weighted_prices'][arb + 'usdt'], arbitrage_book[arb]['reverse']['weighted_prices'][arb + 'btc'])
                arbitrage_book[arb]['regular']['triangle_values'] = np.divide(np.subtract(arbitrage_book[arb]['regular']['weighted_prices'][arb + 'usdt'], regular_arb_price), regular_arb_price)
                arbitrage_book[arb]['reverse']['triangle_values'] = np.divide(np.subtract(btc_book['weighted_prices']['reverse'], reverse_arb_price), reverse_arb_price)
        except Exception as err:
            logger.exception(err)
            sys.exit()

async def arb_monitor():
    global arbitrage_book
    global balances
    while 1:
        await asyncio.sleep(0.005)
        for arb in ARBS:
            for type in ['regular', 'reverse']:
                if arbitrage_book[arb][type]['triangle_values'][0] > 0:
                    logger.info('Executing the arb trade for {} {}. Arb value is {}'.format(type, arb, arbitrage_book[arb][type]['triangle_values'][0]))
                    # await asyncio.wait([ex_arb(arb, True if type == 'regular' else False)])

def ex_trade(pair, side, quantity):
    params = create_signed_params(pair, side, quantity)
    print(params)
    r = requests.post(trade_url, headers=api_header, params=params)
    return {'content': r.json(), 'status_code': r.status_code, 'params': params}

async def ex_arb(arb, is_regular):
    pairs = ['BTCUSDT', arb + 'BTC', arb + 'USDT'] if is_regular else [arb + 'USDT', arb + 'BTC', 'BTCUSDT']
    balances_hash = [round_quote_precision(get_balances('USDT')), 0, 0]

    for i, pair in enumerate(pairs):
        if i == 0:
            trade_response = ex_trade(pair, 'BUY', balances_hash[0])
        elif i == 1:
            trade_response = ex_trade(pair, 'BUY', balances_hash[1]) if is_regular else ex_trade(pair, 'SELL', balances_hash[1])
        elif i == 2:
            trade_response = ex_trade(pair, 'SELL', balances_hash[2])
        log_msg = '{} params : '.format(pair) + str(trade_response['params']) + ' | trade response: ' + str(trade_response['content'])
        logger.info(log_msg)
        if trade_response['status_code'] == 200:
            if i < 2:
                balances_hash[i + 1] = round_lot_precision(pairs[i + 1], float(trade_response['content']['executedQty']) * 0.999)
                continue
            else:
                log_msg = 'Trades for {} were successful'.format(arb)
                logger.info(log_msg)
        else:
            logger.info('Status code error: {}'.format(trade_response['status_code']))
            break



async def stillAlive():
    global arbitrage_book
    await asyncio.sleep(10)
    check_list = []
    while 1:
        await asyncio.sleep(10)
        check_list.append(arbitrage_book['eth']['regular']['triangle_values'][0])
        check_len = len(check_list)
        if check_len > 2:
            check_list = check_list[-3:]
            logger.info(check_list)
            if check_list[2] == check_list[1] and check_list[2] == check_list[1]:
                logger.info('Program still running but stream stopped')
                sys.exit()
            else:
                continue
        else:
            continue

async def printBook():
    global arbitrage_book
    global btc_book
    await asyncio.sleep(10)
    while 1:
        print(btc_book['orderbook']['a'][0:3])
        await asyncio.sleep(10)

async def main():
    coroutines = []
    coroutines.append(subscribe())
    coroutines.append(fullBookTimer())
    await asyncio.wait(coroutines)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
