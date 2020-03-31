#!/usr/bin/env python3

import sys
import numpy as np
from functools import wraps, partial
import time
import pandas as pd
from collections import deque

import tracemalloc
import linecache
import os
import copy

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

    # we dnot use namedtuple here because we need modify it a lot.
    #  Node = namedtuple('Node',
    #          ['id', 'split_feature_idx', 'cls', 'parent',
    #              'single_node_gini', 'subtree_node_gini',
    #              'left', 'right',
    #              'left_size', 'right_size'],
    #          # defaults parameter get from right to left, so this means
    #          # parameter left or right can be None, split_feature_idx or cls
    #          # are required to be provided by user.
    #          defaults=[None, None, None, None, 0, 0,])

    class Node(object):
        # optimize memory usage
        __slots__ = ['split_feature_idx', 'cls', 'parent', 'single_node_gini',
                'subtree_node_gini', 'left', 'right', 'left_size', 'right_size',
                'leaf_node_amount']

        def __init__(self, split_feature_idx, cls, parent,
                single_node_gini, subtree_node_gini=0.0, left=None, right=None,
                left_size=0, right_size=0, leaf_node_amount=0):
            # we dont use self.__dict__.update(kwargs) to make it clear
            self.split_feature_idx = split_feature_idx
            self.cls = cls
            self.parent = parent
            self.single_node_gini = single_node_gini
            self.subtree_node_gini = subtree_node_gini
            self.left = left
            self.right = right
            self.left_size = left_size
            self.right_size = right_size
            self.leaf_node_amount = leaf_node_amount

    def __init__(self, train_data, train_label, min_samples_split=2,
            gini_threshold=0.1):
        MnistClassifier.__init__(self, train_data, train_label)

        self._min_samples_split = min_samples_split
        self._gini_threshold = gini_threshold

        self._build_tree()

    def _preprocess(self, X, predict=False):
        # binarization: 0 if x < 128 else 1
        if not predict:
            N, d = X.shape
            roi = []
            for i in range(d):
                _, counts = np.unique(X[:, i], return_counts=True)
                if counts[0] == 0 or counts[0] == N:
                    # the values on this column are all same
                    continue
                roi.append(i)
            self._roi_columns_idx = roi

        #  print('features before filtering:', d) # 784
        #  print('features after filtering:', len(roi)) # 717
        binarized = np.choose(X < 128, [1, 0])
        return binarized[:, self._roi_columns_idx]

    def _is_leaf(self, root):
        return root and root.split_feature_idx is None

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
    def _display_top(self, snapshot, key_type='lineno', limit=3):
        '''Copied from https://stackoverflow.com/questions/552744/how-do-i-profile-memory-usage-in-python.'''
        snapshot = snapshot.filter_traces((
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
        ))
        top_stats = snapshot.statistics(key_type)

        print("Top %s lines" % limit)
        for index, stat in enumerate(top_stats[:limit], 1):
            frame = stat.traceback[0]
            # replace "/path/to/module/file.py" with "module/file.py"
            filename = os.sep.join(frame.filename.split(os.sep)[-2:])
            print("#%s: %s:%s: %.1f KiB"
                % (index, filename, frame.lineno, stat.size / 1024))
            line = linecache.getline(frame.filename, frame.lineno).strip()
            if line:
                print('    %s' % line)

        other = top_stats[limit:]
        if other:
            size = sum(stat.size for stat in other)
            print("%s other: %.1f KiB" % (len(other), size / 1024))
        total = sum(stat.size for stat in top_stats)
        print("Total allocated size: %.1f KiB" % (total / 1024))

    @timeit
    def _build_tree(self):
        def get_leaf_nodes(root):
            # breadth first search, to get all leaf nodes
            nodes = deque([root])
            leaf_nodes = []
            while len(nodes):
                node = nodes.popleft()
                if self._is_leaf(node):
                    leaf_nodes.append(node)
                if node.left:
                    nodes.append(node.left)
                if node.right:
                    nodes.append(node.right)
            return leaf_nodes

        def update_from_leaf_to_root(leaf_node):
            '''Fill subtree_node_gini all the path to root.'''
            cur = leaf_node.parent
            leaf_node_sample_amount = cur.left_size
            if cur.right is leaf_node:
                leaf_node_sample_amount = cur.right_size

            assert leaf_node_sample_amount > 0

            add = leaf_node_sample_amount * leaf_node.single_node_gini

            while cur:
                cur.subtree_node_gini += add
                cur.leaf_node_amount += 1

                cur = cur.parent

        #  tracemalloc.start()

        # we build tree first
        self._tree = self._build_tree_iter(self._train_data,
                self._train_label, np.arange(self._train_data.shape[1]))

        # update subtree_node_gini from leaves to root
        leaf_nodes = get_leaf_nodes(self._tree)
        for leaf_node in leaf_nodes:
            update_from_leaf_to_root(leaf_node)

        #  snapshot = tracemalloc.take_snapshot()
        #  self._display_top(snapshot)

    def _build_tree_iter(self, X, Y, available_features_idx, parent=None):
        if Y.size <= 0: return None

        gini = self._gini(Y)
        cls = self._major_class(Y)
        if gini < self._gini_threshold or \
                Y.size < self._min_samples_split or \
                len(available_features_idx) == 0:
            return MnistClassifierByDecisionTree.Node(#id=self._node_id,
                    split_feature_idx=None, cls=cls,
                    parent=parent, single_node_gini=gini)

        # find the feature that has the minimal gini
        min_gini_idx= None
        min_gini_val = 1.0 # by definition, maximum gini is 1.0
        for current_feature_idx in available_features_idx:
            current_feature = X[:, current_feature_idx]

            # note that we have a binarization preprocess for every feature,
            # so a feature can only be 0 or 1
            positive_subset_idx = current_feature == 1
            left_size = positive_subset_idx.sum()
            negative_subset_idx = current_feature != 1
            right_size = negative_subset_idx.sum()

            gini_with_current_feature = \
                left_size * self._gini(Y[positive_subset_idx]) \
                + right_size * self._gini(Y[negative_subset_idx])
            # this maybe unnecessary if we give a proper initial
            # value to min_gini_val
            gini_with_current_feature /= Y.size

            assert 0 <= gini_with_current_feature <= 1.0

            if gini_with_current_feature < min_gini_val:
                min_gini_val = gini_with_current_feature
                min_gini_idx = current_feature_idx

        # split X by the feature that has the minimal gini
        split_feature_idx = min_gini_idx
        split_feature = X[:, split_feature_idx]
        positive_subset_idx = split_feature == 1
        left_size = positive_subset_idx.sum()
        negative_subset_idx = split_feature != 1
        right_size = negative_subset_idx.sum()

        # delete this feature from available_features
        available_features_idx = np.setdiff1d(available_features_idx,
                [split_feature_idx])

        # build subtree recursively
        # we need pass parent to build_iter, so we create a leaf node first,
        # then update its children
        new_node = MnistClassifierByDecisionTree.Node(
            #  id=self._node_id,
            split_feature_idx=split_feature_idx,
            cls=cls,
            single_node_gini=gini,
            parent=parent,
            left_size=left_size,
            right_size=right_size
        )
        left = self._build_tree_iter(X[positive_subset_idx],
            Y[positive_subset_idx], available_features_idx, new_node)
        right = self._build_tree_iter(X[negative_subset_idx],
            Y[negative_subset_idx], available_features_idx, new_node)
        new_node.left = left
        new_node.right = right

        return new_node

    def _prune_tree(self, root):
        '''Prune out just one interval node, returns the pruned tree,
        the passed-in root tree is NOT modified.
        '''
        def g_t_func(node):
            assert node
            assert not self._is_leaf(node)

            assert node.leaf_node_amount > 1

            return (node.single_node_gini * (node.left_size + node.right_size) - \
                    node.subtree_node_gini ) / (node.leaf_node_amount - 1)

        def get_min_g_t_node(root):
            '''Returns the internal node that has the g(t) value.'''
            if not root or self._is_leaf(root):
                return None

            queue = deque([root])
            min_g_t = None
            min_g_t_node = None
            while len(queue):
                node = queue.popleft()
                if self._is_leaf(node): continue

                cur_g_t = g_t_func(node)
                assert cur_g_t >= 0

                if min_g_t is None or cur_g_t < min_g_t:
                    min_g_t = cur_g_t
                    min_g_t_node = node

                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)

            print('min_g_t:', min_g_t)
            return min_g_t_node

        def update_leaf_node_amount(start_node, delta=-1):
            '''start_node is the pruned subtree, after pruning this subtree
            becomes a leaf node, so we must update its parents leaf_node_amount.

            And we use delta as a hint to plus or minus.
            '''
            assert start_node

            cur = start_node.parent
            delta = delta * (start_node.leaf_node_amount - 1)

            while cur:
                cur.leaf_node_amount += delta

                cur = cur.parent

        if not root or self._is_leaf(root):
            return None

        min_g_t_node = get_min_g_t_node(root)

        if min_g_t_node is root:
            return None

        new_node = MnistClassifierByDecisionTree.Node(
                split_feature_idx=None,
                cls=min_g_t_node.cls,
                parent=min_g_t_node.parent,
                single_node_gini=min_g_t_node.single_node_gini)

        # we first prune the original tree in place to get the result,
        # then we make a copy of the result to be returned later,
        # but befure return we need bring to original tree back.
        parent = min_g_t_node.parent
        is_left = True
        # prune
        if min_g_t_node is parent.left:
            parent.left = new_node
        else:
            parent.right = new_node
            is_left = False

        # sub leaf node amount
        update_leaf_node_amount(min_g_t_node, -1)
        new_tree = copy.deepcopy(root)

        # bring the original tree back
        # add leaf node amount back
        update_leaf_node_amount(min_g_t_node, +1)
        if is_left:
            parent.left = min_g_t_node
        else:
            parent.right = min_g_t_node

        return new_tree

    @timeit
    def _get_pruned_trees(self):
        pruned_trees = []
        cur_tree = self._tree
        while cur_tree:
            pruned_trees.append(cur_tree)
            cur_tree = self._prune_tree(cur_tree)
        return pruned_trees

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

        X = self._preprocess(X, predict=True)
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

# env: i7-8700k
# time: 19min20s
# memory: 4.2GB
@timeit
def main():
    train_data, train_label = load_minist('./mnist_train.csv')
    test_data, test_label = load_minist('./mnist_test.csv')

    # this cost 139s
    classifier = MnistClassifierByDecisionTree(train_data,
            train_label,
            # it is ok that we keep dividing until a leaf node contains
            # only on sample, we will prune it later.
            min_samples_split=2,
            # honestly, I dnot know how to choose gini_threshold
            # if dnot use cross-validation.
            gini_threshold=0.04)
    print('root gini:', classifier._tree.single_node_gini)
    print('root left size:', classifier._tree.left_size)
    print('root right size:', classifier._tree.right_size)

    # this cost 325s
    pruned_trees = classifier._get_pruned_trees()
    print('tree amount:', len(pruned_trees))

    # this will cost about 693s
    # This should be done on cross-validation, but I'm lazy.
    for idx, tree in enumerate(pruned_trees):
        print('leaf node amount of current tree:', tree.leaf_node_amount)
        classifier._tree = tree
        print('idx: {}, accuracy:{}'.format(idx,
            model_test(classifier, test_data, test_label)))

if __name__ == "__main__":
    main()
