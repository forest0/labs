#!/usr/bin/env python3

import numpy as np

class Perceptron(object):
    def __init__(self, eta, max_iter):
        self._eta = eta
        self._max_iter = max_iter

    def fit(self, X, y):
        N, d = X.shape
        X = np.hstack([X, np.ones((N, 1))])
        N, d = X.shape

        w = np.zeros(d)
        eta = self._eta

        for it in range(1, 1+self._max_iter):
            # 每轮随机顺序遍历整个训练集，
            # 并没有严格的每次都随机取点
            idxs = np.arange(N)
            np.random.shuffle(idxs)
            err_cnt = 0
            for idx in idxs:
                if y[idx] * np.dot(X[idx], w) <= 0:
                    err_cnt += 1
                    w = w + eta * y[idx] * X[idx].T

            # 这轮没有误分类点，已经找到需要的超平面
            if err_cnt == 0:
                break

            print('iter done: {}/{}, error rate: {}'.format(
                it, self._max_iter, err_cnt / N))

        self._w = w


    def predict(self, X):
        N = X.shape[0]
        X = np.hstack([X, np.ones((N, 1))])
        return np.sign(np.dot(X, self._w))

def load_minist(file_name):
    data_arr, label_arr = [], []
    with open(file_name) as f:
        for line in f:
            label, *data = line.strip().split(',')

            # 二分类
            # 0~4: -1
            # 5~9: +1
            label_arr.append(-1 if int(label) < 5 else 1)

            data_arr.append([int(num) / 255.0 for num in data])

    return np.array(data_arr), np.array(label_arr, dtype=np.int32)

def model_test(model, X, y):
    y_predict = model.predict(X)
    return (y == y_predict).sum() / X.shape[0]

def main():
    train_data, train_label = load_minist('./mnist_train.csv')
    test_data, test_label = load_minist('./mnist_test.csv')

    model = Perceptron(eta=0.0001, max_iter=20)
    model.fit(train_data, train_label)

    print('accuracy', model_test(model, test_data, test_label))

if __name__ == "__main__":
    main()
