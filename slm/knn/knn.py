#!/usr/bin/env python3

import numpy as np
from collections import Counter
import time
from functools import wraps, partial
import heapq
import pickle
import matplotlib.pyplot as plt
plt._INSTALL_FIG_OBSERVER = True
import ipdb
from tqdm import tqdm

# some core functions will be timed if you set this to be True.
enable_timing_function = False
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


class KNN(object):
    def __init__(self, X):
        self._X = X

    def get_k_nearest_neighbors_index(self, center, k):
        '''Search k nearest neighbors interface.

        Args:
            center (numpy.ndarray): Search center, this parameter's shape must be 1xd.
            k (int): Neighbor amount.

        Returns:
            numpy.ndarray: The index of it's k nearest neighbors, sort by distance
            ascending.
        '''
        raise NotImplementedError

class KNNByLinearSearch(KNN):
    def __init__(self, X):
        '''
        Args:
            X (numpy.ndarray): data points, one point per row.
        '''
        KNN.__init__(self, X)

    @timeit(prefix='linear search')
    def get_k_nearest_neighbors_index(self, center, k):
        '''Search k nearest neighbors by naive linear search.

        Args:
            center (numpy.ndarray): Search center, this parameter's shape must be 1xd.
            k (int): Neighbor amount.

        Returns:
            numpy.ndarray: The index of it's k nearest neighbors, sort by distance
            ascending.
        '''
        assert len(center.shape) == 2 and center.shape[0] == 1

        # calculate euclidean distance
        dists = np.sqrt(((self._X - center) ** 2).sum(axis=1))

        # we only need k nearest neighbors,
        # so these is no necessary to sort the whole array.
        ind = dists.argpartition(k)[:k]
        # print(dists[ind])
        # we need to return index sort by distance ascending.
        dists_and_index = np.hstack((dists[ind].reshape(-1, 1), ind.reshape(-1, 1)))

        ind = dists_and_index[:, 0].argsort()
        return dists_and_index[ind, 1].astype(np.int32)

class Node(object):
    def __init__(self, id, points, axis_idx, axis_val, left=None, right=None):

        self._id = id

        self.points = points
        self.axis_idx = axis_idx
        self.axis_val = axis_val
        self.left = left
        self.right = right

    def _visualize(self, left_top=[0.0, 1.0], right_bottom=[1.0, 0.0]):
        '''Visualize kdtree, used for debugging.
        Only works for two-dimensional kdtree.
        Note that if this function is to work properly, each leaf node should
        hold exactly one point.
        '''
        self._idx = 0

        assert self.points.shape[0] == 1

        def draw_line(point1, point2):
            plt.plot([point1[0], point2[0]],
                     [point1[1], point2[1]], c='k')
        def visualize_iter(root, left_top, right_bottom):
            if not root: return

            # annotate with format 'a,b', where a is the traverse order,
            # and b is the point's index in the points matrix provided by user.
            plt.annotate('{},{}'.format(self._idx, int(root.points[0][0])),
                root.points[0][1:])
            self._idx += 1

            # the first column is the index
            axis_idx = root.axis_idx - 1

            mid = sorted([root.axis_val, left_top[axis_idx], right_bottom[axis_idx]])[1]
            spans = [left_top[axis_idx^1], right_bottom[axis_idx^1]]
            # get the two endpoints of the split line
            point1, point2 = [0, 0], [0, 0]
            point1[axis_idx] = point2[axis_idx] = mid
            point1[axis_idx^1] = min(spans)
            point2[axis_idx^1] = max(spans)
            draw_line(point1, point2)

            if axis_idx: # split line is horizontal
                visualize_iter(root.left, point1, right_bottom)
                visualize_iter(root.right, left_top, point2)
            else: # vertical
                visualize_iter(root.left, left_top, point1)
                visualize_iter(root.right, point2, right_bottom)

        visualize_iter(self, left_top, right_bottom)

class PriorityQueue(object):
    def __init__(self, max_size=0):
        '''PriorityQueue with maximum size.

        Args:
            max_size (int): If zero, this works as a normal PriorityQueue;
                otherwise, the maximum length of queue is max_size, items
                with less priority will be discarded.
        '''
        self._queue = []
        self._idx = 0
        self._max_size = max_size

    def push(self, item, priority):
        # idx handles the situation that when two items with same priority,
        # they will be returned as FIFO
        if self._max_size != 0 and len(self) >= self._max_size:
            if priority < self.top():
                self.pop()
            else:
                return
        heapq.heappush(self._queue, (-priority, self._idx, item))
        self._idx += 1

    def pop(self):
        return heapq.heappop(self._queue)[-1]

    def top(self):
        # according to heapq's documentation, self._queue[0] is the smallest one.
        return -self._queue[0][0]

    def __len__(self):
        return len(self._queue)

class KNNByKDTree(KNN):
    def __init__(self, X, leaf_node_capacity=10):
        '''Build a kdtree.

        Args:
            X (numpy.ndarray): A 2D matrix that one sample is represented
                by a row.
            leaf_node_capacity (int): Leaf node can hold this amount of points
                at most.
        '''
        KNN.__init__(self, X)

        self._N, self._d = X.shape
        self._leaf_node_capacity = leaf_node_capacity
        self._node_idx = 0


        # during the building process, we will will lose index of the point,
        # so we bind index with point by adding the index column.
        index_column = np.arange(self._N, dtype=np.int32).reshape(self._N, 1)
        self._X = np.hstack((index_column, self._X))

        self._kdtree = self._build(self._X)

    # create this function to figure out the spend time of building process
    @timeit
    def _build(self, X):
        return self._build_iter(X)

    def _build_iter(self, X):
        if X.size <= 0: return None
        N, _ = X.shape

        self._node_idx += 1

        if N <= self._leaf_node_capacity:
            # a acceleration trick, merge tailing node with less points
            return Node(
                id=self._node_idx,
                points=X,
                axis_idx=0,
                axis_val=0,
                left=None,
                right=None)

        # traverse axis according to variance descending order,
        # hope it will scatter out.
        # plus one becase we add index column as follows
        axis = X[:, 1:].var(axis=0).argpartition(-1)[-1] + 1

        axis_column = X[:, axis]

        # we need to divide the data into two roughly equal parts by
        # a hyper-plane that is vertical to this axis. Points whose coordinate
        # value on this axis are small than the boundary will go left, bigger
        # ones go to right and equal ones stay on this plane.
        ind = axis_column.argsort()
        axis_column = axis_column[ind]
        middle = axis_column[N // 2]

        return Node(
            id=self._node_idx,
            points=X[ind[axis_column == middle]],
            axis_idx=axis,
            axis_val=middle,
            left=self._build_iter(X[ind[axis_column < middle]]),
            right=self._build_iter(X[ind[axis_column > middle]]))

    def _fill_path(self, root, center):
        '''Find leaf node that is nearest to center.

        Args:
            root (Node): The kdtree.
            center (numpy.ndarray): The search target, it must be a row vector.
        '''
        while root and not self._visited[root._id]:
            self._path_stack.append(root)
            axis = root.axis_idx
            center_value = center[0][axis-1]

            # we must reach the leaf node
            if center_value < root.axis_val:
                if root.left:
                    root = root.left
                else:
                    # it is possible that right tree is not empty
                    root = root.right
            else:
                # center is on the split hyperplane or the right of the hyperplane
                #   - if on the right of the hyperplane, we just go right
                #   - if on the hyperplane exactly, we still need to go to the
                #       leaf, picking any side is ok, we just go right.
                if root.right:
                    root = root.right
                else:
                    # it is possible that left tree is not empty
                    root = root.left

    def _search(self, center, m):
        search_cnt = 0

        self._path_stack = []
        self._visited = np.zeros(self._N+1, dtype=bool)
        self._fill_path(self._kdtree, center)

        while len(self._path_stack):
            cur_node = self._path_stack.pop()
            if self._visited[cur_node._id]:
                continue

            self._visited[cur_node._id] = True
            cur_dists = np.sqrt(
                    ((cur_node.points[:, 1:] - center[0]) ** 2).sum(axis=1))
            search_cnt += cur_dists.size

            # we only need min-m ones
            if cur_dists.size > m:
                ind = cur_dists.argpartition(m)
                cur_dists = cur_dists[ind[:m]]
                points_index = cur_node.points[ind[:m], 0]
            else:
                points_index = cur_node.points[:, 0]

            for idx, dist in zip(points_index, cur_dists):
                # we only need to store points' index and distance.
                # we just push it in, queue automatically holds m nearest neighbors at most
                self._nearest_neighbors.push(idx, dist)

            if len(self._path_stack) == 0: return search_cnt

            farest = self._nearest_neighbors.top()
            parent = self._path_stack[-1]
            if farest <= abs(center[0][parent.axis_idx-1] - parent.axis_val) \
                    and len(self._nearest_neighbors) == m:
                # it is impossible that sibling can have closer neighbors
                continue

            # the hypersphere is intersected with the split hyperplane,
            # we need to search the sibling.

            if cur_node is parent.left:
                if parent.right and not self._visited[parent.right._id]:
                    self._fill_path(parent.right, center)
            else:
                if parent.left and not self._visited[parent.left._id]:
                    self._fill_path(parent.left, center)

        return search_cnt


    @timeit(prefix='my_kdtree')
    def get_k_nearest_neighbors_index(self, center, k):
        '''Search k nearest neighbors by kdtree.

        Args:
            center (numpy.ndarray): Search center, this parameter's shape must be 1xd.
            k (int): Neighbor amount.

        Returns:
            numpy.ndarray: The index of it's k nearest neighbors, sort by distance
            ascending.
        '''
        self._nearest_neighbors = PriorityQueue(max_size=k)
        search_cnt = self._search(center, k)
        print("kdtree search cnt:", search_cnt)
        result = []
        for _ in range(len(self._nearest_neighbors)):
            result.append(self._nearest_neighbors.pop())
        return np.array(result[::-1], dtype=np.int32)

class MnistClassifier(object):
    def __init__(self, train_data, train_label):
        self._train_data = self._preprocess(train_data)
        self._train_label = train_label

    @timeit
    def _preprocess(self, X):
        #  return X / 255.0

        #  min = X.min(axis=0)
        #  max = X.max(axis=0)
        #  # plus one to avoid divide by zero error
        #  return (X - min) / (max - min + 1)

        # note that we can NOT perform (x - mean) / standard_deviation
        # here(which will lead variance to be 1)
        # because we use the variance to split points.

        # it seems that usual preprocessing tricks has little effect on the
        # final performance of Mnist dataset, and take the fact that integer operations are much
        # fater than floating point, we keep the data as it is.
        return X

    def predict(self, X):
        '''Classify handwritten digits.

        Args:
            X (numpy.ndarray): Digits to be classified, one per row.

        Returns:
            numpy.ndarray: The predicted digits.
        '''
        raise NotImplementedError

class MnistClassifierByKNN(MnistClassifier):
    def __init__(self, knn, train_data, train_label, k):
        MnistClassifier.__init__(self, train_data, train_label)

        self._knn_searcher = knn(self._train_data)
        self._k = k

    @timeit
    def predict(self, X):
        # take same preprocess steps as the model do.
        X = self._preprocess(X)
        result = []

        for center in X:
            center = center.reshape((1,-1)) # search target must be a row vector.
            ind = self._knn_searcher \
                    .get_k_nearest_neighbors_index(center, self._k)

            k_nearest_neighbors = self._train_label[ind]
            # classify by majority voting rule
            predict_class = Counter(k_nearest_neighbors).most_common(1)[0][0]

            result.append(predict_class)
        return np.array(result, dtype=np.int32)


@timeit
def load_minist(file_name):
    label_arr, data_arr = [], []
    with open(file_name) as f:
        for line in f:
            label, *data = line.strip().split(',')
            label_arr.append(label)
            data_arr.append(data)

    return np.array(data_arr, dtype=np.int32), \
           np.array(label_arr, dtype=np.int32)
    #  the following is much slower
    #  data = np.genfromtxt(file_name, delimiter=',', dtype=np.int32)
    #  return data[:, :-1], data[:, -1:]


@timeit
def model_test(model, test_data, test_label):
    predict_class = model.predict(test_data)
    correct_amount = (predict_class == test_label).sum()
    accuracy = correct_amount / test_data.shape[0]
    return accuracy

@timeit
def model_select(train_data, train_label, validation_data, validation_label,
        verbose=True):
    # pick a good k on mnist
    result = {}
    max_accuracy = 0
    max_accuracy_k = 0
    for k in range(1, 25+1):
        classifier = MnistClassifierByKNN(KNNByLinearSearch, train_data,
            train_label, k)
        result[k] = model_test(classifier, validation_data, validation_label)

        if verbose:
            print('k:{:>3d} --> accuracy: {:.4f}'.format(k, result[k]))

        if result[k] > max_accuracy:
            max_accuracy = result[k]
            max_accuracy_k = k

    return max_accuracy_k


def kdtree_implementation_valiate(linear_model_cls, kdtree_model_cls, train_data, validation_data, k):
    '''Compare kdtree implementation with linear search,
    verify that it is a right implementation.
    '''
    linear_model = linear_model_cls(train_data)
    kdtree_model = kdtree_model_cls(train_data)

    # FIXME: 2020-03-23, tqdm does not work in k8s?
    # already tried:
    #     - set tty to true
    #     - python -u to disable buffering
    #  for idx, center in tqdm(enumerate(validation_data)):
    for idx, center in enumerate(validation_data):
        center = center.reshape(1, -1)
        neighbors_idx_by_linear_model = linear_model.get_k_nearest_neighbors_index(center, k)
        neighbors_idx_by_kdtree_model = kdtree_model.get_k_nearest_neighbors_index(center, k)

        if (neighbors_idx_by_linear_model == neighbors_idx_by_kdtree_model).all():
            continue

        print('not same on:', idx)

        print(neighbors_idx_by_linear_model)
        print(neighbors_idx_by_kdtree_model)

        neighbors_by_linear_model = train_data[neighbors_idx_by_linear_model]
        dists_by_linear_model = np.sqrt(((neighbors_by_linear_model - center) ** 2).sum(axis=1))
        print(dists_by_linear_model)


        neighbors_by_kdtree_model = train_data[neighbors_idx_by_kdtree_model]
        dists_by_kdtree_model = np.sqrt(((neighbors_by_kdtree_model - center) ** 2).sum(axis=1))
        print(dists_by_kdtree_model)

        break

def find_counter_example(linear_model_cls, kdtree_model_cls, data_shape, k=2, found=False):
    def visualize(dataset, center, root):
        plt.clf()

        plt.scatter(dataset[:, 0], dataset[:, 1])
        plt.scatter(center[0][0], center[0][1], c='r')

        root._visualize()

        plt.show()

    search_conter_example_cnt = 0
    if found:
        state = pickle.load(open('np.random.state', 'rb'))
        np.random.set_state(state)
    while True:
        if not found:
            # get current random seed of numpy
            state = np.random.get_state()

        search_conter_example_cnt += 1
        if search_conter_example_cnt % 500 == 0:
            print('search_conter_example_cnt:', search_conter_example_cnt)

        data = np.random.rand(*data_shape)
        center = np.random.rand(1, data_shape[1])
        if found:
            print(data)
            print(center)

        linear_model = linear_model_cls(data)
        kdtree_model = kdtree_model_cls(data, leaf_node_capacity=0)
        if found:
            ipdb.set_trace()
            visualize(data, center, kdtree_model._kdtree)
            pause(1) # let firgure show in ipdb

        neighbors_idx_by_linear_model = linear_model.get_k_nearest_neighbors_index(center, k)
        neighbors_idx_by_kdtree_model = kdtree_model.get_k_nearest_neighbors_index(center, k)

        if (neighbors_idx_by_linear_model == neighbors_idx_by_kdtree_model).all():
            continue

        print('===== conter example found =====')

        if not found:
            with open('np.random.state', 'wb') as f:
                pickle.dump(state, f)

        print(neighbors_idx_by_linear_model)
        print(neighbors_idx_by_kdtree_model)

        neighbors_by_linear_model = data[neighbors_idx_by_linear_model]
        dists_by_linear_model = np.sqrt(((neighbors_by_linear_model - center) ** 2).sum(axis=1))
        print(dists_by_linear_model)


        neighbors_by_kdtree_model = data[neighbors_idx_by_kdtree_model]
        dists_by_kdtree_model = np.sqrt(((neighbors_by_kdtree_model - center) ** 2).sum(axis=1))
        print(dists_by_kdtree_model)

        break


def test_on_mnist():
    '''test knn on mnist dataset.
    '''
    train_data, train_label = load_minist('./mnist_train.csv')
    test_data, test_label = load_minist('./mnist_test.csv')
    # maybe a shuffle?

    # select a good k on mnist by linear search.
    #  validation_data_amount = 2000
    #  validation_data = test_data[:validation_data_amount]
    #  validation_label = test_label[:validation_data_amount]
    #  k = model_select(train_data, train_label, validation_data, validation_label)
    #  print('model select choose k:', k)
    '''
    result:
    k:  1 --> accuracy: 0.9600
    k:  2 --> accuracy: 0.9600
    k:  3 --> accuracy: 0.9605
    k:  4 --> accuracy: 0.9605
    k:  5 --> accuracy: 0.9585
    k:  6 --> accuracy: 0.9600
    k:  7 --> accuracy: 0.9570
    k:  8 --> accuracy: 0.9595
    k:  9 --> accuracy: 0.9520
    k: 10 --> accuracy: 0.9535
    k: 11 --> accuracy: 0.9510
    k: 12 --> accuracy: 0.9535
    k: 13 --> accuracy: 0.9500
    k: 14 --> accuracy: 0.9485
    k: 15 --> accuracy: 0.9460
    k: 16 --> accuracy: 0.9500
    k: 17 --> accuracy: 0.9480
    k: 18 --> accuracy: 0.9500
    k: 19 --> accuracy: 0.9490
    k: 20 --> accuracy: 0.9485
    k: 21 --> accuracy: 0.9470
    k: 22 --> accuracy: 0.9470
    k: 23 --> accuracy: 0.9460
    k: 24 --> accuracy: 0.9445
    k: 25 --> accuracy: 0.9430
    '''
    k = 3

    #  classifier = MnistClassifierByKNN(KNNByLinearSearch, train_data,
    #      train_label, k)
    classifier = MnistClassifierByKNN(KNNByKDTree, train_data, train_label, k)
    print(model_test(classifier, test_data[:100], test_label[:100]))
    '''
    final performance on mnist testset(10000 cases):
        accuracy: 0.9717
        linear_search_time: 0.15936653792858124s per testcase
        kdtree_search_time: 0.261935769867897s per testcase
    '''

    # debug kdtree, first let found to be False, run program to find counter
    # example; then let found to be True, run program to begin debug on the
    # counter example just found.
    #
    # current implementation is right, run this will get an infinity loop.
    #  find_counter_example(
    #      KNNByLinearSearch,
    #      KNNByKDTree,
    #      (22,2), # less points will make it hard to find counter example
    #      2,
    #      found=False)

def test_on_random_data():
    global enable_timing_function
    enable_timing_function = True

    k = 5

    train_data = np.random.rand(60000, 10)
    test_data = np.random.rand(10000, 10)

    # this function check whether linear search and kdtree give the same result,
    # and we also have some verbose output that shows kdtree will scan less
    # points than linear search.
    kdtree_implementation_valiate(
        KNNByLinearSearch,
        KNNByKDTree,
        train_data,
        test_data,
        k
    )

    '''
    experiment result:
        kdtree average search points amount: 14402.6
        linear_search_time: 0.002496488070487976s per testcase
        kdtree_search_time: 0.058024237871170045s per testcase

    conclusion:
        under this condition, we can see that kdtree has indeed prunned out lots
        of branches, but unfortunately kdtree version is still much slower than
        linear search, the following are the two main reasons:
            1. linear search implemented by optimized vector operations
            2. kdtree implementation itself(not the algorithm) has efficiency
                problem.
    '''

def test_other_implementations():
    '''Test performance on kdtree implementation of scipy and sklearn.'''
    from scipy.spatial import KDTree as SciKDTree
    #  from scipy.spatial import cKDTree as ScicKDTree

    class KNNByScipyKDTree(SciKDTree):
        def __init__(self, data, leafsize=10):
            SciKDTree.__init__(self, data, leafsize)

        @timeit(prefix='scipy_kdtree')
        def get_k_nearest_neighbors_index(self, center, k):
            _, ind = self.query(center, k)
            return ind

    # tried to test on scipy.spatial.cKDTree,
    # but cKDTree seems to fail to build tree,
    # it enters cKDTree's __init__ function for several minutes
    # and wont exit.
    #
    #  class KNNByScipycKDTree(ScicKDTree):
    #      def __init__(self, data, leafsize=10):
    #          ScicKDTree.__init__(self, data, leafsize)
    #
    #      @timeit(prefix='scipy_ckdtree')
    #      def get_k_nearest_neighbors_index(self, center, k):
    #          _, ind = self.query(center, k)
    #          return ind

    from sklearn.neighbors import KDTree as SKLKDTree
    class KNNBySKLearnKDTree(SKLKDTree):
        def __init__(self, data, leafsize=10):
            SKLKDTree.__init__(self, data, leafsize)

        @timeit(prefix='sklearn_kdtree')
        def get_k_nearest_neighbors_index(self, center, k):
            return self.query(center, k=k, return_distance=False)

    global enable_timing_function
    enable_timing_function = True

    train_data, train_label = load_minist('./mnist_train.csv')
    test_data, test_label = load_minist('./mnist_test.csv')

    k = 3

    # compare my implementation with scipy
    kdtree_implementation_valiate(
        KNNByKDTree,
        KNNByScipyKDTree,
        train_data,
        test_data,
        k
    )
    '''
    my_implementation: 0.269369s per testcase
    scipy implementation: 1.24836s per testcase
    '''

    # compare two implementation in scipy
    #  kdtree_implementation_valiate(
    #      KNNByScipyKDTree,
    #      KNNByScipycKDTree,
    #      train_data,
    #      test_data,
    #      k
    #  )

    # compare my implementation with sklearn
    kdtree_implementation_valiate(
        KNNByKDTree,
        KNNBySKLearnKDTree,
        train_data,
        test_data,
        k
    )
    '''
    my_implementation: 0.283231s per testcase
    sklearn implementation: 0.0966187s testcase

    we can see that sklearn implementation is much faster,
    after taking a glance at sklearn's source code(I dont check their algorithm
    yet), I think the main reason is that they implemente by cython,
    so I stop to dig it.
    '''


def main():
    # kdtree is not suitable for mnist at all, because the range is each
    # dimension in mnist is [0, 255], which means the maximum difference on any
    # dimension is 255. However, there on **only 5 cases** in the test set(which
    # contains 10000 cases) of mnist that has a nearest neighbor with distance
    # less than 255. And this is really bad because the hypersphere is always
    # intintersected with the split hyperplane, so we have to always(except
    # above 5 cases) search the other side of the hyperplane, that means, we are
    # scanning the whole space every time!
    #
    #  test_on_mnist()

    # test on randomly generated data shows that kdtree can indeed prunne out
    # lots of branches.
    #
    test_on_random_data()

    #  test_other_implementations()


if __name__ == "__main__":
    main()

