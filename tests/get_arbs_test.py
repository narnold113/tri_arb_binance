import requests

def url_handler(url):
    return requests.get(url).json()

def is_white_list(symbol):
    x_list = ['BULL', 'UP', 'DOWN', 'BEAR']
    for x in x_list:
        if x in symbol:
            return True
    return False

def get_arbs():
    exchange_info = url_handler('https://api.binance.com/api/v3/exchangeInfo')
    ticker_info = url_handler('https://api.binance.com/api/v3/ticker/24hr')
    btc_price = url_handler('https://api.binance.com/api/v3/avgPrice?symbol=BTCUSDT')['price']
    arbs = []
    ARBS = []
    PAIRS = []
    # tickers = {
    #     ticker['symbol']: {
    #         'quoteVolume': ticker['quoteVolume'],
    #         'isMarginTradingAllowed': ticker['isMarginTradingAllowed']
    #     }
    #     for ticker in ticker_info
    # }
    tickers = {
        ticker['symbol']: ticker['quoteVolume']
        for ticker in ticker_info
    }
    for item in exchange_info['symbols']:
        if item['symbol'][-3:] == 'BTC' and item['isSpotTradingAllowed'] == True and is_white_list(item['symbol']) == False:
        # if item['symbol'][-3:] == 'BTC' and item['isMarginTradingAllowed'] == True and is_white_list(item['symbol']) == False:
            arb = item['symbol'][0 : len(item['symbol']) - 3]
            arbs.append(arb)
            if arbs.count(arb) == 2:
                ARBS.append(arb)
                PAIRS.append(arb + 'USDT')
                PAIRS.append(arb + 'BTC')
        elif item['symbol'][-4:] == 'USDT' and item['isSpotTradingAllowed'] == True and is_white_list(item['symbol']) == False:
        # elif item['symbol'][-4:] == 'USDT' and item['isMarginTradingAllowed'] == True and is_white_list(item['symbol']) == False:
            arb = item['symbol'][0 : len(item['symbol']) - 4]
            arbs.append(arb)
            if arbs.count(arb) == 2:
                ARBS.append(arb)
                PAIRS.append(arb + 'USDT')
                PAIRS.append(arb + 'BTC')
    ARBS.sort()
    PAIRS.sort()

    arbitrage_book = {
        arb: {
            pair: float(tickers[ticker]) if pair[-4:] == 'USDT' else float(tickers[ticker]) * float(btc_price)
            for pair in PAIRS if pair[:len(arb)] == arb
                for ticker in tickers if ticker == pair
        }
        for arb in ARBS
    }

    low_arbs = [arb for arb in ARBS if arbitrage_book[arb][arb + 'USDT'] < 5_000_000 or arbitrage_book[arb][arb + 'BTC'] < 5_000_000]

    for arb in low_arbs:
        arbitrage_book.pop(arb)

    return [arb.lower() for arb in arbitrage_book.keys()]


# print(len(get_arbs()))
