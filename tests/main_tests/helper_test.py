from configparser import ConfigParser
import numpy as np

# balances = [100, 200, 600]
# orderbook = [[100, 1], [200, 1], [300,1], [400,1]]

def getWeightedPrice(orders, balance, reverse=False):
    weightedPrices = []
    for bal in balance:
        volume = 0
        price = 0
        wp = 0
        remainder = 0
        if reverse:
            for order in orders:
                volume += order[1]
                wp += order[0] * (order[1] / bal)
                if volume >= bal:
                    remainder = volume - bal
                    wp -= order[0] * (remainder / bal)
                    weightedPrices.append(wp)
                    break
        else:
            for order in orders:
                volume += order[0] * order[1]
                wp += order[0] * ((order[0] * order[1]) / bal)
                if volume >= bal:
                    remainder = volume - bal
                    wp -= order[0] * (remainder / bal)
                    weightedPrices.append(wp)
                    break
    return np.array(weightedPrices, np.float64)

# res = getWeightedPrice(orderbook, balances, reverse=False)
# print(res)
# print(type(res))
# print(res.dtype)


def read_db_config(filename='config.ini', section='mariadb'):
    parser = ConfigParser()
    parser.read(filename)
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception('{0} not found in the {1} file'.format(section, filename))
    return db