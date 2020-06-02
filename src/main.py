import json
import asyncio
import websockets
import aiohttp
import numpy as np
import logging
import traceback as tb
import helper as helper
import mysql.connector
import random
import time
import sys
from datetime import datetime
from statistics import fmean
from mysql.connector import Error
from mysql.connector import errorcode

logger = logging.getLogger('tri_arb_binance')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logHandler = logging.FileHandler('tri_arb_binance.log', mode='a')
logHandler = logging.StreamHandler()
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# balances = [1_000, 10_000, 25_000, 50_00]
balances = [1_000]

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

                for type in ['regular', 'reverse']:
                    if arbitrage_book[arb][type]['triangle_values'][0] >= 0:
                        if 'timestamp' not in threshold_dict[arb][type].keys():
                            threshold_dict[arb][type]['timestamp'] = float(time.time())
                            threshold_values[arb][type].append(arbitrage_book[arb][type]['triangle_values'][0])
                        else:
                            threshold_values[arb][type].append(arbitrage_book[arb][type]['triangle_values'][0])
                    else:
                        if 'timestamp' not in threshold_dict[arb][type].keys():
                            continue
                        else:
                            threshold_dict[arb][type]['duration'] = float(time.time() - threshold_dict[arb][type]['timestamp'])
                            threshold_dict[arb][type]['low'] =  float(min(threshold_values[arb][type]))
                            threshold_dict[arb][type]['high'] = float(max(threshold_values[arb][type]))
                            threshold_dict[arb][type]['mean'] = float(fmean(threshold_values[arb][type]))

                            threshold_keep[arb][type].append(threshold_dict[arb][type])
                            threshold_values[arb][type] = list()
                            threshold_dict[arb][type] = dict()
        except Exception as err:
            logger.exception(err)
            sys.exit()

async def createSqlTables():
    conn = None
    try:
        conn = mysql.connector.connect(user='python', password='python', host='127.0.0.1', database='tri_arb_binance')
        cursor = conn.cursor()

        for arb in ARBS:
            table_creation = str(
                "CREATE TABLE {} ("
                "timestamp DECIMAL(16,6) NOT NULL,"
                "duration DECIMAL(9,6) NULL,"
                "low DECIMAL(8,7) NULL,"
                "high DECIMAL(8,7) NULL,"
                "mean DECIMAL(8,7) NULL,"
                "type VARCHAR(50) NULL"
                ") ENGINE=InnoDB".format(arb)
            )
            try:
                cursor.execute(table_creation)

                log_msg = 'succesfully created table for ' + arb
                logger.info(log_msg)
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    # print(arb, "table already exists.")
                    log_msq = arb + ' table already exists'
                    logger.info(log_msg)
                else:
                    # print(err.msg)
                    logger.exception(err.msq)
    except Error as e:
        logger.exception(e.msg)
        sys.exit()
    finally:
        if conn is not None and conn.is_connected():
            conn.close()

async def arbMonitor():
    global arbitrage_book
    global threshold_keep

    try:
        conn = mysql.connector.connect(user='python', password='python', host='127.0.0.1', database='tri_arb_binance')

        while 1:
            await asyncio.sleep(30)
            try:
                for arb in ARBS:
                    insert_statement = str(
                        "INSERT INTO {} "
                        "VALUES (%s, %s, %s, %s, %s, %s)".format(arb)
                    )
                    for type in ['regular', 'reverse']:
                        # print(arb, type, len(threshold_keep[arb][type]))
                        if len(threshold_keep[arb][type]) >= 5:
                            log_msq = arb + 'for type' + type + 'has over 5 length'
                            logger.info(log_msg)
                            # print(arb, 'for type', type, 'has over 5 length')
                            for dct in threshold_keep[arb][type]:
                                insert_values = list(dct.values())
                                insert_values.append(type)
                                cursor = conn.cursor()
                                cursor.execute(insert_statement, tuple(insert_values))
                                conn.commit()
                                cursor.close()
                                # print('SQL insert was succesfull')
                            threshold_keep[arb][type][:] = list()
                        else:
                            continue
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
                # print('Awaiting populateArb and arbMonitor functions')
                await asyncio.wait([populateArb(), arbMonitor()])
            else:
                continue
        except Exception as err:
            logger.exception(err)
            sys.exit()
        else:
            continue

async def printBook():
    global arbitrage_book
    global btc_book
    await asyncio.sleep(10)
    while 1:
        print(btc_book['orderbook']['a'][0:3])
        await asyncio.sleep(1)

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
                res = await ws.recv()
                await updateBook(res)
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def main():
    coroutines = []
    coroutines.append(subscribe())
    coroutines.append(fullBookTimer())
    coroutines.append(createSqlTables())
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
