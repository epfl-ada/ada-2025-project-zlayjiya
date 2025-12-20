import numpy as np


def gini(arr):
    """
    Simple Gini helper for a 1D array.
    """
    arr = np.asarray(arr, dtype=float)
    if arr.size == 0 or np.allclose(arr.sum(), 0):
        return 0.0
    arr = np.sort(arr)
    n = arr.size
    cumx = np.cumsum(arr)
    return (n + 1 - 2 * (cumx / cumx[-1]).sum()) / n
