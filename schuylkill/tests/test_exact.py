import schuylkill as skool
import pytest
import pandas as pd


def test_exact():

    # Create the data
    left = pd.DataFrame({"street": ["Washington", "Market", "Broad"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street": ["Washington"], "y": [1]})

    # merge
    merged = skool.exact_merge(left, right, on="street")

    # test
    assert all(
        col in merged.columns
        for col in ["street_x", "x", "right_index", "street_y", "y"]
    )
    assert len(merged) == len(left)
    assert len(merged.dropna()) == 1


def test_contains():

    # Create the data
    left = pd.DataFrame({"street": ["Wash", "road", "Test"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street": ["Washington", "Market", "Broad"], "y": [1, 2, 3]})

    # merge
    merged = skool.exact_merge(left, right, on="street", how="contains")

    # test
    assert len(merged) == len(left)
    assert len(merged.dropna()) == 2  # 2 matches


def test_startswith():

    # Create the data
    left = pd.DataFrame({"street": ["Wash", "road", "Market"], "x": [1, 2, 3]})
    right = pd.DataFrame(
        {"street": ["Washington", "Market St", "Broad"], "y": [1, 2, 3]}
    )

    # merge
    merged = skool.exact_merge(left, right, on="street", how="startswith")

    # test
    assert len(merged) == len(left)
    assert len(merged.dropna()) == 2  # 2 matches


def test_suffixes():

    # Create the data
    left = pd.DataFrame({"street": ["Washington", "Market", "Broad"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street": ["Washington"], "y": [1]})

    # merge
    merged = skool.exact_merge(left, right, on="street", suffixes=("_left", "_right"))

    # test
    assert all(col in merged.columns for col in ["street_left", "street_right"])


def test_diff_ons():

    # Create the data
    left = pd.DataFrame({"street_1": ["Washington", "Market", "Broad"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street_2": ["Washington"], "y": [1]})

    # merge
    merged = skool.exact_merge(left, right, left_on="street_1", right_on="street_2")

    # test
    assert len(merged.dropna()) == 1


def test_missing_on():

    # Create the data
    left = pd.DataFrame({"street_1": ["Washington", "Market", "Broad"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street_2": ["Washington"], "y": [1]})

    # missing_on
    with pytest.raises(ValueError):
        merged = skool.exact_merge(left, right)


def test_bad_ons():

    # Create the data
    left = pd.DataFrame({"street_1": ["Washington", "Market", "Broad"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street_2": ["Washington"], "y": [1]})

    # bad on
    with pytest.raises(ValueError):
        merged = skool.exact_merge(left, right, left_on="street")

    # bad on
    with pytest.raises(ValueError):
        merged = skool.exact_merge(left, right, right_on="street")
