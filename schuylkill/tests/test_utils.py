import schuylkill as skool
import pytest
import pandas as pd


def test_pipe():

    # Create the data
    left = pd.DataFrame({"street": ["Washington", "Mark", "road"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street": ["Washington", "Market", "Broad"], "y": [4, 5, 6]})

    # merge
    merged = (
        skool.exact_merge(left, right, on="street", how="exact")
        .pipe(skool.exact_merge, left, right, on="street", how="startswith")
        .pipe(skool.exact_merge, left, right, on="street", how="contains")
    )

    # all should have matches
    assert len(merged.dropna()) == 3
    assert (merged["right_index"] == [0, 1, 2]).all()


def test_pipe_fuzzy():

    # Create the data
    left = pd.DataFrame({"street": ["Washington", "Mark", "road"], "x": [1, 2, 3]})
    right = pd.DataFrame({"street": ["Washington", "Market", "Broad"], "y": [4, 5, 6]})

    # merge
    with pytest.warns(UserWarning):
        merged = skool.fuzzy_merge(left, right, on="street", score_cutoff=0).pipe(
            skool.fuzzy_merge, left, right, left_on="street", right_on="street"
        )

    # all should have matches
    assert len(merged.dropna()) == 3


def test_clean_strings_1():

    # Create the data
    left = pd.DataFrame({"street": ["This is a test! "], "x": [1]})

    # clean
    result = skool.clean_strings(left, ["street"])
    assert result["street"].squeeze() == "this is a test"


def test_clean_strings_2():

    # Create the data
    left = pd.DataFrame({"street": ["This is a test! "], "x": [1]})

    # clean
    result = skool.clean_strings(left, ["street"], remove_punctuation=False)
    assert result["street"].squeeze() == "this is a test!"

    # clean
    result = skool.clean_strings(left, ["street"], ignored=["test"])
    assert result["street"].squeeze() == "this is a"


def test_clean_strings_3():

    # Create the data
    left = pd.DataFrame({"street": ["This is a test! "], "x": [1]})

    # clean
    result = skool.clean_strings(left, ["street"], ignored=["test"])
    assert result["street"].squeeze() == "this is a"


def test_clean_strings_error():

    # Create the data
    left = pd.DataFrame({"street": ["This is a test! "], "x": [1]})

    with pytest.raises(Exception):
        skool.clean_strings(left, ["x"])

