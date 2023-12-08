from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from torch_frame import (
    categorical,
    embedding,
    multicategorical,
    numerical,
    sequence_numerical,
    timestamp,
)
from torch_frame.data.stats import StatType, compute_col_stats
from torch_frame.datasets.fake import _random_timestamp


def test_compute_col_stats_numerical():
    ser = pd.Series([1, 2, 3])
    stype = numerical
    assert compute_col_stats(ser, stype) == {
        StatType.MEAN: 2.0,
        StatType.STD: 0.816496580927726,
        StatType.QUANTILES: [1.0, 1.5, 2.0, 2.5, 3.0],
    }


def test_compute_col_stats_numerical_with_dirty_columns():
    ser = pd.Series([1, 2, 3, 'One', np.inf, np.nan])
    stype = numerical
    with pytest.raises(TypeError,
                       match='Numerical series contains invalid entries.'):
        compute_col_stats(ser, stype)


def test_compute_col_stats_categorical():
    ser = pd.Series(['a', 'a', 'a', 'b', 'c'])
    stype = categorical
    assert compute_col_stats(ser, stype) == {
        StatType.COUNT: (['a', 'b', 'c'], [3, 1, 1]),
    }


def test_compute_col_stats_multi_categorical():
    for ser, sep in [
        (pd.Series(['a|a|b', 'a|c', 'c|a', 'a|b|c', '', None, np.nan]), '|'),
            # # Testing with leading and traling whitespace
        (pd.Series(['a, a , b', 'a, c', 'c ,a', '  a, b, c', '  ',
                    None]), ','),
            # Testing with list representation
        (pd.Series([['a', 'a', 'b'], ['a', 'c'], ['c', 'a'], ['a', 'b', 'c'],
                    [], None]), None),
    ]:
        stype = multicategorical
        assert compute_col_stats(ser, stype, sep=sep) == {
            StatType.MULTI_COUNT: (['a', 'c', 'b'], [4, 3, 2]),
        }


def test_compute_col_stats_timestamp():
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2023, 1, 1)
    num_rows = 10

    # Test YEAR_RANGE with year specified
    format = '%Y-%m-%d %H:%M:%S'
    arr = [
        _random_timestamp(start_date, end_date, format)
        for _ in range(num_rows)
    ]
    arr[0::2] = len(arr[0::2]) * [np.nan]
    ser = pd.Series(arr)
    stype = timestamp

    year_range = compute_col_stats(ser, stype,
                                   time_format=format)[StatType.YEAR_RANGE]
    assert (year_range[0] >= 2000 and year_range[1] <= 2023
            and year_range[0] <= year_range[1])

    # Test YEAR_RANGE with year unspecified
    format = '%m-%d'
    arr = [
        _random_timestamp(start_date, end_date, format)
        for _ in range(num_rows)
    ]
    arr[0::2] = len(arr[0::2]) * [np.nan]
    ser = pd.Series(arr)
    stype = timestamp

    year_range = compute_col_stats(ser, stype,
                                   time_format=format)[StatType.YEAR_RANGE]
    assert (year_range[0] == year_range[1] == 1900)


def test_compute_col_stats_timestamp_with_nan():
    ser = pd.Series([np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan])
    stype = timestamp
    year_range = compute_col_stats(ser, stype)[StatType.YEAR_RANGE]
    assert year_range[0] == -1 and year_range[1] == -1


def test_compute_col_stats_sequence_numerical():
    ser = pd.Series([[1, 2, 3], [4, 5, 6]])
    stype = sequence_numerical
    assert compute_col_stats(ser, stype) == {
        StatType.MEAN: 3.5,
        StatType.STD: 1.707825127659933,
        StatType.QUANTILES: [1.0, 2.25, 3.5, 4.75, 6.0],
    }


def test_compute_col_stats_sequence_numerical_with_nan_inf():
    ser = pd.Series([[1, 2, 3, np.nan], [4, 5, 6]])
    expected_col_stats = {
        StatType.MEAN: 3.5,
        StatType.STD: 1.707825127659933,
        StatType.QUANTILES: [1.0, 2.25, 3.5, 4.75, 6.0],
    }
    stype = sequence_numerical
    assert compute_col_stats(ser, stype) == expected_col_stats
    ser = pd.Series([[1, 2, 3, np.inf], [4, 5, 6]])
    assert compute_col_stats(ser, stype) == expected_col_stats


def test_compute_col_stats_sequence_numerical_with_nan():
    ser = pd.Series([[np.nan, np.nan, np.nan, np.inf],
                     [np.nan, np.nan, np.nan]])
    stype = sequence_numerical
    assert compute_col_stats(ser, stype) == {
        StatType.MEAN: np.nan,
        StatType.STD: np.nan,
        StatType.QUANTILES: [np.nan, np.nan, np.nan, np.nan, np.nan],
    }


def test_compute_col_stats_numerical_with_inf():
    ser = pd.Series([1, 2, 3, np.inf, -np.inf])
    stype = numerical
    assert compute_col_stats(ser, stype) == {
        StatType.MEAN: 2.0,
        StatType.STD: 0.816496580927726,
        StatType.QUANTILES: [1.0, 1.5, 2.0, 2.5, 3.0],
    }


def test_compute_col_stats_numerical_with_nan():
    ser = pd.Series([1, 2, 3, np.nan])
    stype = numerical
    assert compute_col_stats(ser, stype) == {
        StatType.MEAN: 2.0,
        StatType.STD: 0.816496580927726,
        StatType.QUANTILES: [1.0, 1.5, 2.0, 2.5, 3.0],
    }


def test_compute_col_stats_numerical_nan():
    ser = pd.Series([np.nan, np.nan, np.nan, np.nan])
    stype = numerical
    assert compute_col_stats(ser, stype) == {
        StatType.MEAN: np.nan,
        StatType.STD: np.nan,
        StatType.QUANTILES: [np.nan, np.nan, np.nan, np.nan, np.nan],
    }


def test_compute_col_stats_embedding():
    emb_dim = 12
    ser = pd.Series([np.random.rand(emb_dim) for _ in range(3)])
    stype = embedding
    assert compute_col_stats(ser, stype) == {
        StatType.EMB_DIM: emb_dim,
    }
