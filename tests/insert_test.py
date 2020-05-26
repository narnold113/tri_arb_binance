import numpy as np 

# x = np.array([[100,1], [101,2], [102,3]], np.float64)
# u = np.array([[100.5, 0.5], [101.5, 3], [105,1]], np.float64)
x = np.array([[100,1], [99,2], [98,3]], np.float64)
u = np.array([[100.5, 0.5], [99.5, 3], [90,1]], np.float64)
not_in_index = np.in1d(u[:,0], x[:,0], invert=True)

# ss_index = np.searchsorted(x[:,0], u[not_in_index,0])
ss_index = np.searchsorted(-x[:,0], -u[not_in_index,0], side='left')
new_x = np.insert(x, ss_index, u[not_in_index], axis=0)

# print('array', x[:,0][::-1])
print('Index position:', ss_index)

print(x)
print(new_x)