import requests
import time
from datetime import datetime

url = 'https://www.binance.com/api/v3/depth?symbol=BNBBTC&limit=10'
r = requests.get(url)
print(r.status_code)


# request_datetime = datetime.strptime(r.headers['Date'], '%b, %d %b %Y %H:%M:%S %Z')
# request_timestamp = datetime.timestamp()
# print(request_datetime)

# while 1:
#     r = requests.get(url)
#     print(r.status_code)
#     print(r.headers['X-MBX-USED-WEIGHT'])
#     print(r.headers['X-MBX-USED-WEIGHT-1m'])
#     print(datetime.now(), '\n')

#     # time.sleep(0.1)

