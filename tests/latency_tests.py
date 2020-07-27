import aiohttp
import asyncio
import hmac
import hashlib
import os
import time
APIKEY = str(os.environ["BIN_API"])
SECRETKEY = str(os.environ["BIN_SECRET"])

def create_signed_params(symbol, side, quantity, price):
    timestamp = int(round(time.time() * 1000))
    query_string = 'symbol={}&side={}&type={}&timeInForce={}&quantity={}&price={}&recvWindow={}&timestamp={}'.format(symbol, side, 'LIMIT', 'GTC', quantity, price, 10_000, timestamp)
    return {
        'symbol': symbol,
        'side': side,
        'type': 'LIMIT',
        'timeInForce': 'GTC',
        'quantity': quantity,
        'price': price,
        'recvWindow': 10_000,
        'timestamp': timestamp,
        'signature': hmac.new(bytes(SECRETKEY, 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
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
                return [float(x['free']) for x in balances if x['asset'] == quote][0]

async def get_market_data():
    url = 'https://api.binance.com/api/v3/ticker/price'
    async with aiohttp.ClientSession() as session:
        async with session.request(method="GET",
                                   url=url) as resp:
            json_content = await resp.json()
            if json_content is not None and resp.status == 200:
                return json_content[0]

async def ex_limitorder(symbol, side, quantity, price):
    trade_url = 'https://api.binance.com/api/v3/order'
    api_header = {'X-MBX-APIKEY': APIKEY}
    params = create_signed_params(symbol, side, quantity, price)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=trade_url, headers=api_header, params=params) as resp:
                json_res = await resp.json()
                if json_res is not None:
                    return {'content': json_res, 'status_code': resp.status, 'params': params}
    except Exception as err:
        logger.exception(err)
        sys.exit()


async def main():
    method = input("Balance, Market or order? ").upper()
    try:
        if method == 'B':
            now = time.time()
            balance = await get_balance('USDT')
            print(balance)
        elif method == 'M':
            now = time.time()
            mdata = await get_market_data()
            print(mdata)
        elif method == 'O':
            symbol = input('symbol: ').upper()
            quantity = input('quantity: ')
            price = input('price: ')
            now = time.time()
            print(await ex_limitorder(symbol, 'BUY', quantity, price))
    except Exception as err:
        print(err)
    print(time.time() - now)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except:
        pass
    finally:
        loop.close()
