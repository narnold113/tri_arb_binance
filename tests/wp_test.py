def getWeightedPrice(orders, balance, reverse=False):
    volume = 0
    price = 0
    wp = 0
    if reverse:
        for order in orders:
            volume += order[1]
            wp += order[0] * (order[1] / balance)
            if volume >= balance:
                remainder = volume - balance
                wp -= order[0] * (remainder / balance)
                return wp
    else:
        for order in orders:
            volume += order[0] * order[1]
            wp += order[0] * ((order[0] * order[1]) / balance)
            if volume >= balance:
                remainder = volume - balance
                wp -= order[0] * (remainder / balance)
                return wp


orderbook = [[100, 1], [200, 1], [300,1], [400,1]]

wp = getWeightedPrice(orderbook, 4, reverse=True)

print(wp)
