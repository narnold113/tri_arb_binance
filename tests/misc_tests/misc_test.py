# import numpy as np

# x = np.array([2], np.float64, ndmin=2)

# print(x)





# ARBS = [
#     'eth' # OK
#     # ,'ltc' # OK
#     # ,'xrp' # OK
#     # ,'bch' # OK
#     # ,'eos' # OK
#     # ,'xmr' # OK
#     # ,'etc' # OK
#     # ,'bsv' # OK
#     # ,'zrx' # OK
#     # ,'trx'
# ]
# PAIRS = []
# for arb in ARBS:
#     PAIRS.append(arb + 'usdt')
#     PAIRS.append(arb + 'btc')
# PAIRS.insert(0, 'btcusdt')
# # print(PAIRS)

# pair_iterator = [pair for pair in PAIRS if pair[:3] == 'eth']
# print(sorted(pair_iterator, reverse=True))
# for pair in pair_iterator:
#     print(pair[-4:])


# import numpy as np

# val = 4
# x = np.array([1,2,3,4])
# if val != x[-1]:
#     x = np.append(x, val)
# # x = np.where(val != x[-1], x, np.append(x, val))
# # x = np.append(x, 5)

# print(x)



# import numpy as np
# import time

# now_timestamp = time.time()
# print(now_timestamp)

# x = np.array([[0.001, now_timestamp]])
# print(x)

# y = np.nan

# if np.isnan(y):
#     print('Y is np.nan')




# import numpy as np
# import time
# ARBS = [
#     'eth' # OK
#     ,'ltc' # OK
#     ,'xrp' # OK
#     ,'bch' # OK
#     ,'eos' # OK
#     ,'xmr' # OK
#     ,'etc' # OK
#     ,'bsv' # OK
#     ,'zrx' # OK
#     ,'trx'
# ]
#
# threshold_array = []
# threshold_tmp = {
#     arb: {
#         'first_timestamp': 0,
#         'values': set()
#     }
#     for arb in ARBS
# }
# # print(type(threshold_tmp['eth']['values']))
# threshold_keep = {
#     arb: {
#         'regular': [],
#         'reverse': []
#     }
#     for arb in ARBS
# }
# print(len(threshold_keep))
#
# # threshold_tmp['eth']['values'].update([1,2,3,4])
# # first_t = time.time()
# # time.sleep(1)
# # threshold_array.extend([first_t, time.time() - first_t, threshold_tmp['eth']['values']])
# # print(threshold_array)
# # threshold_keep['eth']['regular'].append(threshold_array)
# # print(threshold_keep['eth']['regular'][0])
# # threshold_array = np.append(threshold_array, values)
# # threshold_keep['eth']['regular'].append(threshold_array)
# # print(threshold_keep['eth'])








#
# dict = {
#     'eth': 0,
#     'ltc': 1
# }
# dict_values = tuple(dict.values())
# dict_values.append('regular')
# print(dict_values)
# time = 1591114072.180439











#
#
#
#
#
# from statistics import fmean
# import time
#
# ARBS = [
#     'eth',
#     'ltc'
# ]
#
# t_dict = {
#     arb: dict()
#     for arb in ARBS
# }
#
# t_dict['eth']['timestamp'] = time.time()
# x = [1,2,3,4,5]
# # t_dict['low'], t_dict['high'], t_dict['mean'] = min(x), max(x), fmean(x)
# # print(t_dict)
# # if 'timestamp' in t_dict.keys():
# #     print('Timestamp in tdict.keys')
# # else:
# #     print('Nope')
#
# time.sleep(1)
# t_dict['eth']['duration'] = time.time() - t_dict['eth']['timestamp']
# # arr.extend([now, later - now])
# # arr.extend(stats)
# t_dict['eth']['type'] = 'regular'
# print(t_dict)











#
# arb = 'ETH'
#
# x = 'BTCUSDT'
# y = 'ETHBTC'
# z = 'ETHUSDT'
#
# def myFunc(pair):
#     pass
#
#
#
#
#
#
#
#
# balances = [{'asset': 'BTC', 'free': '0.00006779', 'locked': '0.00000000'}, {'asset': 'ETH', 'free': '0.10290524', 'locked': '0.00000000'}, {'asset': 'EOS', 'free': '0.00044000', 'locked': '0.00000000'}, {'asset': 'USDT', 'free': '0.01032688', 'locked': '0.00000000'}, {'asset': 'XRP', 'free': '167.47300000', 'locked': '0.00000000'}]
# usdt = float([x['free'] for x in balances if x['asset'] == 'USDT'][0])
# # print(usdt)
#
#
#
#
#
# times = [[1593639974622, 1593639974580], [1593639974692, 1593639974650], [1593639974770, 1593639974724]]
# y = [x[0] - x[1] for x in times]
# print(y)
# # print(times[1][0] - times[2][1])









# import random
# import time
#
# x = []
# while 1:
#     time.sleep(1)
#     x.append(random.randint(0,1))
#     x_len = len(x)
#     if x_len > 2:
#         x = x[-3:]
#         if x[2] == x[1] and x[2] == x[0]:
#             break
#     else:
#         continue







# Starting from BTCUSDT
# REGULAR = buy buy sell
# REVERSE = sell sell buy

#
# import requests
#
#
# ARBS = [
#     'eth'
# ]
# PAIRS = []
# for arb in ARBS:
#     PAIRS.append(arb + 'usdt')
#     PAIRS.append(arb + 'btc')
# PAIRS.insert(0, 'btcusdt')
#
# symbolsInfo = requests.get('https://api.binance.com/api/v3/exchangeInfo').json()['symbols']
# symbolsInfo = [x for x in symbolsInfo if x['symbol'].lower() in PAIRS]
# stepSizes = {
#     symbol['symbol']: symbol['filters'][2]['stepSize']
#     for symbol in symbolsInfo
# }
# print(stepSizes)


#
# def is_something(number, is_regular):
#     return 'Buy {}'.format(number) if is_regular else 'Sell {}'.format(number)
#
# print(is_something(10, True if 'regular' == 'regular' else False))
#












# import aiohttp
# import time
# import hmac
# import hashlib
# import asyncio
# import os
# from datetime import datetime
#
# async def _get_balance(quote):
#     url = "https://api.binance.com/api/v3/account"
#     header = {'X-MBX-APIKEY': str(os.environ["BIN_API"])}
#     timestamp = int(round(time.time() * 1000))
#     recvWindow = 10_000
#     query_string = 'recvWindow={}&timestamp={}'.format(recvWindow, timestamp)
#     signature = hmac.new(bytes(os.environ["BIN_SECRET"], 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
#     params = {
#         'recvWindow': recvWindow,
#         'timestamp': timestamp,
#         'signature': signature
#     }
# #    await asyncio.sleep(5)
#     async with aiohttp.ClientSession() as session:
#         async with session.request(method="GET",
#                                    url=url,
#                                    headers=header,
#                                    params=params) as resp:
#             json_content = await resp.json()
#             # print(json_content)
#             if json_content is not None:
#                 balances = [x for x in json_content['balances'] if float(x['free']) != 0]
#                 return [[x['free'] for x in balances if x['asset'] == quote][0], resp.status]
#
# async def get_balance(quote):
#     bal = await _get_balance('USDT')
#     print(bal[0]) ### Is a string ###
#
# async def countToTen():
#     for i in range(1,11):
#         print('i: {} | Time: {}'.format(i, datetime.now()))
#         await asyncio.sleep(1)
#
# async def main():
#     coroutines = []
#     coroutines.append(get_balance('USDT'))
#     # coroutines.append(countToTen())
#     await asyncio.wait(coroutines)
#
#
# if __name__ == "__main__":
#     try:
#         loop = asyncio.get_event_loop()
#         loop.run_until_complete(main())
#     except:
#         pass
#     finally:
#         loop.close()





# import get_arbs_test
#
# list = get_arbs_test.get_arbs()
# print(list)
#
#

# import logging
# from statistics import mean
#
# logger = logging.getLogger('tri_arb_binance')
# logger.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# # logHandler = logging.FileHandler('tri_arb_binance.log', mode='a')
# logHandler = logging.StreamHandler()
# logHandler.setLevel(logging.INFO)
# logHandler.setFormatter(formatter)
# logger.addHandler(logHandler)
#
# logger.info('This is a string: {} And this is another string: {}'.format(str('123'), str('456')))
#
# print(mean([1,2,3,4,5]))


# def getWeightedPrice(orders, balance, reverse=False):
#     volume = 0
#     price = 0
#     wp = 0
#     if reverse:
#         for order in orders:
#             volume += order[1]
#             wp += order[0] * (order[1] / balance)
#             if volume >= balance:
#                 remainder = volume - balance
#                 wp -= order[0] * (remainder / balance)
#                 return wp
#     else:
#         for order in orders:
#             volume += order[0] * order[1]
#             wp += order[0] * ((order[0] * order[1]) / balance)
#             if volume >= balance:
#                 remainder = volume - balance
#                 wp -= order[0] * (remainder / balance)
#                 return wp
#
# fills = [
#     {'price': '11688.51000000', 'qty': '0.00241500', 'commission': '0.00098952', 'commissionAsset': 'BNB', 'tradeId': 383819543}
#     # {'price': '11689.51000000', 'qty': '0.00141500', 'commission': '0.00058952', 'commissionAsset': 'BNB', 'tradeId': 383819543},
#     # {'price': '11690.51000000', 'qty': '0.00441500', 'commission': '0.00188952', 'commissionAsset': 'BNB', 'tradeId': 383819543},
#     ]
#
# # for x in fills:
# #     print(x['price'])
#
# # print([[float(x['price']), float(x['qty'])] for x in fills])
#
#
#
# print(getWeightedPrice([[float(x['price']), float(x['qty'])] for x in fills], 28.22775165, False))
#
#









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
from datetime import datetime

logger = logging.getLogger('tri_arb_binance')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logHandler = logging.FileHandler('tri_arb_binance.log', mode='a')
logHandler = logging.StreamHandler()
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)



print(np.average([1,2,3]))









pass
