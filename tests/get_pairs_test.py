import requests

ex_info = requests.get('https://api.binance.com/api/v3/exchangeInfo').json()
# print(ex_info.keys())
# print(ex_info['symbols'][0]['symbol'])

all_pairs = []

for item in ex_info['symbols']:
    if item['symbol'][-3:] == 'BTC':
        all_pairs.append(item['symbol'])
    elif item['symbol'][-4:] == 'USDT':
        all_pairs.append(item['symbol'])

sliced_pairs = [pair[:3] for pair in all_pairs]

# print(len(all_pairs))
print(sliced_pairs.sort())
