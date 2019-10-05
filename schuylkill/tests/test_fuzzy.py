import schuylkill as skool
import pytest
import pandas as pd


def test_fuzzy():

    # Create the data
    left = pd.DataFrame({"street": ["Washington", "Market", "Broad"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street": ["Washington", "Mrkt", "Brd"], "y": [4, 5, 6]})

    # merge
    merged = skool.fuzzy_merge(left, right, on="street", score_cutoff=0)

    # test
    assert len(merged) == len(left)
    assert len(merged.dropna()) == 3


def test_diff_ons():

    # Create the data
    left = pd.DataFrame({"street_1": ["Washington", "Market", "Broad"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street_2": ["Washington", "Mrkt", "Brd"], "y": [4, 5, 6]})

    # merge
    merged = skool.fuzzy_merge(
        left, right, left_on="street_1", right_on="street_2", score_cutoff=0
    )

    # test
    assert len(merged) == len(left)
    assert len(merged.dropna()) == 3


def test_threshold():

    # Create the data
    left = pd.DataFrame({"street": ["Washington", "Market", "Broad"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street": ["Washington", "Mrkt", "Brd"], "y": [4, 5, 6]})

    # merge
    merged = skool.fuzzy_merge(left, right, on="street", score_cutoff=100)

    # test
    assert len(merged) == len(left)
    assert len(merged.dropna()) == 1


def test_missing_on():

    # Create the data
    left = pd.DataFrame({"street_1": ["Washington", "Market", "Broad"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street_2": ["Washington"], "y": [1]})

    # missing_on
    with pytest.raises(ValueError):
        merged = skool.fuzzy_merge(left, right)


def test_bad_ons():

    # Create the data
    left = pd.DataFrame({"street_1": ["Washington", "Market", "Broad"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street_2": ["Washington"], "y": [1]})

    # bad on
    with pytest.raises(ValueError):
        merged = skool.fuzzy_merge(left, right, left_on="street")

    # bad on
    with pytest.raises(ValueError):
        merged = skool.fuzzy_merge(left, right, right_on="street")
