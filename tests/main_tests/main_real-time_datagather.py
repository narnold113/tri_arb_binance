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
import get_arbs_test
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

ARBS = ['eth']
PAIRS = []
for arb in ARBS:
    PAIRS.append(arb + 'usdt')
    PAIRS.append(arb + 'btc')
PAIRS.insert(0, 'btcusdt')
STREAMS = []
# STREAMS = ['ethusdt@bookTicker']
for pair in PAIRS:
    STREAMS.append(pair + '@bookTicker')
SIDES = [
    'a',
    'b'
]

btc_ticker = [[0,0,0], [0,0,0]] # [price, quantity, volume] Bid side is in first array
arbitrage_book = {
    arb: {
        pair: [[0,0,0], [0,0,0]] # [price, quantity, volume] Bid side is in first array
        for pair in PAIRS if pair[0:len(arb)] == arb
    }
    for arb in ARBS
}
for arb in ARBS:
    arbitrage_book[arb]['triangles'] = [[0,0], [0,0]] # [value, volume] Regular is in first array
# print(PAIRS)
# print(arbitrage_book)


async def updateBook(payload):
    global arbitrage_book
    global btc_ticker
    try:
        json_payload = json.loads(payload)
        if 'stream' in json_payload.keys():
            pair = json_payload['data']['s'].lower()
            if pair[-3:] == 'btc':
                arb = pair[0:len(pair) - 3]
            elif pair[-4:] == 'usdt':
                arb = pair[0:len(pair) - 4]

            if pair == 'btcusdt':
                btc_ticker[0][0] = float(json_payload['data']['b'])
                btc_ticker[0][1] = float(json_payload['data']['B'])
                btc_ticker[0][2] = btc_ticker[0][0] * btc_ticker[0][1]

                btc_ticker[1][0] = float(json_payload['data']['a'])
                btc_ticker[1][1] = float(json_payload['data']['A'])
                btc_ticker[1][2] = btc_ticker[1][0] * btc_ticker[1][1]
            else:
                arbitrage_book[arb][pair][0][0] = float(json_payload['data']['b'])
                arbitrage_book[arb][pair][0][1] = float(json_payload['data']['B'])
                arbitrage_book[arb][pair][0][2] = arbitrage_book[arb][pair][0][0] * arbitrage_book[arb][pair][0][1]

                arbitrage_book[arb][pair][1][0] = float(json_payload['data']['a'])
                arbitrage_book[arb][pair][1][1] = float(json_payload['data']['A'])
                arbitrage_book[arb][pair][1][2] = arbitrage_book[arb][pair][1][0] * arbitrage_book[arb][pair][1][1]
        # print(arbitrage_book['eth']
        # print([x for x in arbitrage_book['eth']])

        # print('BTCUSD Bid: {}\nBTCUSD Ask: {}'.format(btc_ticker[0], btc_ticker[1]))
        # print('ETHBTC Bid: {}\nETHBTC Ask: {}'.format(arbitrage_book['eth']['ethbtc'][0], arbitrage_book['eth']['ethbtc'][1]))
        # print('ETHUSD Bid: {}\nETHUSD Ask: {}'.format(arbitrage_book['eth']['ethusdt'][0], arbitrage_book['eth']['ethusdt'][1]))

        # print('BTCUSD volume: ' + str(btc_ticker[1][2]))
        # print('ETHBTC volume: ' + str(arbitrage_book['eth']['ethbtc'][1][2] * btc_ticker[1][0]))
        # print('ETHUSD volume: ' + str(arbitrage_book['eth']['ethusdt'][0][2]))
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def populateArb():
    global arbitrage_book
    global btc_ticker
    await asyncio.sleep(5)

    while 1:
        try:
            await asyncio.sleep(0.005)
            reg_volume_hash = []
            rev_volume_hash = []
            for arb in ARBS:
                pair_iterator = [pair for pair in PAIRS if pair[:len(arb)] == arb]
                for pair in sorted(pair_iterator, reverse=True):
                    pass
                reg_synth_price = np.multiply(btc_ticker[1][0], arbitrage_book[arb][arb + 'btc'][1][0])
                reg_volume_hash.append(btc_ticker[1][2])
                reg_volume_hash.append(arbitrage_book[arb][arb + 'btc'][1][2] * btc_ticker[1][0])
                reg_volume_hash.append(arbitrage_book[arb][arb + 'usdt'][0][2])
                arbitrage_book[arb]['triangles'][0][0] = np.divide(np.subtract(arbitrage_book[arb][arb + 'usdt'][0][0], reg_synth_price), reg_synth_price)
                arbitrage_book[arb]['triangles'][0][1] = min(reg_volume_hash)

                rev_synth_price = np.divide(arbitrage_book[arb][arb + 'usdt'][1][0], arbitrage_book[arb][arb + 'btc'][0][0])
                rev_volume_hash.append(btc_ticker[0][2])
                rev_volume_hash.append(arbitrage_book[arb][arb + 'btc'][0][2] * btc_ticker[0][0])
                rev_volume_hash.append(arbitrage_book[arb][arb + 'usdt'][1][2])
                arbitrage_book[arb]['triangles'][1][0] = np.divide(np.subtract(btc_ticker[0][0], rev_synth_price), rev_synth_price)
                arbitrage_book[arb]['triangles'][1][1] = min(rev_volume_hash)

                print(arbitrage_book['eth']['triangles'])


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
                    # now = time.time()
                    res = await ws.recv()
                    await updateBook(res)
                    # print((time.time() - now) * 1000)
                except Exception as err:
                    logger.exception(err)
                    sys.exit()
    except Exception as err:
        logger.exception(err)
        sys.exit()



async def main():
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
