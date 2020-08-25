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
import get_arbs_test as get_arbs
from datetime import datetime

logger = logging.getLogger('tri_arb_binance')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logHandler = logging.FileHandler('tri_arb_binance.log', mode='a')
logHandler = logging.StreamHandler()
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

APIKEY = str(os.environ["BIN_API"])
SECRETKEY = str(os.environ["BIN_SECRET"])
trade_url = 'https://api.binance.com/api/v3/order'
api_header = {'X-MBX-APIKEY': APIKEY}
ARBLIMIT = 0.015
is_trading = False
balance = 0
build_list = []

# ARBS = get_arbs.get_arbs()
ARBS = ['eth']
# ARBS.remove('dai')
logger.info('Number of ARBS: {}'.format(len(ARBS)))
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
    STREAMS.append(pair + '@depth20@100ms')

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
            for pair in PAIRS if pair[0:len(arb)] == arb
        },
        'regular': { ### Regular arbitrage order: buy BTC/USD, buy ALT/BTC and sell ALT/USD. For buys, we calculate weighted price on the "ask" side ###
            'weighted_prices': {
                pair: 0
                for pair in PAIRS if pair[0:len(arb)] == arb # or pair == 'BTCUSD'
            },
            'triangle_values': []
        },
        'reverse': { ### Reverse arbitrage order: sell BTC/USD, sell ALT/BTC and buy ALT/USD. For sells, we consume the "bid" side of the orderbook ###
            'weighted_prices': {
                pair: 0
                for pair in PAIRS if pair[0:len(arb)] == arb # or pair == 'BTCUSD'
            },
            'triangle_values': [],
            'amount_if_bought': 0
        }
    }
    for arb in ARBS
}


### Helper functions ###
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

def getWeightedPrice(orders, balance, reverse=False, isRecursion=False):
    volume = 0
    price = 0
    wp = 0
    if reverse:
        for order in orders:
            volume += order[1]
            wp += order[0] * (order[1] / balance)
            if volume >= balance:
                remainder = volume - balance
                wp -= order[0] * (remainder / balance)
                if isRecursion:
                    return wp
                else:
                    return [wp, volume / balance]
        return [getWeightedPrice(orders, volume, True, True), volume / balance]
    else:
        for order in orders:
            volume += order[0] * order[1]
            wp += order[0] * ((order[0] * order[1]) / balance)
            if volume >= balance:
                remainder = volume - balance
                wp -= order[0] * (remainder / balance)
                if isRecursion:
                    return wp
                else:
                    return [wp, volume / balance]
        return [getWeightedPrice(orders, volume, False, True), volume / balance]







async def subscribe() -> None:
    url = 'wss://stream.binance.com:9443/stream'
    strParams = '''{"method": "SUBSCRIBE","params": "placeholder","id": 1}'''
    params = json.loads(strParams)
    params['params'] = STREAMS
    try:
        async with websockets.client.connect(url, max_queue=None, max_size=None, ping_interval=60) as ws:
            try:
                await ws.send(str(params).replace('\'', '"'))
            except Exception as err:
                logger.exception(err)
                sys.exit()
            # try:
            #     sub_coros = [
            #         buildBook(pair)
            #         for pair in PAIRS
            #     ]
            #     await asyncio.wait(sub_coros)
            # except Exception:
            #     logger.exception(err)
            #     sys.exit()
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

# async def buildBook(pair):
#     if pair[-3:] == 'btc':
#         arb = pair[0:len(pair) - 3]
#     elif pair[-4:] == 'usdt':
#         arb = pair[0:len(pair) - 4]
#     async with aiohttp.ClientSession() as session:
#         async with session.get('https://www.binance.com/api/v3/depth?symbol={}&limit=500'.format(pair.upper())) as response:
#             if response.status == 200:
#                 json_snapshot = await response.json()
#                 if pair == 'btcusdt':
#                     btc_book['orderbook']['lastUpdateId'] = json_snapshot['lastUpdateId']
#                     btc_book['orderbook']['a'] = np.array(json_snapshot['asks'], np.float64)
#                     btc_book['orderbook']['b'] = np.array(json_snapshot['bids'], np.float64)
#                     build_list.append(pair)
#                 else:
#                     arbitrage_book[arb]['orderbooks'][pair]['lastUpdateId'] = json_snapshot['lastUpdateId']
#                     arbitrage_book[arb]['orderbooks'][pair]['a'] = np.array(json_snapshot['asks'], np.float64)
#                     arbitrage_book[arb]['orderbooks'][pair]['b'] = np.array(json_snapshot['bids'], np.float64)
#                     build_list.append(pair)
#             else:
#                 logger.info('Failed to get snapshot response. Here is the http-response status code: {}'.format(response.status))
#                 sys.exit()

async def updateBook(res):
    global arbitrage_book
    global btc_book
    print(res)
    # try:
    #     json_res = json.loads(res)
    #     if 'stream' in json_res.keys():
    #         pair = json_res['data']['s'].lower()
    #         if pair[-3:] == 'btc':
    #             arb = pair[0:len(pair) - 3]
    #         elif pair[-4:] == 'usdt':
    #             arb = pair[0:len(pair) - 4]
    #         firstUpdateId = json_res["data"]["U"]
    #         finalUpdateId = json_res["data"]["u"]
    #
    #         if pair == 'btcusdt':
    #             if finalUpdateId > btc_book['orderbook']['lastUpdateId']: ### See Binance API documentation for details on this condition ###
    #                 for side in SIDES:
    #                     uos = np.array(json_res["data"][side], np.float64)
    #                     btc_ob = btc_book['orderbook'][side]
    #                     if uos.size == 0:
    #                         continue
    #                     else:
    #                         not_in_index = np.in1d(uos[:,0], btc_ob[:,0], invert=True)
    #                         ss_index = np.searchsorted(btc_ob[:,0], uos[not_in_index,0]) if side == 'a' else np.searchsorted(-btc_ob[:,0], -uos[not_in_index,0])
    #                         btc_ob = np.insert(btc_ob, ss_index, uos[not_in_index], axis=0)
    #
    #                         inter, orders_ind, updateorders_ind = np.intersect1d(btc_ob[:,0], uos[:,0], return_indices=True)
    #                         btc_ob[orders_ind] = uos[updateorders_ind]
    #
    #                         delete_ind = np.where(btc_ob == 0)[0]
    #                         btc_ob = np.delete(btc_ob, delete_ind, axis=0)
    #                         btc_book['orderbook'][side] = btc_ob
    #             else:
    #                 pass
    #         else:
    #             if finalUpdateId > arbitrage_book[arb]['orderbooks'][pair]['lastUpdateId']:
    #                 for side in SIDES:
    #                     uos = np.array(json_res["data"][side], np.float64)
    #                     arb_ob = arbitrage_book[arb]['orderbooks'][pair][side]
    #                     if uos.size == 0:
    #                         continue
    #                     else:
    #                         not_in_index = np.in1d(uos[:,0], arb_ob[:,0], invert=True)
    #                         ss_index = np.searchsorted(arb_ob[:,0], uos[not_in_index,0]) if side == 'a' else np.searchsorted(-arb_ob[:,0], -uos[not_in_index,0])
    #                         arb_ob = np.insert(arb_ob, ss_index, uos[not_in_index], axis=0)
    #
    #                         inter, orders_ind, updateorders_ind = np.intersect1d(arb_ob[:,0], uos[:,0], return_indices=True)
    #                         arb_ob[orders_ind] = uos[updateorders_ind]
    #
    #                         delete_ind = np.where(arb_ob == 0)[0]
    #                         arb_ob = np.delete(arb_ob, delete_ind, axis=0)
    #                         arbitrage_book[arb]['orderbooks'][pair][side] = arb_ob
    #             else:
    #                 pass
    #     else:
    #         pass
    # except Exception as err:
    #     logger.exception(err)
    #     sys.exit()

async def populateArb():
    global arbitrage_book
    global btc_book
    global balance
    global is_trading
    while 1:
        await asyncio.sleep(0.003)
        try:
            btc_book['weighted_prices']['regular'] = getWeightedPrice(btc_book['orderbook']['a'], balance, reverse=False)
            btc_book['weighted_prices']['reverse'] = getWeightedPrice(btc_book['orderbook']['b'], balance, reverse=False)
            btc_book['amount_if_bought'] = np.divide(balance, btc_book['weighted_prices']['regular'])
            for arb in ARBS:
                pair_iterator = [pair for pair in PAIRS if pair[0:len(arb)] == arb]
                for pair in sorted(pair_iterator, reverse=True):
                    arb_ob = arbitrage_book[arb]['orderbooks'][pair]
                    if pair[-4:] == 'usdt':
                        arbitrage_book[arb]['regular']['weighted_prices'][pair] = getWeightedPrice(arb_ob['b'], balance, reverse=False)
                        arbitrage_book[arb]['reverse']['weighted_prices'][pair] = getWeightedPrice(arb_ob['a'], balance, reverse=False)
                        arbitrage_book[arb]['reverse']['amount_if_bought'] = np.divide(balance, arbitrage_book[arb]['reverse']['weighted_prices'][pair])
                    else:
                        arbitrage_book[arb]['regular']['weighted_prices'][pair] = getWeightedPrice(arb_ob['a'], btc_book['amount_if_bought'], reverse=False)
                        arbitrage_book[arb]['reverse']['weighted_prices'][pair] = getWeightedPrice(arb_ob['b'], arbitrage_book[arb]['reverse']['amount_if_bought'], reverse=True)

                regular_arb_price = np.multiply(btc_book['weighted_prices']['regular'], arbitrage_book[arb]['regular']['weighted_prices'][arb + 'btc'])
                reverse_arb_price = np.divide(arbitrage_book[arb]['reverse']['weighted_prices'][arb + 'usdt'], arbitrage_book[arb]['reverse']['weighted_prices'][arb + 'btc'])
                arbitrage_book[arb]['regular']['triangle_values'] = np.divide(np.subtract(arbitrage_book[arb]['regular']['weighted_prices'][arb + 'usdt'], regular_arb_price), regular_arb_price)
                arbitrage_book[arb]['reverse']['triangle_values'] = np.divide(np.subtract(btc_book['weighted_prices']['reverse'], reverse_arb_price), reverse_arb_price)

                if arbitrage_book[arb]['regular']['triangle_values'] > 0 and is_trading == False:
                    logger.info('Executing regular {}. Arb value is {} | Weighted Prices: {}'.format(arb, arbitrage_book[arb]['regular']['triangle_values'], [btc_book['weighted_prices']['regular'], arbitrage_book[arb]['regular']['weighted_prices'][arb + 'btc'], arbitrage_book[arb]['regular']['weighted_prices'][arb + 'usdt']]))
                    await ex_arb(arb.upper(), True, [btc_book['weighted_prices']['regular'], arbitrage_book[arb]['regular']['weighted_prices'][arb + 'btc'], arbitrage_book[arb]['regular']['weighted_prices'][arb + 'usdt']])
                elif arbitrage_book[arb]['reverse']['triangle_values'] > 0 and is_trading == False:
                    logger.info('Executing regular {}. Arb value is {} | Weighted Prices: {}'.format(arb, arbitrage_book[arb]['reverse']['triangle_values'], [btc_book['weighted_prices']['reverse'], arbitrage_book[arb]['reverse']['weighted_prices'][arb + 'btc'], arbitrage_book[arb]['reverse']['weighted_prices'][arb + 'usdt']]))
                    await ex_arb(arb.upper(), False, [btc_book['weighted_prices']['reverse'], arbitrage_book[arb]['reverse']['weighted_prices'][arb + 'btc'], arbitrage_book[arb]['reverse']['weighted_prices'][arb + 'usdt']])
                else:
                    continue

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
                    if json_res is not None:
                        if resp.status != 200:
                            if json_res['code'] == -2010:
                                logger.info('Trade failed. Insufficient Funds. Recursion yay')
                                await ex_trade(pair, side, str(float(quantity) * 0.999), recvWindow)
                            else:
                                logger.info('Some other type of error occurred. {}'.format(json_res['code']))
                        else:
                            return {'content': json_res, 'status_code': resp.status, 'params': params}
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def ex_arb(arb, is_regular, weighted_prices):
    global is_trading
    global balance
    global arbitrage_book
    global btc_book
    is_trading = True
    quantity_hash = [str(balance), 0, 0]
    leakage_hash = {}
    slippage_hash = {}

    for i, pair in enumerate(['BTCUSDT', arb + 'BTC', arb + 'USDT'] if is_regular else [arb + 'USDT', arb + 'BTC', 'BTCUSDT']):
        start_time = time.time()
        if i == 0:
            trade_response = await ex_trade(pair, 'BUY', quantity_hash[i], 1_000)
        elif i == 1:
            trade_response = await ex_trade(pair, 'BUY' if is_regular else 'SELL', quantity_hash[i], 10_000)
        elif i == 2:
            trade_response = await ex_trade(pair, 'SELL', quantity_hash[i], 10_000)
        logger.info('Trade Params: {} | Trade Response: {} | Trade Latency: {}'.format(str(trade_response['params']), str(trade_response['content']), time.time() - start_time))
        if trade_response['status_code'] == 200:
            try:
                if i == 0:
                    if is_regular:
                        quantity_hash[i + 1] = str(round_quote_precision(float(trade_response['content']['executedQty'])))
                        leakage_hash['btc'] = float(trade_response['content']['executedQty'])
                        slippage_hash['BTCUSDT'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[0]) / weighted_prices[0]) * 100, 3)
                    else:
                        wp = getWeightedPrice(arbitrage_book[arb.lower()]['orderbooks'][arb.lower() + 'btc']['b'][:25], float(trade_response['content']['executedQty']), reverse=True)
                        quantity_hash[i + 1] = str(round_quote_precision(float(trade_response['content']['executedQty']) * wp))
                        leakage_hash[arb] = float(trade_response['content']['executedQty'])
                        slippage_hash[arb + 'USDT'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[2]) / weighted_prices[2]) * 100, 3)
                        logger.info('Weighted Price for next quantity hash: {}'.format(wp))
                elif i == 1:
                    if is_regular:
                        wp = getWeightedPrice(arbitrage_book[arb.lower()]['orderbooks'][arb.lower() + 'usdt']['b'][:25], float(trade_response['content']['executedQty']), reverse=True)
                        quantity_hash[i + 1] = str(round_quote_precision(float(trade_response['content']['executedQty']) * wp))
                        leakage_hash['btc'] = leakage_hash['btc'] - float(trade_response['content']['cummulativeQuoteQty'])
                        leakage_hash[arb] = float(trade_response['content']['executedQty'])
                        slippage_hash[arb + 'BTC'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[1]) / weighted_prices[1]) * 100, 3)
                        logger.info('Weighted Price for next quantity hash: {}'.format(wp))
                    else:
                        wp = getWeightedPrice(btc_book['orderbook']['b'], float(trade_response['content']['cummulativeQuoteQty']), reverse=True)
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
                    sys.exit()
            except Exception as err:
                logger.exception(err)
                sys.exit()
        else:
            logger.info('Status code error: {}'.format(trade_response['status_code']))
            is_trading = False
            sys.exit()
            break

async def stillAlive():
    global arbitrage_book
    await asyncio.sleep(10)
    check_list = []
    while 1:
        await asyncio.sleep(60)
        check_list.append(arbitrage_book['eth']['regular']['triangle_values'])
        check_len = len(check_list)
        if check_len > 2:
            check_list = check_list[-3:]
            # logger.info(check_list)
            if check_list[2] == check_list[1] and check_list[2] == check_list[1]:
                logger.info('Program still running but websocket streams have stopped')
                sys.exit()
            else:
                continue
        else:
            continue

async def restart(isRecursion):
    global is_trading
    if not isRecursion:
        await asyncio.sleep(10_800) # 3 hrs
        if not is_trading:
            sys.exit()
        else:
            logger.info('Tried to exit but is_trading == True')
            await asyncio.sleep(1)
            await restart(True)

async def fullBookTimer():
    global build_list
    global balance
    while 1:
        await asyncio.sleep(1)
        try:
            check = all(item in build_list for item in PAIRS)
            if check:
                logger.info('All orderbooks have successfully been filled')
                await asyncio.wait([populateArb(), stillAlive(), restart(False)])
            else:
                continue
        except Exception as err:
            logger.exception(err)
            sys.exit()
        else:
            continue

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
                    params = create_signed_params(item + 'USDT', 'SELL', round_quote_precision(high_bal_dict[item]), 10_000)
                    res = requests.post(url=trade_url, headers=api_header, params=params)
                    logger.info(res.json())
                    if res.status_code == 200:
                        print('{} balance converted to USDT'.format(item))
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
    # coroutines.append(fullBookTimer())
    await asyncio.wait(coroutines)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
