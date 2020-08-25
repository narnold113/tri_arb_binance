def getWeightedPrice(orders, balance, reverse=False, isRecursion=False):
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
                if isRecursion:
                    return wp
                else:
                    return [wp, volume / balance]
        return [getWeightedPrice(orders, volume, True, True), volume / balance]
    else:
        for order in orders:
            volume += order[0] * order[1]
            wp += order[0] * ((order[0] * order[1]) / balance)
            if volume >= balance:
                remainder = volume - balance
                wp -= order[0] * (remainder / balance)
                if isRecursion:
                    return wp
                else:
                    return [wp, volume / balance]
        return [getWeightedPrice(orders, volume, False, True), volume / balance]


balance = 450
orders = [[50, 1], [51,2], [52,1], [53,5]]

print(getWeightedPrice(orders, balance))
