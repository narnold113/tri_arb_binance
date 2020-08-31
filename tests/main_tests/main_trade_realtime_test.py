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
is_trading = False
isBookFull = False
balance = 30
build_set = set()
trade_responses = []

ARBS = ['eth', 'xrp', 'ltc', 'dash']
# ARBS = get_arbs.get_arbs()
logger.info('Number of ARBS: {}'.format(len(ARBS)))
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
# print(PAIRS)
# print(arbitrage_book)



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
    global build_set
    global isBookFull
    try:
        json_payload = json.loads(payload)
        if 'stream' in json_payload.keys():
            pair = json_payload['data']['s'].lower()
            if not isBookFull:
                build_set.add(pair)
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
        # print(arbitrage_book['eth']
        # print([x for x in arbitrage_book['eth']])

        # print('BTCUSD Bid: {}\nBTCUSD Ask: {}'.format(btc_book[0], btc_book[1]))
        # print('ETHBTC Bid: {}\nETHBTC Ask: {}'.format(arbitrage_book['eth']['ethbtc'][0], arbitrage_book['eth']['ethbtc'][1]))
        # print('ETHUSD Bid: {}\nETHUSD Ask: {}'.format(arbitrage_book['eth']['ethusdt'][0], arbitrage_book['eth']['ethusdt'][1]))

        # print('BTCUSD volume: ' + str(btc_book[1][2]))
        # print('ETHBTC volume: ' + str(arbitrage_book['eth']['ethbtc'][1][2] * btc_book[1][0]))
        # print('ETHUSD volume: ' + str(arbitrage_book['eth']['ethusdt'][0][2]))
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def populateArb():
    global arbitrage_book
    global btc_book
    global is_trading
    global balance
    while 1:
        try:
            await asyncio.sleep(0.005)
            reg_volume_hash = []
            rev_volume_hash = []
            for arb in ARBS:
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

                # print(arbitrage_book[arb]['triangles'])
                if arbitrage_book[arb]['triangles'][0][0] > 0.0001 and is_trading == False: # Regular
                    if arbitrage_book[arb]['triangles'][0][1] >= 11:
                        weighted_prices = [
                            btc_book[1][0],
                            arbitrage_book[arb][arb + 'btc'][1][0],
                            arbitrage_book[arb][arb + 'usdt'][0][0]
                        ]
                        balances = [
                            str(round_quote_precision(arbitrage_book[arb]['triangles'][0][1] if arbitrage_book[arb]['triangles'][0][1] <= balance else balance)),
                            str(round_quote_precision(arbitrage_book[arb]['triangles'][0][1] if arbitrage_book[arb]['triangles'][0][1] <= balance else balance / weighted_prices[0])),
                            str(round_quote_precision(((arbitrage_book[arb]['triangles'][0][1] if arbitrage_book[arb]['triangles'][0][1] <= balance else balance / weighted_prices[0]) / weighted_prices[1]) * weighted_prices[2]))
                        ]
                        logger.info('Executing regular {}. Arb value is {} | Weighted Prices: {} | Balances for quote quantity: {}'.format(arb, arbitrage_book[arb]['triangles'][0][0], weighted_prices, balances))
                        await ex_arb(
                            arb.upper(),
                            True,
                            balances,
                            weighted_prices
                        )
                        break # breaking the for loop because the orderbooks used are now 30ish ms old
                elif arbitrage_book[arb]['triangles'][1][0] > 0.0001 and is_trading == False: # Reverse
                    if arbitrage_book[arb]['triangles'][1][1] >= 11:
                        weighted_prices = [
                            arbitrage_book[arb][arb + 'usdt'][1][0],
                            arbitrage_book[arb][arb + 'btc'][0][0],
                            btc_book[0][0]
                        ]
                        balances = [
                            str(round_quote_precision(arbitrage_book[arb]['triangles'][1][1] if arbitrage_book[arb]['triangles'][1][1] <= balance else balance)),
                            str(round_quote_precision((arbitrage_book[arb]['triangles'][1][1] if arbitrage_book[arb]['triangles'][1][1] <= balance else balance / weighted_prices[0]) * weighted_prices[1])),
                            str(round_quote_precision(((arbitrage_book[arb]['triangles'][1][1] if arbitrage_book[arb]['triangles'][1][1] <= balance else balance / weighted_prices[0]) * weighted_prices[1]) * weighted_prices[2]))
                        ]
                        logger.info('Executing reverse {}. Arb value is {} | Weighted Prices: {} | Balances for quote quantity: {}'.format(arb, arbitrage_book[arb]['triangles'][1][0], weighted_prices, balances))
                        await ex_arb(
                            arb.upper(),
                            False,
                            balances,
                            weighted_prices
                        )
                        break # breaking the for loop because the orderbooks used are now 30ish ms old
        except Exception as err:
            logger.exception(err)
            sys.exit()

async def ex_trade(pair, side, quantity, leg, wait_time, is_high):
    global trade_url
    global api_header
    global trade_responses

    logger.info('{} | {} {} {} {} '.format(int(round(time.time() * 1000)), pair, side, quantity, leg, wait_time))

    if leg == 2:
        await asyncio.sleep(0.001 + (wait_time / 1000))
    elif leg == 3:
        await asyncio.sleep(0.004 + (wait_time / 1000))
    elif leg == 4: # Recursion
        await asyncio.sleep(0.005)

    params = create_signed_params(pair, side, quantity, 1_000)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=trade_url, headers=api_header, params=params) as resp:
                json_res = await resp.json()
                if json_res is not None:
                    if resp.status == 200:
                        # logger.info({'content': json_res, 'params': params})
                        if is_high:
                            pass
                        else:
                            trade_responses.append({'params': params, 'response': json_res, 'leg': leg, 'wait_time': wait_time, 'trade_latency': json_res['transactTime'] - params['timestamp']})
                    else:
                        if json_res['code'] == -2010:
                            logger.info('Leg {} failed. Wait_time: {}'.format(leg, wait_time))
                            if (leg == 2 or leg == 3 or leg == 4) and wait_time == 9 and len(trade_responses) < 3:
                                logger.info('Last order of leg {} failed. Recursion.'.format(leg))
                                return await ex_trade(pair, side, str(round_quote_precision(float(quantity) * 0.999)), 4, 12, False)
                        else:
                            logger.info('Some other type of error occurred: {}'.format(json_res))
                            sys.exit()
    except Exception as err:
        logger.exception(err)
        sys.exit()

# async def ex_arb(arb, balances, is_regular, weighted_prices):
async def ex_arb(arb, is_regular, balances, weighted_prices):
    global is_trading
    global trade_responses
    is_trading = True
    trade_coroutines = []
    if is_regular:
        for i in range(0,4):
            trade_coroutines.append(ex_trade(arb + 'BTC', 'BUY', balances[1], 2, i * 3, False))
            trade_coroutines.append(ex_trade(arb + 'USDT', 'SELL', balances[2], 3, i * 3, False))
        trade_coroutines.insert(0, ex_trade('BTCUSDT', 'BUY', balances[0], 1, 0, False))
        await asyncio.wait(trade_coroutines)
        # trade_coroutines = [
        #     ex_trade('BTCUSDT', 'BUY', balances[0], 1),
        #     ex_trade(arb + 'BTC', 'BUY', balances[1], 2),
        #     ex_trade(arb + 'USDT', 'SELL', balances[2], 3)
        # ]
    else:
        # trade_coroutines = [
        #     ex_trade(arb + 'USDT', 'BUY', balances[0], 1),
        #     ex_trade(arb + 'BTC', 'SELL', balances[1], 2),
        #     ex_trade('BTCUSDT', 'SELL', balances[2], 3)
        # ]
        for i in range(0,4):
            trade_coroutines.append(ex_trade(arb + 'BTC', 'SELL', balances[1], 2, i * 3, False))
            trade_coroutines.append(ex_trade('BTCUSDT', 'SELL', balances[2], 3, i * 3, False))
        trade_coroutines.insert(0, ex_trade(arb + 'USDT', 'BUY', balances[0], 1, 0, False))
        await asyncio.wait(trade_coroutines)

    is_trading = False
    leakage_hash = {}
    slippage_hash = {}
    for i, tr in enumerate(trade_responses[-3:]):
        if i == 0:
            if is_regular:
                leakage_hash['BTC'] = float(tr['response']['executedQty'])
                slippage_hash['BTCUSDT'] = round(((float(tr['response']['fills'][0]['price']) - weighted_prices[0]) / weighted_prices[0]) * 100, 3)
            else:
                leakage_hash[arb] = float(tr['response']['executedQty'])
                slippage_hash[arb + 'USDT'] = round(((float(tr['response']['fills'][0]['price']) - weighted_prices[0]) / weighted_prices[0]) * 100, 3)
        elif i == 1:
            if is_regular:
                leakage_hash['BTC'] = leakage_hash['BTC'] - float(tr['response']['cummulativeQuoteQty'])
                leakage_hash[arb] = float(tr['response']['executedQty'])
                slippage_hash[arb + 'BTC'] = round(((float(tr['response']['fills'][0]['price']) - weighted_prices[1]) / weighted_prices[1]) * 100, 3)
            else:
                leakage_hash[arb] = leakage_hash[arb] - float(tr['response']['executedQty'])
                leakage_hash['BTC'] = float(tr['response']['cummulativeQuoteQty'])
                slippage_hash[arb + 'BTC'] = round(((float(tr['response']['fills'][0]['price']) - weighted_prices[1]) / weighted_prices[1]) * -100, 3)
        else:
            if is_regular:
                leakage_hash[arb] = leakage_hash[arb] - float(tr['response']['executedQty'])
                slippage_hash[arb + 'USDT'] = round(((float(tr['response']['fills'][0]['price']) - weighted_prices[2]) / weighted_prices[2]) * -100, 3)
            else:
                leakage_hash['BTC'] = leakage_hash['BTC'] - float(tr['response']['executedQty'])
                slippage_hash['BTCUSDT'] = round(((float(tr['response']['fills'][0]['price']) - weighted_prices[2]) / weighted_prices[2]) * -100, 3)
        logger.info(tr)

    logger.info(
        str(
            'Trades for {} arb were successful\n'
            'BTC Leakage: {} ({} USDT) and {} Leakage: {} ({} USDT)\n'
            'Slippage Percentages: {}\n'
            'Average trade latency: {}\n'
            'Arb latency: {}'
        ).format(
            arb,
            leakage_hash['BTC'],
            leakage_hash['BTC'] * (weighted_prices[0] if is_regular else weighted_prices[2]),
            arb,
            leakage_hash[arb],
            leakage_hash[arb] * (weighted_prices[2] if is_regular else weighted_prices[0]),
            slippage_hash,
            np.average([x['response']['transactTime'] - x['params']['timestamp'] for x in trade_responses]),
            trade_responses[2]['response']['transactTime'] - trade_responses[0]['params']['timestamp']
        )
    )

    # sys.exit()
    # loop.close()


    # global is_trading
    # global arbitrage_book
    # global btc_book
    # is_trading = True
    # quantity_hash = [str(bal), 0, 0]
    # leakage_hash = {}
    # slippage_hash = {}

    # for i, pair in enumerate(['BTCUSDT', arb + 'BTC', arb + 'USDT'] if is_regular else [arb + 'USDT', arb + 'BTC', 'BTCUSDT']):
    #     start_time = time.time()
    #     if i == 0:
    #         trade_response = await ex_trade(pair, 'BUY', quantity_hash[i], 1_000)
    #     elif i == 1:
    #         trade_response = await ex_trade(pair, 'BUY' if is_regular else 'SELL', quantity_hash[i], 10_000)
    #     elif i == 2:
    #         trade_response = await ex_trade(pair, 'SELL', quantity_hash[i], 10_000)
    #     logger.info('Trade Params: {} | Trade Response: {} | Trade Latency: {}'.format(str(trade_response['params']), str(trade_response['content']), time.time() - start_time))
    #     try:
    #         if i == 0:
    #             if is_regular:
    #                 quantity_hash[i + 1] = str(round_quote_precision(float(trade_response['content']['executedQty'])))
    #                 leakage_hash['btc'] = float(trade_response['content']['executedQty'])
    #                 slippage_hash['BTCUSDT'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[0]) / weighted_prices[0]) * 100, 3)
    #             else:
    #                 wp = arbitrage_book[arb.lower()][arb.lower() + 'btc'][0][0]
    #                 quantity_hash[i + 1] = str(round_quote_precision(float(trade_response['content']['executedQty']) * wp))
    #                 leakage_hash[arb] = float(trade_response['content']['executedQty'])
    #                 slippage_hash[arb + 'USDT'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[2]) / weighted_prices[2]) * 100, 3)
    #                 logger.info('Weighted Price for next quantity hash: {}'.format(wp))
    #         elif i == 1:
    #             if is_regular:
    #                 wp = arbitrage_book[arb.lower()][arb.lower() + 'usdt'][0][0]
    #                 quantity_hash[i + 1] = str(round_quote_precision(float(trade_response['content']['executedQty']) * wp))
    #                 leakage_hash['btc'] = leakage_hash['btc'] - float(trade_response['content']['cummulativeQuoteQty'])
    #                 leakage_hash[arb] = float(trade_response['content']['executedQty'])
    #                 slippage_hash[arb + 'BTC'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[1]) / weighted_prices[1]) * 100, 3)
    #                 logger.info('Weighted Price for next quantity hash: {}'.format(wp))
    #             else:
    #                 wp = btc_book[0][0]
    #                 quantity_hash[i + 1] = str(round_quote_precision(float(trade_response['content']['cummulativeQuoteQty']) * wp))
    #                 leakage_hash[arb] = leakage_hash[arb] - float(trade_response['content']['executedQty'])
    #                 leakage_hash['btc'] = float(trade_response['content']['cummulativeQuoteQty'])
    #                 slippage_hash[arb + 'BTC'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[1]) / weighted_prices[1]) * -100, 3)
    #                 logger.info('Weighted Price for next quantity hash: {}'.format(wp))
    #         else:
    #             if is_regular:
    #                 leakage_hash[arb] = leakage_hash[arb] - float(trade_response['content']['executedQty'])
    #                 slippage_hash[arb + 'USDT'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[2]) / weighted_prices[2]) * -100, 3)
    #             else:
    #                 leakage_hash['btc'] = leakage_hash['btc'] - float(trade_response['content']['executedQty'])
    #                 slippage_hash['BTCUSDT'] = round(((float(trade_response['content']['fills'][0]['price']) - weighted_prices[0]) / weighted_prices[0]) * -100, 3)
    #
    #             balance = round_quote_precision(float(trade_response['content']['cummulativeQuoteQty']))
    #             logger.info(
    #                 str(
    #                     'Trades for {} arb were successful\n'
    #                     'USDT balance before: {} and after: {}\n'
    #                     'BTC Leakage: {} ({} USDT) and {} Leakage: {} ({} USDT)\n'
    #                     'Slippage Percentages: {}\n'
    #                 ).format(
    #                     arb,
    #                     quantity_hash[0],
    #                     balance,
    #                     leakage_hash['btc'],
    #                     leakage_hash['btc'] * weighted_prices[0],
    #                     arb, leakage_hash[arb],
    #                     leakage_hash[arb] * weighted_prices[2],
    #                     slippage_hash
    #                 )
    #             )
    #             is_trading = False
    #             sys.exit()
    #     except Exception as err:
    #         logger.exception(err)
    #         sys.exit()

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
                    trade_respone = await ex_trade(item + 'USDT', 'SELL', str(round_quote_precision(high_bal_dict[item] * 0.999)), 0, 0, True)
                    # logger.info('Trade Response for high_balance: {}'.format(trade_respone['content']))
                    logger.info('{} balance converted to USDT'.format(item))


                    # params = create_signed_params(item + 'USDT', 'SELL', round_quote_precision(high_bal_dict[item]), 10_000)
                    # res = requests.post(url=trade_url, headers=api_header, params=params)
                    # json_res = res.json()
                    # logger.info(res.json())
                    # if res.status_code == 200:
                    #     print('{} balance converted to USDT'.format(item))
                    # else:
                    #     if json_res['code'] = -2010:

                except Exception as err:
                    print(err)
            return 'At least one crypto balance was over $10'
        else:
            return 'No high balances'
    except Exception as err:
        logger.exception(err)
        sys.exit()

async def fullBookTimer():
    global build_set
    global isBookFull
    while 1:
        await asyncio.sleep(0.5)
        try:
            check = all(item in build_set for item in PAIRS)
            if check:
                logger.info('All orderbooks have successfully been filled')
                isBookFull = True
                await asyncio.wait([populateArb()])
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
