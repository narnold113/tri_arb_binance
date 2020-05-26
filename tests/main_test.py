import json
import asyncio
import websockets
import requests
import numpy as np
import logging
import traceback as tb
import helper_test as helper
import mysql.connector
import random
import time
import sys
from datetime import datetime
from mysql.connector import Error
from mysql.connector import errorcode

logger = logging.getLogger('tri_arb_binance')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logHandler = logging.FileHandler('tri_arb_hitbtc.log', mode='a')
logHandler = logging.StreamHandler()
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

balances = [1_000, 10_000, 25_000, 50_000]

ARBS = [
    'eth' # OK
    # ,'ltc' # OK
    # ,'xrp' # OK
    # ,'bch' # OK
    # ,'eos' # OK
    # ,'xmr' # OK
    # ,'etc' # OK
    # ,'zrx' # OK
    # ,'trx'
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
# print(PAIRS)

STREAMS = []
for pair in PAIRS:
    STREAMS.append(pair + '@depth@100ms')
# print(STREAMS)

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
build_list = []



async def updateOrderbooks(res):
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
                if np.isnan(btc_book['orderbook']['a'][0][0]): ### Fill btc orderbook with snapshot with pair depth ###
                    try:
                        raw_snapshot = requests.get('https://www.binance.com/api/v3/depth?symbol=BTCUSDT&limit=500')
                        if raw_snapshot.status_code == 200:
                            snapshot = raw_snapshot.json()
                            btc_book['orderbook']['lastUpdateId'] = snapshot['lastUpdateId']
                            btc_book['orderbook']['a'] = np.array(snapshot['asks'], np.float64)
                            btc_book['orderbook']['b'] = np.array(snapshot['bids'], np.float64)
                            build_list.append(pair)
                            print('Filled btc_book successfully')
                        else:
                            print(raw_snapshot.status_code)
                        # print('snapshot lastUpdateId', snapshot['lastUpdateId'])
                        # print('firstUpdateId', firstUpdateId)
                        # print('finalUpdateId', finalUpdateId)
                    except Exception:
                        tb.print_exc()
                else:
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
                if np.isnan(arbitrage_book[arb]['orderbooks'][pair]['a'][0][0]): ### Fill orderbooks in arbitrage_book with snapshot of pair depth ###
                    try:
                        raw_snapshot = requests.get('https://www.binance.com/api/v3/depth?symbol={}&limit=500'.format(pair.upper()))
                        if raw_snapshot.status_code == 200:
                            snapshot = raw_snapshot.json()
                            arbitrage_book[arb]['orderbooks'][pair]['lastUpdateId'] = snapshot['lastUpdateId']
                            arbitrage_book[arb]['orderbooks'][pair]['a'] = np.array(snapshot['asks'], np.float64)
                            arbitrage_book[arb]['orderbooks'][pair]['b'] = np.array(snapshot['bids'], np.float64)
                            build_list.append(pair)
                            print('Filled', pair, 'orderbook successfully')
                        else:
                            print(raw_snapshot.status_code)
                    except Exception:
                        tb.print_exc()
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
                                # arb_ob = np.append(arb_ob, uos[notin_ind], axis=0)

                                inter, orders_ind, updateorders_ind = np.intersect1d(arb_ob[:,0], uos[:,0], return_indices=True)
                                arb_ob[orders_ind] = uos[updateorders_ind]

                                delete_ind = np.where(arb_ob == 0)[0]
                                arb_ob = np.delete(arb_ob, delete_ind, axis=0)
                                arbitrage_book[arb]['orderbooks'][pair][side] = arb_ob
                    else:
                        pass
        else:
            pass
    except Exception:
        tb.print_exc()

threshold_array = []
threshold_tmp = {
    arb: {
        'first_timestamp': 0,
        'values': set()
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
async def populateArb():
    global arbitrage_book
    global btc_book
    global balances
    global threshold_array
    global threshold_tmp
    global threshold_keep

    while 1:
        await asyncio.sleep(0.01)
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
                
                if arbitrage_book[arb]['regular']['triangle_values'][0] >= 0:
                    if threshold_tmp[arb]['first_timestamp'] == 0:
                        threshold_tmp[arb]['first_timestamp'] = time.time()
                        threshold_tmp[arb]['values'].add(arbitrage_book[arb]['regular']['triangle_values'][0])
                    else:
                        threshold_tmp[arb]['values'].add(arbitrage_book[arb]['regular']['triangle_values'][0])
                else:
                    if threshold_tmp[arb]['first_timestamp'] == 0:
                        continue
                    else:
                        threshold_array.extend([threshold_tmp[arb]['first_timestamp'], time.time() - threshold_tmp[arb]['first_timestamp'], list(threshold_tmp[arb]['values'])])
                        threshold_keep[arb]['regular'].append(threshold_array)
                        
                        threshold_array = []
                        threshold_tmp[arb]['first_timestamp'] = 0
                        threshold_tmp[arb]['values'] = set()
        except Exception:
            tb.print_exc()


async def arbMonitor():
    global arbitrage_book
    global threshold_tmp
    await asyncio.sleep(10)

    while 1:
        await asyncio.sleep(3)
        print(arbitrage_book['eth']['regular']['triangle_values'])
        print(len(threshold_keep['eth']['regular']))
        # for arb in ARBS:
        #     if arbitrage_book[arb]['regular']['triangle_values'][0] > 0.004:
        #         start_time = datetime.now()



        # print(arbitrage_book['eth']['regular']['triangle_values'][0])
        # await asyncio.sleep(0.1)



async def printBook():
    global arbitrage_book
    global btc_book
    await asyncio.sleep(10)
    while 1:
        # btc_ob = btc_book['orderbook']['a'][btc_book['orderbook']['a'][:,0].argsort()]
        print(btc_book['orderbook']['a'][0:3])
        # arb_ob = arbitrage_book['eth']['orderbooks']['ethusdt']['a'][arbitrage_book['eth']['orderbooks']['ethusdt']['a'][:,0].argsort()]
        # print(arb_ob[0:3])
        await asyncio.sleep(1)

async def fullBookTimer():
    global build_list

    while 1:
        await asyncio.sleep(0.5)
        # print(PAIRS)
        # print(build_list)
        try:
            check = all(item in build_list for item in PAIRS)
            if check:
                print('Awaiting populateArb function')
                await populateArb()
            else:
                continue
        except Exception:
            tb.print_exc()
        else:
            continue

async def subscribe() -> None:
    url = 'wss://stream.binance.com:9443/stream'
    strParams = '''{"method": "SUBSCRIBE","params": "placeholder","id": 1}'''
    params = json.loads(strParams)
    params['params'] = STREAMS
    try:
        async with websockets.client.connect(url) as ws:
            try:
                await ws.send(str(params).replace('\'', '"'))
            except Exception as err:
                print(err)
            while 1:
                res = await ws.recv()
                await updateOrderbooks(res)
                # print(res, '\n\n')
    except Exception as err:
        print(err)
        
async def main():
    coroutines = []
    coroutines.append(subscribe())
    # coroutines.append(printBook())
    coroutines.append(fullBookTimer())
    coroutines.append(arbMonitor())
    await asyncio.wait(coroutines)
    # pass


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()