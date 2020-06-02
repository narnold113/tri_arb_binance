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
