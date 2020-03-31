#!/usr/bin/env python3

'''
Plot pruning procedure based on log file.

accuracies.txt and alphas.txt are `greped` from log file.
'''

from matplotlib import pyplot as plt
plt.rcParams['font.sans-serif'] = 'STHeiti'

plt.figure()

############################################################

with open('./alphas.txt') as f:
    Y = []
    for line in f:
        Y.append(float(line.strip()))
# we drop some points to show figure more clearly
Y = Y[:-150]

plt.subplot(1,2,1)

plt.plot(range(len(Y)), Y)
plt.xlabel('剪枝次数')
plt.ylabel('$\\alpha$')

############################################################

with open('./accuracies.txt') as f:
    X, Y = [], []
    for line in f:
        x, y = line.strip().split(' ')
        X.append(int(x))
        Y.append(float(y))

plt.subplot(1,2,2)
plt.plot(X, Y)
plt.xlabel('叶结点数')
plt.ylabel('准确率')

plt.show()
