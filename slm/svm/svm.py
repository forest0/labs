#!/usr/bin/env python3

import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D # registers the 3D projection
from matplotlib import pyplot as plt
import pickle
from functools import wraps, partial
import time
import logging
from enum import Enum
from scipy.spatial.distance import pdist, squareform

logger = logging.getLogger('svm')
logger.setLevel(logging.WARNING)

# some core functions will be timed if you set this to be True.
enable_timing_function = True
def timeit(func=None, *, prefix=""):
    '''Decorator that reports the execution time.
    '''
    if func is None:
        return partial(timeit, prefix=prefix)

    @wraps(func)
    def wrapper(*args, **kwargs):
        if enable_timing_function:
            start = time.time()
        result = func(*args, **kwargs)
        if enable_timing_function:
            end = time.time()
            print('<timeit {} "{}": {} s>'.format(prefix, func.__name__, end - start))
        return result
    return wrapper

def load_dataset(path):
    df = pd.read_csv(path, sep='\t', header=None)
    return df.iloc[:, :2].to_numpy(), df.iloc[:, -1].to_numpy()

def explore_simple_data():
    df = pd.read_csv('linear_separable.txt', sep='\t', header=None)
    print(df.describe())

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(df[0], df[1], c=df[2])

    plt.show()

def get_decision_boundary(train_data, train_label, alphas, b):
    support_vector_idx = alphas > 0

    x = np.arange(train_data[:,0].min(), train_data[:, 0].max(), 0.5)

    alphas = alphas[support_vector_idx]
    train_data = train_data[support_vector_idx]
    train_label = train_label[support_vector_idx]

    # calculate b by a support vector
    b = train_label[0] - (alphas * train_label).dot(
            (train_data * train_data[0]).sum(axis=1))

    # y coordinate on decision boundary
    y = -((alphas * train_label).dot( train_data[:, 0]) * x  + b) \
            / (alphas * train_label).dot( train_data[:, 1])

    return x, y

def visualize_dataset_with_decision_boundary(train_data, train_label, alphas, b):
    print('support vector amount:', (alphas > 0).sum())
    print('corresponding alphas:', alphas[alphas>0])
    print('b in smo:', b)

    support_vector_idx = alphas > 0

    # plot dataset
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(train_data[:,0], train_data[:,1], c=train_label)
    ax.scatter(train_data[support_vector_idx, 0],
            train_data[support_vector_idx,1], marker='x')

    line_x, line_y = get_decision_boundary(train_data, train_label, alphas, b)
    ax.plot(line_x, line_y, c='b')

    plt.show()

class SVMBySMO(object):

    # maybe a enum class is better
    SUPPORT_KERNEL_FUNCTION = ['AsIs', 'Polynomial', 'Gaussian']

    def __init__(self, train_data, train_label, C, epsilon,
            kernel=('AsIs',), max_iter=40):
        self._X = train_data
        self._Y = train_label
        self._C = C
        self._epsilon = epsilon
        self._kernel = kernel

        self._N = train_data.shape[0]
        self._gram = self._calculate_gram()

        self._alphas = np.zeros(self._N)
        self._b = 0.0

        self._errors = -train_label.astype(np.float64)

        self._solve_alphas(max_iter)

    SelectFirstAlphaStrategy = Enum('SelectFirstAlphaStrategy',(
        'Between0AndC',
        'EqualToC',
        'EqualTo0',
    ))

    def _calculate_gram(self):
        kernel_function, *kernel_args = self._kernel
        if kernel_function not in SVMBySMO.SUPPORT_KERNEL_FUNCTION:
            raise ValueError('kernel function: "{}" not support'
                    .format(kernel_function))
        gram = None

        if kernel_function == 'AsIs':
            gram = self._X @ self._X.T
        elif kernel_function == 'Polynomial':
            p = kernel_args[0]
            gram = ((self._X @ self._X.T) + 1) ** p
        elif kernel_function == 'Gaussian':
            s = kernel_args[0]
            pairwise_dists = squareform(pdist(self._X, 'euclidean'))
            gram = np.exp(-pairwise_dists ** 2 / s ** 2)

        return gram

    def _select_first_alpha(self, strategy):
        alphas = self._alphas
        Y = self._Y
        E = self._errors
        epsilon = self._epsilon

        YE = Y * E

        if strategy == SVMBySMO.SelectFirstAlphaStrategy.Between0AndC:

            # first we check samples that hold 0 < alpha_i < C
            abs_YE = np.abs(YE)
            indexes = np.nonzero(np.logical_and(
                np.logical_and(0 < alphas, alphas < self._C),
                abs_YE > epsilon
            ))[0]
            negative_errors = -abs_YE[indexes]

        elif strategy == SVMBySMO.SelectFirstAlphaStrategy.EqualToC:

            # then we check samples that hold alpha_i == C
            indexes = np.nonzero(np.logical_and(
                alphas == self._C,
                YE > epsilon
            ))[0]
            negative_errors = -YE[indexes]

        else:
            assert strategy == SVMBySMO.SelectFirstAlphaStrategy.EqualTo0

            # we last check samples that hold alpha_i == 0,
            # because alpha_i == 0 corresponding to the most samples.
            indexes = np.nonzero(np.logical_and(
                alphas == 0,
                YE < -epsilon
            ))[0]
            negative_errors = YE[indexes]

        return indexes[negative_errors.argsort()]

    def _two_alpha_target_function_will_decrease_enough_on(self, i, j):
        # TODO:
        # how to check target function decrease enough,
        # I checked the gradient but it seems large enough.
        #
        # This function always return True now.
        '''We judge if alpha_i and alpha_j will lead two alpha's target function
        decrease enough by gradient.
        '''
        E = self._errors
        Y = self._Y
        alphas = self._alphas
        gram = self._gram

        v1 = E[i] + Y[i] - self._b - alphas[i] * Y[i] * gram[i, i] - \
                alphas[j] * Y[j] * gram[i, j]
        v2 = E[j] + Y[j] - self._b - alphas[i] * Y[i] * gram[i ,j] - \
                alphas[j] * Y[j] * gram[j, j]
        var_sigma = alphas[i] * Y[i] + alphas[j] * Y[j]

        gradient = alphas[j] * (gram[i, i] + gram[j, j] - 2 * gram[i, j]) - \
                Y[j] * (var_sigma * (gram[i, i] + gram[i, j]) + Y[i] - Y[j] - v1 + v2)
        logger.debug('gradient is %f', gradient)

        #  return gradient > 0
        return True

    def _select_second_alpha(self, first_alpha_idx, second_alpha_seen):
        def valid(first_alpha_idx, second_alpha_idx):
            if second_alpha_idx != first_alpha_idx and \
               second_alpha_idx not in second_alpha_seen and \
               self._two_alpha_target_function_will_decrease_enough_on(
                        first_alpha_idx, second_alpha_idx):
                return True
            return False

        E = self._errors
        alphas = self._alphas
        C = self._C

        if E[first_alpha_idx] > 0: # we want small E2 to maximum |E1 - E2|
            # we need two smallest errors, in case the smallest is E1
            indexes = E.argpartition(1)[:2]
            # guarantee that the first one is smallest
            if E[indexes[0]] > E[indexes[1]]:
                indexes = [indexes[1], indexes[0]]
            idx = indexes[0]
            if idx == first_alpha_idx:
                idx = indexes[1]
        elif E[first_alpha_idx] < 0: # we want large E2 to maximum |E1 - E2|
            indexes = E.argpartition(-2)[-2:]
            if E[indexes[0]] < E[indexes[1]]:
                indexes = [indexes[1], indexes[0]]
            idx = indexes[0]
            if idx == first_alpha_idx:
                idx = indexes[1]
        else: # E1 == 0, we have to check smallest and biggest ones.
            small_indexes = E.argpartition(1)[:2]
            big_indexes = E.argpartition(-2)[-2:]
            indexes = np.hstack(small_indexes, big_indexes)
            Es = np.abs(E[indexes])
            indexes = Es.argsort()
            idx = indexes[-1]
            if idx == first_alpha_idx:
                idx == indexes[-2]

        if valid(first_alpha_idx, idx):
            return idx

        alphas_between_0_and_C_indexes = np.nonzero(np.logical_and(
            0 < alphas, alphas < C
        ))[0]
        for idx in alphas_between_0_and_C_indexes:
            if valid(first_alpha_idx, idx):
                return idx

        alphas_equal_to_0_indexes = np.nonzero(alphas == 0)[0]
        for idx in alphas_equal_to_0_indexes:
            if valid(first_alpha_idx, idx):
                return idx

        return None

    def _update_error(self, idx, alpha_old):
        self._errors += (self._alphas[idx] - alpha_old) * self._Y[idx] * \
                self._gram[idx]

    def _solve_two_alpha(self, i, j):
        logger.debug('trying to solve on (%d,%d)', i, j)
        gram = self._gram
        alphas = self._alphas
        Y = self._Y
        C = self._C
        E = self._errors

        alpha_i_old, alpha_j_old = alphas[i], alphas[j]

        if Y[i] == Y[j]:
            L = max(0, alpha_j_old + alpha_i_old - C)
            H = min(C, alpha_j_old + alpha_i_old)
        else:
            L = max(0, alpha_j_old - alpha_i_old)
            H = min(C, C + alpha_j_old - alpha_i_old)
        if L == H:
            # only one possible solution
            logger.debug('L == H')
            return False

        eta = gram[i, i] + gram[j, j] - 2 * gram[i, j]
        if eta == 0:
            # 0 cant be denominator
            logger.debug('eta == 0')
            return False

        alphas[j] += Y[j] * (E[i] - E[j]) / eta
        alphas[j] = alphas[j].clip(L, H)
        # alphas[j] may stays the same as before
        if abs(alphas[j] - alpha_j_old) < 1e-5:
            return False
        self._update_error(j, alpha_j_old)

        alphas[i] += Y[i] * Y[j] * (alpha_j_old - alphas[j])
        self._update_error(i, alpha_i_old)

        b1 = self._b - E[i] - Y[i] * gram[i, i] * (alphas[i] - alpha_i_old) - \
            Y[j] * gram[i, j] * (alphas[j] - alpha_j_old)
        b2 = self._b - E[j] - Y[i] * gram[i, j] * (alphas[i] - alpha_i_old) - \
            Y[j] * gram[j, j] * (alphas[j] - alpha_j_old)

        if 0 < alphas[i] < C: self._b = b1
        elif 0 < alphas[j] < C: self._b = b2
        else: self._b = (b1 + b2) / 2

        logger.debug('succeed to solve on (%d,%d)', i, j)
        return True

    @timeit
    def _solve_alphas(self, max_iter=40):
        iter_cnt = 0
        strategy = SVMBySMO.SelectFirstAlphaStrategy.Between0AndC
        while iter_cnt < max_iter:

            first_alpha_indexes = self._select_first_alpha(strategy)
            if first_alpha_indexes.size == 0 and strategy == \
                        SVMBySMO.SelectFirstAlphaStrategy.EqualTo0:
                logger.info('all points satisfy KKT, break')
                break

            first_alpha_tried_idx = 0
            first_alpha_len = first_alpha_indexes.size
            second_alpha_seen = set()
            last_iter_has_progress = -2
            while first_alpha_tried_idx < first_alpha_len:
                first_alpha_idx = first_alpha_indexes[first_alpha_tried_idx]

                second_alpha_idx = self._select_second_alpha(first_alpha_idx, second_alpha_seen)
                if not second_alpha_idx:
                    first_alpha_tried_idx += 1
                    second_alpha_seen = set()
                    continue

                if not self._solve_two_alpha(first_alpha_idx, second_alpha_idx):
                    second_alpha_seen.add(second_alpha_idx)
                    continue

                last_iter_has_progress = iter_cnt
                break

            if last_iter_has_progress != iter_cnt:
                # search failed on last strategy
                # we choose next most promising strategy

                if strategy == SVMBySMO.SelectFirstAlphaStrategy.Between0AndC:
                    strategy = SVMBySMO.SelectFirstAlphaStrategy.EqualToC
                    continue
                elif strategy == SVMBySMO.SelectFirstAlphaStrategy.EqualToC:
                    strategy = SVMBySMO.SelectFirstAlphaStrategy.EqualTo0
                    continue

            # reset default strategy that is most promising
            strategy = SVMBySMO.SelectFirstAlphaStrategy.Between0AndC

            logger.debug('iter %d: done', iter_cnt+1)

            if iter_cnt - last_iter_has_progress > 1:
                if iter_cnt == 0:
                    logger.warning('no progress at the first iteration, break')
                else:
                    logger.info('no progress after 2 iterations, break')
                break

            iter_cnt += 1

    def get_params(self):
        return self._alphas, self._b

    def predict(self, X):
        support_vector_idx = self._alphas > 0
        alphas = self._alphas[support_vector_idx]
        Y = self._Y[support_vector_idx]

        K = self._X[support_vector_idx]
        ret = None

        kernel_function, *kernel_args = self._kernel
        if kernel_function == 'AsIs':
            Kb = K.dot(self._X[support_vector_idx][0])
            K = K @ X.T
        elif kernel_function == 'Polynomial':
            p = kernel_args[0]
            Kb = (K.dot(self._X[support_vector_idx][0]) + 1) ** p
            K = ((K @ X.T) + 1) ** p
        elif kernel_function == 'Gaussian':
            s = kernel_args[0]
            Kb = np.exp(
                -(((K - self._X[support_vector_idx][0]) ** 2).sum(axis=1) \
                    / s ** 2)
            )
            K_buf = np.zeros((support_vector_idx.sum(), X.shape[0]))
            # TODO: can we remove this loop?
            for i in range(X.shape[0]):
                K_buf[:, i] = np.exp(
                    -(((K - X[i]) ** 2).sum(axis=1) \
                        / s ** 2)
                )
            K = K_buf
        else:
            raise ValueError('kernel function: "{}" not support'
                    .format(kernel_function))

        b = Y[0] - (alphas * Y).dot(Kb)
        ret = K.T.dot(alphas * Y) + b
        #  sign function
        return np.where(ret < 0, -1, 1)

def test_svm_smo_asis():
    train_data, train_label = load_dataset('linear_separable.txt')
    s = SVMBySMO(train_data, train_label, 0.6, 1e-3, max_iter=40)
    visualize_dataset_with_decision_boundary(train_data, train_label,
            *s.get_params())

def test_predict():
    def generate_test_data(amount):
        data = np.zeros((amount, 2))

        data[:, 0] = np.random.normal(4.79, 3.1, amount)
        data[:, 1] = np.random.normal(0, 1.46, amount)

        return data

    train_data, train_label = load_dataset('linear_separable.txt')

    fig = plt.figure()
    ax1 = fig.add_subplot(121)
    ax1.scatter(train_data[:,0], train_data[:,1], c=train_label)

    s = SVMBySMO(train_data, train_label, 0.6, 1e-3, max_iter=40)

    line_x, line_y = get_decision_boundary(train_data, train_label, *s.get_params())
    ax1.plot(line_x, line_y, c='b')

    test_data = generate_test_data(20)
    predict_label = s.predict(test_data)

    ax2 = fig.add_subplot(122)
    ax2.scatter(test_data[:,0], test_data[:,1], c=predict_label)
    ax2.plot(line_x, line_y, c='b')

    plt.show()

def explore_non_linear_separable_data():
    df = pd.read_csv('nonlinear_separable_train.txt', sep='\t', header=None)
    print(df.describe())

    fig = plt.figure()

    # we plot in input space first
    ax1 = fig.add_subplot(121)
    ax1.title.set_text('Input Space')
    ax1.scatter(df[0], df[1], c=df[2])

    # we can see that this dataset is indeed nonlinear separable,
    # then we apply a kernel trick, use polynomial kernel function
    # to map the dataset to another space.
    input_X, Y = df.iloc[:, :2].to_numpy(), df.iloc[:, -1].to_numpy()
    N = input_X.shape[0]

    # we map R^2 to R^3
    feature_X = np.zeros((N, 3))
    feature_X[:, 0] = input_X[:, 0] ** 2
    feature_X[:, 1] = np.sqrt(2) * input_X[:, 0] * input_X[:, 1]
    feature_X[:, 2] = input_X[:, 1] ** 2

    # plot in feature space
    ax2 = fig.add_subplot(122, projection='3d')
    ax2.title.set_text('Feature Space')
    ax2.scatter3D(feature_X[:, 0], feature_X[:, 1], feature_X[:, 2], c=Y)

    plt.show()

def test_linear_method_on_nonlinear_separable_data():
    train_data, train_label = load_dataset('nonlinear_separable_train.txt')
    s = SVMBySMO(train_data, train_label, 0.6, 1e-3, max_iter=100)
    visualize_dataset_with_decision_boundary(train_data, train_label,
            *s.get_params())

def explore_kernel_trick(kernel, C):
    train_data, train_label = load_dataset('nonlinear_separable_train.txt')

    fig = plt.figure()
    ax1 = fig.add_subplot(121)
    ax1.scatter(train_data[:,0], train_data[:,1], c=train_label)
    ax1.title.set_text('Origin')

    s = SVMBySMO(train_data, train_label, C, 1e-4, kernel=kernel, max_iter=20000)
    # we try to verify that our kernel implementation, so we just predict on train_data
    predict_label = s.predict(train_data)

    ax2 = fig.add_subplot(122)
    ax2.scatter(train_data[:,0], train_data[:,1], c=predict_label)
    ax2.title.set_text('kernel: {}'.format(kernel[0]))

    # plot support vector
    alphas = s.get_params()[0]
    support_vector_idx = np.nonzero(np.logical_and(0 < alphas, alphas < C))[0]
    ax2.scatter(train_data[support_vector_idx,0],
                train_data[support_vector_idx,1],
                marker='x')

    print('support vertor amount:', support_vector_idx.size)

    plt.show()

def calculate_accuracy(Y, predict_Y):
    return (Y == predict_Y).sum() / Y.size

def test_accuracy_on_nonlinear_separable(**kwargs):
    train_data, train_label = load_dataset('nonlinear_separable_train.txt')
    test_data, test_label = load_dataset('nonlinear_separable_test.txt')

    s = SVMBySMO(train_data, train_label, **kwargs)
    predict_label = s.predict(test_data)

    accuracy = calculate_accuracy(test_label, predict_label)
    print('accuracy:', accuracy)


def main():
    explore_simple_data()

    test_svm_smo_asis()

    test_predict()

    explore_non_linear_separable_data()

    test_linear_method_on_nonlinear_separable_data()

    # this two functions may take several seconds to run
    explore_kernel_trick(('Polynomial', 2), 200)
    explore_kernel_trick(('Gaussian', 1.3), 100)

    # this two functions may take several seconds to run
    test_accuracy_on_nonlinear_separable(C=200, epsilon=1e-4,
        kernel=('Polynomial', 2), max_iter=20000)
    test_accuracy_on_nonlinear_separable(C=100, epsilon=1e-4,
        kernel=('Gaussian', 1.3), max_iter=20000)

def configure_logger():
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
            '%(name)s -- [%(levelname)s] %(funcName)s:%(lineno)d %(message)s')

    ch.setFormatter(formatter)
    logger.addHandler(ch)

if __name__ == "__main__":
    configure_logger()

    main()
