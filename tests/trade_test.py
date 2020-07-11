import hmac
import hashlib
import os
import time
import math
import requests
import logging

logger = logging.getLogger('tri_arb_binance')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logHandler = logging.FileHandler('trade_testing.log', mode='a')
# logHandler = logging.StreamHandler()
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

ARBS = [
    'eth'
]
PAIRS = []
for arb in ARBS:
    PAIRS.append(arb + 'usdt')
    PAIRS.append(arb + 'btc')
PAIRS.insert(0, 'btcusdt')

symbolsInfo = requests.get('https://api.binance.com/api/v3/exchangeInfo').json()['symbols']
symbolsInfo = [x for x in symbolsInfo if x['symbol'].lower() in PAIRS]
stepSizes = {
    symbol['symbol']: float(symbol['filters'][2]['stepSize'])
    for symbol in symbolsInfo
}
# print(stepSizes)

trade_url = 'https://api.binance.com/api/v3/order'
api_header = {'X-MBX-APIKEY': str(os.environ["BIN_API"])}


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

def ex_trade(pair, side, quantity):
    params = create_signed_params(pair, side, quantity)
    print(params)
    r = requests.post(trade_url, headers=api_header, params=params)
    return {'content': r.json(), 'status_code': r.status_code, 'params': params}

def ex_arb(arb, is_regular):
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
            break


def get_balances(quote):
    url = "https://api.binance.com/api/v3/account"
    header = {'X-MBX-APIKEY': str(os.environ["BIN_API"])}
    timestamp = int(round(time.time() * 1000))
    recvWindow = 10_000
    query_string = 'recvWindow={}&timestamp={}'.format(recvWindow, timestamp)
    signature = hmac.new(bytes(os.environ["BIN_SECRET"], 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
    params = {
        'recvWindow': recvWindow,
        'timestamp': timestamp,
        'signature': signature
    }
    r = requests.get(url, headers=header, params=params)
    if r.json() is not None:
        balances = [x for x in r.json()['balances'] if float(x['free']) != 0]
        return float([x['free'] for x in balances if x['asset'] == quote][0])


def main():
    # ex_arb('ETH', False)
    print(get_balances('USDT'))
    # print(ex_trade(input('Pair: ').upper(), input('Side: ').upper(), float(input('Quantity: '))))
    # balance_dict = get_balances()
    # balances = [x for x in balance_dict['balances'] if float(x['free']) != 0]
    # print(balances)

if __name__ == '__main__':
    main()
