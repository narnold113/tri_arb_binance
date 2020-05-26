import requests 
import numpy as np 


pair = 'btcusdt'
r = requests.get('https://www.binance.com/api/v3/depth?symbol={}&limit=100'.format(pair.upper())).json()
# r_json = r.json()
print(r)


na_bids = np.array(r['bids'], np.float64)

# print(na_bids)