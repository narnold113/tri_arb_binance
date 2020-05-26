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




import numpy as np 
import time
ARBS = [
    'eth' # OK
    ,'ltc' # OK
    ,'xrp' # OK
    ,'bch' # OK
    ,'eos' # OK
    ,'xmr' # OK
    ,'etc' # OK
    ,'bsv' # OK
    ,'zrx' # OK
    ,'trx'
]

threshold_array = []
threshold_tmp = {
    arb: {
        'first_timestamp': 0,
        'values': set()
    }
    for arb in ARBS
}
print(type(threshold_tmp['eth']['values']))
threshold_keep = {
    arb: {
        'regular': [],
        'reverse': []
    }
    for arb in ARBS
}

threshold_tmp['eth']['values'].update([1,2,3,4])
first_t = time.time()
time.sleep(1)
threshold_array.extend([first_t, time.time() - first_t, threshold_tmp['eth']['values']])
print(threshold_array)
threshold_keep['eth']['regular'].append(threshold_array)
print(threshold_keep['eth']['regular'][0])
# threshold_array = np.append(threshold_array, values)
# threshold_keep['eth']['regular'].append(threshold_array)
# print(threshold_keep['eth'])
