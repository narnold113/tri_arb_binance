import hmac
import hashlib
import os
import time
import requests

# recvWindow = input()

def create_finalParams(symbol, side, type, timeInForce, quantity, price, recvWindow):
    timestamp = int(round(time.time() * 1000))
    query_string = 'symbol={}&side={}&type={}&timeInForce={}&quantity={}&price={}&recvWindow={}&timestamp={}'.format(symbol, side, type, timeInForce, quantity, price, recvWindow, timestamp)
    signature = hmac.new(bytes(os.environ["BIN_SECRET"], 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()

    return {
        'symbol': symbol,
        'side': side,
        'type': type,
        'timeInForce': timeInForce,
        'quantity': quantity,
        'price': price,
        'recvWindow': recvWindow,
        'timestamp': timestamp,
        'signature': signature
    }

url = 'https://api.binance.com/api/v3/order'
params = create_finalParams('EOSUSDT', 'SELL', 'LIMIT', 'GTC', 5, 5, 10_000)
header = {'X-MBX-APIKEY': str(os.environ["BIN_API"])}

r = requests.post(url, headers=header, params=params)
print(r.status_code)
print(r.json())
print('Execution time: ', abs(params['timestamp'] - r.json()['transactTime']))
