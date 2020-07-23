# import timeit

# setup1 = '''
# import numpy as np
# import json

# raw_data = str('{"lastUpdateId":4216800757,"bids":[["8908.64000000","0.00224400"],["8908.54000000","0.00428600"],["8908.03000000","0.05658200"],["8908.02000000","0.05654400"],["8907.72000000","0.25846000"],["8907.71000000","0.06139600"],["8907.68000000","0.19700000"],["8907.53000000","0.04000000"],["8907.18000000","0.40980300"],["8907.17000000","0.03000000"],["8907.16000000","0.29460700"],["8907.15000000","0.06561000"],["8907.14000000","0.01951400"],["8907.04000000","0.03368100"],["8906.80000000","1.53202900"],["8906.79000000","0.04510200"],["8906.78000000","1.28984500"],["8906.73000000","0.19700000"],["8906.68000000","0.09822800"],["8906.67000000","0.89844800"],["8906.64000000","0.84164200"],["8906.22000000","0.10898900"],["8906.21000000","0.00859700"],["8906.14000000","0.00163500"],["8906.13000000","0.09757500"],["8906.12000000","0.00113500"],["8906.09000000","0.11222600"],["8906.07000000","2.82958000"],["8905.98000000","5.00000000"],["8905.94000000","0.11222800"],["8905.81000000","0.34813500"],["8905.80000000","0.33685600"],["8905.73000000","0.01122100"],["8905.55000000","0.25000000"],["8905.53000000","0.19700000"],["8905.50000000","0.02000000"],["8905.46000000","0.09882100"],["8905.42000000","0.50000000"],["8905.26000000","0.09748200"],["8905.23000000","0.01929900"],["8905.08000000","0.05000000"],["8905.00000000","0.02000000"],["8904.86000000","0.38115300"],["8904.80000000","0.20000000"],["8904.78000000","0.11100000"],["8904.77000000","0.07500000"],["8904.69000000","0.10000000"],["8904.67000000","0.11300300"],["8904.50000000","0.02000000"],["8904.36000000","0.14700000"],["8904.00000000","0.02000000"],["8903.95000000","0.22461900"],["8903.94000000","0.29100000"],["8903.90000000","0.19700000"],["8903.72000000","0.14550000"],["8903.64000000","3.90000000"],["8903.59000000","0.10000000"],["8903.37000000","0.18935900"],["8903.30000000","0.05848000"],["8903.10000000","0.23159000"],["8903.08000000","0.33696000"],["8903.05000000","0.06639900"],["8902.98000000","0.01230800"],["8902.77000000","0.01949900"],["8902.76000000","0.00200000"],["8902.74000000","0.00303000"],["8902.71000000","0.19700000"],["8902.62000000","0.17572500"],["8902.51000000","0.29100000"],["8902.00000000","0.12500000"],["8901.96000000","0.22467000"],["8901.85000000","0.00780000"],["8901.74000000","0.44886800"],["8901.66000000","0.22930400"],["8901.51000000","0.19700000"],["8901.38000000","0.09757600"],["8901.30000000","0.24000000"],["8901.22000000","2.00000000"],["8901.01000000","5.67961700"],["8900.96000000","0.00158000"],["8900.95000000","0.14700000"],["8900.65000000","0.12798200"],["8900.52000000","1.11787900"],["8900.46000000","0.17548600"],["8900.33000000","0.19700000"],["8900.32000000","0.31725000"],["8900.29000000","0.01505500"],["8900.20000000","0.15738900"],["8900.18000000","0.15600000"],["8900.15000000","0.01383100"],["8900.06000000","0.00466800"],["8900.00000000","0.90009900"],["8899.53000000","0.15900000"],["8899.32000000","0.00123600"],["8899.21000000","0.02675800"],["8899.20000000","0.30300000"],["8899.01000000","0.01958300"],["8898.86000000","0.00896800"],["8898.85000000","0.00896800"],["8898.84000000","5.49203000"]],"asks":[["8909.76000000","0.30910900"],["8909.80000000","0.13435600"],["8909.81000000","0.30909400"],["8909.86000000","0.28289600"],["8909.90000000","0.00607100"],["8910.44000000","0.14000000"],["8910.60000000","0.20006500"],["8910.63000000","0.20000000"],["8910.72000000","0.10539300"],["8910.73000000","0.25776700"],["8910.92000000","1.22328100"],["8910.99000000","0.06330400"],["8911.00000000","2.12710500"],["8911.17000000","0.19701600"],["8911.18000000","0.19700000"],["8911.29000000","0.49768400"],["8911.30000000","0.31115700"],["8911.31000000","0.25000000"],["8911.37000000","0.18643500"],["8911.50000000","0.02000000"],["8911.53000000","0.48983800"],["8911.60000000","0.48977600"],["8911.64000000","1.50000000"],["8912.00000000","0.02776000"],["8912.40000000","0.85217300"],["8912.47000000","0.04410600"],["8912.49000000","0.78800000"],["8912.50000000","0.02000000"],["8912.77000000","0.32429200"],["8912.78000000","0.11200000"],["8912.82000000","0.11223800"],["8912.87000000","0.10000000"],["8912.98000000","0.08400000"],["8913.00000000","0.11508900"],["8913.27000000","2.32687700"],["8913.28000000","2.32682100"],["8913.50000000","0.02000000"],["8913.57000000","0.25000000"],["8913.70000000","0.19700000"],["8913.99000000","0.16835500"],["8914.00000000","0.65211800"],["8914.39000000","0.29400000"],["8914.52000000","0.14400000"],["8914.59000000","0.15150000"],["8914.68000000","0.40000000"],["8914.79000000","0.01949400"],["8914.82000000","0.21000000"],["8914.87000000","0.50000000"],["8914.89000000","0.19700000"],["8914.93000000","0.78000000"],["8914.94000000","0.07500000"],["8914.96000000","0.11222800"],["8915.00000000","4.68591600"],["8915.04000000","0.08021400"],["8915.17000000","0.10000000"],["8915.22000000","0.01005500"],["8915.28000000","0.09747700"],["8915.29000000","0.11146300"],["8915.34000000","0.25000000"],["8915.36000000","0.10000000"],["8915.40000000","0.12500000"],["8915.47000000","0.04643500"],["8915.48000000","0.18393600"],["8915.57000000","0.23393200"],["8915.68000000","0.00200000"],["8915.69000000","1.25000000"],["8915.82000000","0.24000000"],["8915.93000000","0.01951400"],["8915.95000000","0.05857200"],["8916.13000000","0.05000000"],["8916.36000000","0.14400000"],["8916.39000000","0.30600000"],["8916.41000000","0.17572500"],["8916.57000000","0.30000000"],["8916.58000000","0.15300000"],["8916.65000000","0.40996000"],["8916.68000000","0.33644800"],["8916.90000000","0.19700000"],["8917.00000000","3.90225600"],["8917.24000000","0.09956300"],["8917.25000000","0.23416800"],["8917.28000000","1.00000000"],["8917.32000000","0.14400000"],["8917.33000000","0.22428200"],["8917.46000000","0.04990000"],["8917.52000000","0.44832900"],["8917.65000000","0.13714400"],["8917.66000000","0.84160000"],["8917.89000000","0.09763400"],["8918.03000000","0.06289600"],["8918.04000000","0.18869300"],["8918.06000000","0.31444300"],["8918.09000000","0.19700000"],["8918.22000000","0.24907200"],["8918.36000000","0.00113500"],["8918.41000000","0.09757800"],["8918.42000000","0.03200000"],["8918.49000000","0.15150000"],["8918.65000000","0.30300000"],["8918.74000000","0.31420600"]]}')

# json_data = json.loads(raw_data)
# asks = np.array(json_data['asks'], np.float64)
# update_asks = np.array([[8908.64, 0.0034], [8908.65, 0.34],[8990, 0.00023], [10000, 1], [8000, 0.00234]], np.float64)

# notin_ind = np.in1d(update_asks[:,0], asks[:,0], invert=True)
# asks = np.append(asks, update_asks[notin_ind], axis=0)
# inter, orders_ind, updateorders_ind = np.intersect1d(asks[:,0], update_asks[:,0], return_indices=True)
# asks[orders_ind] = update_asks[updateorders_ind]
# delete_ind = np.where(asks == 0)[0]
# asks = np.delete(asks, delete_ind, axis=0)
# new_asks = asks[asks[:,0].argsort()]
# '''

# setup2 = '''
# import numpy as np
# import json

# raw_data = str('{"lastUpdateId":4216800757,"bids":[["8908.64000000","0.00224400"],["8908.54000000","0.00428600"],["8908.03000000","0.05658200"],["8908.02000000","0.05654400"],["8907.72000000","0.25846000"],["8907.71000000","0.06139600"],["8907.68000000","0.19700000"],["8907.53000000","0.04000000"],["8907.18000000","0.40980300"],["8907.17000000","0.03000000"],["8907.16000000","0.29460700"],["8907.15000000","0.06561000"],["8907.14000000","0.01951400"],["8907.04000000","0.03368100"],["8906.80000000","1.53202900"],["8906.79000000","0.04510200"],["8906.78000000","1.28984500"],["8906.73000000","0.19700000"],["8906.68000000","0.09822800"],["8906.67000000","0.89844800"],["8906.64000000","0.84164200"],["8906.22000000","0.10898900"],["8906.21000000","0.00859700"],["8906.14000000","0.00163500"],["8906.13000000","0.09757500"],["8906.12000000","0.00113500"],["8906.09000000","0.11222600"],["8906.07000000","2.82958000"],["8905.98000000","5.00000000"],["8905.94000000","0.11222800"],["8905.81000000","0.34813500"],["8905.80000000","0.33685600"],["8905.73000000","0.01122100"],["8905.55000000","0.25000000"],["8905.53000000","0.19700000"],["8905.50000000","0.02000000"],["8905.46000000","0.09882100"],["8905.42000000","0.50000000"],["8905.26000000","0.09748200"],["8905.23000000","0.01929900"],["8905.08000000","0.05000000"],["8905.00000000","0.02000000"],["8904.86000000","0.38115300"],["8904.80000000","0.20000000"],["8904.78000000","0.11100000"],["8904.77000000","0.07500000"],["8904.69000000","0.10000000"],["8904.67000000","0.11300300"],["8904.50000000","0.02000000"],["8904.36000000","0.14700000"],["8904.00000000","0.02000000"],["8903.95000000","0.22461900"],["8903.94000000","0.29100000"],["8903.90000000","0.19700000"],["8903.72000000","0.14550000"],["8903.64000000","3.90000000"],["8903.59000000","0.10000000"],["8903.37000000","0.18935900"],["8903.30000000","0.05848000"],["8903.10000000","0.23159000"],["8903.08000000","0.33696000"],["8903.05000000","0.06639900"],["8902.98000000","0.01230800"],["8902.77000000","0.01949900"],["8902.76000000","0.00200000"],["8902.74000000","0.00303000"],["8902.71000000","0.19700000"],["8902.62000000","0.17572500"],["8902.51000000","0.29100000"],["8902.00000000","0.12500000"],["8901.96000000","0.22467000"],["8901.85000000","0.00780000"],["8901.74000000","0.44886800"],["8901.66000000","0.22930400"],["8901.51000000","0.19700000"],["8901.38000000","0.09757600"],["8901.30000000","0.24000000"],["8901.22000000","2.00000000"],["8901.01000000","5.67961700"],["8900.96000000","0.00158000"],["8900.95000000","0.14700000"],["8900.65000000","0.12798200"],["8900.52000000","1.11787900"],["8900.46000000","0.17548600"],["8900.33000000","0.19700000"],["8900.32000000","0.31725000"],["8900.29000000","0.01505500"],["8900.20000000","0.15738900"],["8900.18000000","0.15600000"],["8900.15000000","0.01383100"],["8900.06000000","0.00466800"],["8900.00000000","0.90009900"],["8899.53000000","0.15900000"],["8899.32000000","0.00123600"],["8899.21000000","0.02675800"],["8899.20000000","0.30300000"],["8899.01000000","0.01958300"],["8898.86000000","0.00896800"],["8898.85000000","0.00896800"],["8898.84000000","5.49203000"]],"asks":[["8909.76000000","0.30910900"],["8909.80000000","0.13435600"],["8909.81000000","0.30909400"],["8909.86000000","0.28289600"],["8909.90000000","0.00607100"],["8910.44000000","0.14000000"],["8910.60000000","0.20006500"],["8910.63000000","0.20000000"],["8910.72000000","0.10539300"],["8910.73000000","0.25776700"],["8910.92000000","1.22328100"],["8910.99000000","0.06330400"],["8911.00000000","2.12710500"],["8911.17000000","0.19701600"],["8911.18000000","0.19700000"],["8911.29000000","0.49768400"],["8911.30000000","0.31115700"],["8911.31000000","0.25000000"],["8911.37000000","0.18643500"],["8911.50000000","0.02000000"],["8911.53000000","0.48983800"],["8911.60000000","0.48977600"],["8911.64000000","1.50000000"],["8912.00000000","0.02776000"],["8912.40000000","0.85217300"],["8912.47000000","0.04410600"],["8912.49000000","0.78800000"],["8912.50000000","0.02000000"],["8912.77000000","0.32429200"],["8912.78000000","0.11200000"],["8912.82000000","0.11223800"],["8912.87000000","0.10000000"],["8912.98000000","0.08400000"],["8913.00000000","0.11508900"],["8913.27000000","2.32687700"],["8913.28000000","2.32682100"],["8913.50000000","0.02000000"],["8913.57000000","0.25000000"],["8913.70000000","0.19700000"],["8913.99000000","0.16835500"],["8914.00000000","0.65211800"],["8914.39000000","0.29400000"],["8914.52000000","0.14400000"],["8914.59000000","0.15150000"],["8914.68000000","0.40000000"],["8914.79000000","0.01949400"],["8914.82000000","0.21000000"],["8914.87000000","0.50000000"],["8914.89000000","0.19700000"],["8914.93000000","0.78000000"],["8914.94000000","0.07500000"],["8914.96000000","0.11222800"],["8915.00000000","4.68591600"],["8915.04000000","0.08021400"],["8915.17000000","0.10000000"],["8915.22000000","0.01005500"],["8915.28000000","0.09747700"],["8915.29000000","0.11146300"],["8915.34000000","0.25000000"],["8915.36000000","0.10000000"],["8915.40000000","0.12500000"],["8915.47000000","0.04643500"],["8915.48000000","0.18393600"],["8915.57000000","0.23393200"],["8915.68000000","0.00200000"],["8915.69000000","1.25000000"],["8915.82000000","0.24000000"],["8915.93000000","0.01951400"],["8915.95000000","0.05857200"],["8916.13000000","0.05000000"],["8916.36000000","0.14400000"],["8916.39000000","0.30600000"],["8916.41000000","0.17572500"],["8916.57000000","0.30000000"],["8916.58000000","0.15300000"],["8916.65000000","0.40996000"],["8916.68000000","0.33644800"],["8916.90000000","0.19700000"],["8917.00000000","3.90225600"],["8917.24000000","0.09956300"],["8917.25000000","0.23416800"],["8917.28000000","1.00000000"],["8917.32000000","0.14400000"],["8917.33000000","0.22428200"],["8917.46000000","0.04990000"],["8917.52000000","0.44832900"],["8917.65000000","0.13714400"],["8917.66000000","0.84160000"],["8917.89000000","0.09763400"],["8918.03000000","0.06289600"],["8918.04000000","0.18869300"],["8918.06000000","0.31444300"],["8918.09000000","0.19700000"],["8918.22000000","0.24907200"],["8918.36000000","0.00113500"],["8918.41000000","0.09757800"],["8918.42000000","0.03200000"],["8918.49000000","0.15150000"],["8918.65000000","0.30300000"],["8918.74000000","0.31420600"]]}')


# json_data = json.loads(raw_data)
# asks = np.array(json_data['asks'], np.float64)
# update_asks = np.array([[8000, 0.00234], [8909.75, 0.34], [8909.76, 0], [8909.77, 0.00023], [10000, 1]], np.float64)

# not_in_index = np.in1d(update_asks[:,0], asks[:,0], invert=True)
# asks = np.insert(asks, asks[:,0].searchsorted(update_asks[not_in_index,0]), update_asks[not_in_index], axis=0)
# inter, orders_ind, updateorders_ind = np.intersect1d(asks[:,0], update_asks[:,0], return_indices=True)
# asks[orders_ind] = update_asks[updateorders_ind]
# delete_ind = np.where(asks == 0)[0]
# asks = np.delete(asks, delete_ind, axis=0)
# '''

# # print(timeit.timeit(setup1, number=100))
# # print(timeit.timeit(setup1, number=100))





# import numpy as np
# import json

# raw_data = str('{"lastUpdateId":4216800757,"bids":[["8908.64000000","0.00224400"],["8908.54000000","0.00428600"],["8908.03000000","0.05658200"],["8908.02000000","0.05654400"],["8907.72000000","0.25846000"],["8907.71000000","0.06139600"],["8907.68000000","0.19700000"],["8907.53000000","0.04000000"],["8907.18000000","0.40980300"],["8907.17000000","0.03000000"],["8907.16000000","0.29460700"],["8907.15000000","0.06561000"],["8907.14000000","0.01951400"],["8907.04000000","0.03368100"],["8906.80000000","1.53202900"],["8906.79000000","0.04510200"],["8906.78000000","1.28984500"],["8906.73000000","0.19700000"],["8906.68000000","0.09822800"],["8906.67000000","0.89844800"],["8906.64000000","0.84164200"],["8906.22000000","0.10898900"],["8906.21000000","0.00859700"],["8906.14000000","0.00163500"],["8906.13000000","0.09757500"],["8906.12000000","0.00113500"],["8906.09000000","0.11222600"],["8906.07000000","2.82958000"],["8905.98000000","5.00000000"],["8905.94000000","0.11222800"],["8905.81000000","0.34813500"],["8905.80000000","0.33685600"],["8905.73000000","0.01122100"],["8905.55000000","0.25000000"],["8905.53000000","0.19700000"],["8905.50000000","0.02000000"],["8905.46000000","0.09882100"],["8905.42000000","0.50000000"],["8905.26000000","0.09748200"],["8905.23000000","0.01929900"],["8905.08000000","0.05000000"],["8905.00000000","0.02000000"],["8904.86000000","0.38115300"],["8904.80000000","0.20000000"],["8904.78000000","0.11100000"],["8904.77000000","0.07500000"],["8904.69000000","0.10000000"],["8904.67000000","0.11300300"],["8904.50000000","0.02000000"],["8904.36000000","0.14700000"],["8904.00000000","0.02000000"],["8903.95000000","0.22461900"],["8903.94000000","0.29100000"],["8903.90000000","0.19700000"],["8903.72000000","0.14550000"],["8903.64000000","3.90000000"],["8903.59000000","0.10000000"],["8903.37000000","0.18935900"],["8903.30000000","0.05848000"],["8903.10000000","0.23159000"],["8903.08000000","0.33696000"],["8903.05000000","0.06639900"],["8902.98000000","0.01230800"],["8902.77000000","0.01949900"],["8902.76000000","0.00200000"],["8902.74000000","0.00303000"],["8902.71000000","0.19700000"],["8902.62000000","0.17572500"],["8902.51000000","0.29100000"],["8902.00000000","0.12500000"],["8901.96000000","0.22467000"],["8901.85000000","0.00780000"],["8901.74000000","0.44886800"],["8901.66000000","0.22930400"],["8901.51000000","0.19700000"],["8901.38000000","0.09757600"],["8901.30000000","0.24000000"],["8901.22000000","2.00000000"],["8901.01000000","5.67961700"],["8900.96000000","0.00158000"],["8900.95000000","0.14700000"],["8900.65000000","0.12798200"],["8900.52000000","1.11787900"],["8900.46000000","0.17548600"],["8900.33000000","0.19700000"],["8900.32000000","0.31725000"],["8900.29000000","0.01505500"],["8900.20000000","0.15738900"],["8900.18000000","0.15600000"],["8900.15000000","0.01383100"],["8900.06000000","0.00466800"],["8900.00000000","0.90009900"],["8899.53000000","0.15900000"],["8899.32000000","0.00123600"],["8899.21000000","0.02675800"],["8899.20000000","0.30300000"],["8899.01000000","0.01958300"],["8898.86000000","0.00896800"],["8898.85000000","0.00896800"],["8898.84000000","5.49203000"]],"asks":[["8909.76000000","0.30910900"],["8909.80000000","0.13435600"],["8909.81000000","0.30909400"],["8909.86000000","0.28289600"],["8909.90000000","0.00607100"],["8910.44000000","0.14000000"],["8910.60000000","0.20006500"],["8910.63000000","0.20000000"],["8910.72000000","0.10539300"],["8910.73000000","0.25776700"],["8910.92000000","1.22328100"],["8910.99000000","0.06330400"],["8911.00000000","2.12710500"],["8911.17000000","0.19701600"],["8911.18000000","0.19700000"],["8911.29000000","0.49768400"],["8911.30000000","0.31115700"],["8911.31000000","0.25000000"],["8911.37000000","0.18643500"],["8911.50000000","0.02000000"],["8911.53000000","0.48983800"],["8911.60000000","0.48977600"],["8911.64000000","1.50000000"],["8912.00000000","0.02776000"],["8912.40000000","0.85217300"],["8912.47000000","0.04410600"],["8912.49000000","0.78800000"],["8912.50000000","0.02000000"],["8912.77000000","0.32429200"],["8912.78000000","0.11200000"],["8912.82000000","0.11223800"],["8912.87000000","0.10000000"],["8912.98000000","0.08400000"],["8913.00000000","0.11508900"],["8913.27000000","2.32687700"],["8913.28000000","2.32682100"],["8913.50000000","0.02000000"],["8913.57000000","0.25000000"],["8913.70000000","0.19700000"],["8913.99000000","0.16835500"],["8914.00000000","0.65211800"],["8914.39000000","0.29400000"],["8914.52000000","0.14400000"],["8914.59000000","0.15150000"],["8914.68000000","0.40000000"],["8914.79000000","0.01949400"],["8914.82000000","0.21000000"],["8914.87000000","0.50000000"],["8914.89000000","0.19700000"],["8914.93000000","0.78000000"],["8914.94000000","0.07500000"],["8914.96000000","0.11222800"],["8915.00000000","4.68591600"],["8915.04000000","0.08021400"],["8915.17000000","0.10000000"],["8915.22000000","0.01005500"],["8915.28000000","0.09747700"],["8915.29000000","0.11146300"],["8915.34000000","0.25000000"],["8915.36000000","0.10000000"],["8915.40000000","0.12500000"],["8915.47000000","0.04643500"],["8915.48000000","0.18393600"],["8915.57000000","0.23393200"],["8915.68000000","0.00200000"],["8915.69000000","1.25000000"],["8915.82000000","0.24000000"],["8915.93000000","0.01951400"],["8915.95000000","0.05857200"],["8916.13000000","0.05000000"],["8916.36000000","0.14400000"],["8916.39000000","0.30600000"],["8916.41000000","0.17572500"],["8916.57000000","0.30000000"],["8916.58000000","0.15300000"],["8916.65000000","0.40996000"],["8916.68000000","0.33644800"],["8916.90000000","0.19700000"],["8917.00000000","3.90225600"],["8917.24000000","0.09956300"],["8917.25000000","0.23416800"],["8917.28000000","1.00000000"],["8917.32000000","0.14400000"],["8917.33000000","0.22428200"],["8917.46000000","0.04990000"],["8917.52000000","0.44832900"],["8917.65000000","0.13714400"],["8917.66000000","0.84160000"],["8917.89000000","0.09763400"],["8918.03000000","0.06289600"],["8918.04000000","0.18869300"],["8918.06000000","0.31444300"],["8918.09000000","0.19700000"],["8918.22000000","0.24907200"],["8918.36000000","0.00113500"],["8918.41000000","0.09757800"],["8918.42000000","0.03200000"],["8918.49000000","0.15150000"],["8918.65000000","0.30300000"],["8918.74000000","0.31420600"]]}')
# json_data = json.loads(raw_data)

# orderbook = {
#     'asks': np.array(json_data['asks'], np.float64),
#     'bids': np.array(json_data['bids'], np.float64)
# }

# update_book = {
#     'asks': np.array([[8000, 0.00234], [8909.75, 0.34], [8909.76, 0], [8909.77, 0.00023], [10000, 1]], np.float64),
#     'bids': np.array([[9000, 0.00234], [8908.64, 0.34], [8908.63, 0], [8908.62, 0.00023], [8000, 1]], np.float64)
# }
# SIDES = [
#     'asks',
#     'bids'
# ]

# for side in SIDES:
#     ob = orderbook[side]
#     update = update_book[side]

#     not_in_index = np.in1d(update[:,0], ob[:,0], invert=True)
#     ss_index = np.searchsorted(ob[:,0], update[not_in_index,0]) if side == 'asks' else np.searchsorted(-ob[:,0], -update[not_in_index,0])
#     ob = np.insert(ob, ss_index, update[not_in_index], axis=0)
#     inter, orders_ind, updateorders_ind = np.intersect1d(ob[:,0], update[:,0], return_indices=True)
#     ob[orders_ind] = update[updateorders_ind]
#     delete_ind = np.where(ob == 0)[0]
#     ob = np.delete(ob, delete_ind, axis=0)
#     orderbook[side] = ob

# print(orderbook['asks'])



















# import timeit
#
# setup1 = '''
# from datetime import datetime
#
# x = datetime.timestamp(datetime.now())
# '''
#
# setup2 = '''
# import time
# x = time.time()
# '''
# print(timeit.timeit(setup2, number=100000))
#








# import timeit
#
# setup1 = '''
import aiohttp
import asyncio
import hmac
import hashlib
import os
import time
APIKEY = str(os.environ["BIN_API"])
SECRETKEY = str(os.environ["BIN_SECRET"])

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

# async def ex_testorder():


async def main():
    try:
        if input("Balance or Market? ").upper() == 'BALANCE':
            now = time.time()
            balance = await get_balance('USDT')
            print(balance)
        else:
            now = time.time()
            mdata = await get_market_data()
            print(mdata)
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
# '''

# print(timeit.timeit(setup1, number=1))
