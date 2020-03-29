#!/usr/bin/env python3

import sys
# namedtuple' defaults parameter requires python3.7
if sys.version_info.major != 3 or sys.version_info.minor < 7:
    print('at least python3.7 is required')
    sys.exit(1)

import numpy as np
from functools import wraps, partial
import time
import pandas as pd
from collections import namedtuple

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

class MnistClassifier(object):
    def __init__(self, train_data, train_label):
        self._train_data = self._preprocess(train_data)
        self._train_label = train_label

    @timeit
    def _preprocess(self, X):
        return X

    def predict(self, X):
        '''Classify handwritten digits.

        Args:
            X (numpy.ndarray): Digits to be classified, one per row.

        Returns:
            numpy.ndarray: The predicted digits.
        '''
        raise NotImplementedError

class MnistClassifierByDecisionTree(MnistClassifier):
    '''A CART classification tree.'''

    Node = namedtuple('Node', ['split_feature_idx', 'cls', 'left', 'right'],
            # defaults parameter get from right to left, so this means
            # parameter left or right can be None, split_feature_idx or cls
            # are required to be provided by user.
            defaults=[None, None,])

    def __init__(self, train_data, train_label, min_samples_split=2,
            gini_threshold=0.1):
        MnistClassifier.__init__(self, train_data, train_label)

        self._min_samples_split = min_samples_split
        self._gini_threshold = gini_threshold

        self._build_tree()

    def _preprocess(self, X):
        # binarization: 0 if x < 128 else 1
        return np.choose(X < 128, [1, 0])

    def _gini(self, Y):
        if Y.size <= 0: # empty set
            return 0.0 # no uncertainty

        _, counts = np.unique(Y, return_counts=True)
        counts = (counts ** 2) / (Y.size ** 2)
        return 1 - counts.sum()

    def _major_class(self, Y):
        if Y.size <= 0: return None
        unique, counts = np.unique(Y, return_counts=True)
        max_idx = counts.argpartition(-1)[-1]
        return unique[max_idx]

    @timeit
    def _build_tree(self):
        self._tree = self._build_tree_iter(self._train_data,
                self._train_label, np.arange(self._train_data.shape[1]))

    def _build_tree_iter(self, X, Y, available_features_idx):
        if Y.size <= 0: return None

        gini = self._gini(Y)
        if gini < self._gini_threshold or \
                Y.size < self._min_samples_split or \
                len(available_features_idx) == 0:
            return MnistClassifierByDecisionTree.Node(
                    split_feature_idx=None, cls=self._major_class(Y))

        # find the feature that has the minimal gini
        min_gini_idx= None
        min_gini_val = 1.1 # by definition, maximum gini is 1.0
        for current_feature_idx in available_features_idx:
            current_feature = X[:, current_feature_idx]

            # note that we have a binarization preprocess for every feature,
            # so a feature can only be 0 or 1
            positive_subset_idx = current_feature == 1
            negative_subset_idx = current_feature == 0

            gini_with_current_feature = \
                positive_subset_idx.sum() * self._gini(Y[positive_subset_idx]) \
                + negative_subset_idx.sum() * self._gini(Y[negative_subset_idx])
            # this maybe unnecessary if we give a proper initial
            # value to min_gini_val
            gini_with_current_feature /= Y.size

            # TODO: remove it
            assert gini_with_current_feature < 1.1

            if gini_with_current_feature < min_gini_val:
                min_gini_val = gini_with_current_feature
                min_gini_idx = current_feature_idx

        # split X by the feature that has the minimal gini
        split_feature_idx = min_gini_idx
        split_feature = X[:, split_feature_idx]
        positive_subset_idx = split_feature == 1
        negative_subset_idx = split_feature == 0

        # delete this feature from available_features
        available_features_idx = np.setdiff1d(available_features_idx,
                [split_feature_idx])

        # build subtree recursively
        return MnistClassifierByDecisionTree.Node(
            split_feature_idx=split_feature_idx,
            cls=None,
            left=self._build_tree_iter(X[positive_subset_idx],
                Y[positive_subset_idx], available_features_idx),
            right=self._build_tree_iter(X[negative_subset_idx],
                Y[negative_subset_idx], available_features_idx)
        )

    def _predict(self, x):
        root = self._tree
        while root and root.split_feature_idx:
            if x[root.split_feature_idx] == 1:
                root = root.left
            else:
                root = root.right
        return root.cls


    def predict(self, X):
        '''Classify handwritten digits by decision tree.

        Args:
            X (numpy.ndarray): Digits to be classified, one per row.

        Returns:
            numpy.ndarray: The predicted digits.
        '''
        if len(X.shape) == 1: # only one testcase
            X = X.reshape((1, -1))

        X = self._preprocess(X)
        result = []
        for testcase in X:
            result.append(self._predict(testcase))

        return np.array(result, dtype=np.int32)

@timeit
def load_minist(file_name):
    train_data = pd.read_csv(file_name, header=None, dtype=np.int32)
    return train_data.iloc[:, 1:].to_numpy(dtype=np.int32), \
           train_data.iloc[:, 0].to_numpy(dtype=np.int32)

@timeit
def model_test(model, test_data, test_label):
    predict_class = model.predict(test_data)
    correct_amount = (predict_class == test_label).sum()
    accuracy = correct_amount / test_data.shape[0]
    return accuracy

def main():
    train_data, train_label = load_minist('./mnist_train.csv')
    test_data, test_label = load_minist('./mnist_test.csv')

    classifier = MnistClassifierByDecisionTree(train_data,
            train_label,
            min_samples_split=10)
    print('accuracy', model_test(classifier, test_data[:1000], test_label[:1000]))

if __name__ == "__main__":
    main()
