import multiprocessing

import numpy as np
import pandas as pd
from fuzzywuzzy import fuzz, process

from .utils import pipeable


def _apply_df(args):
    df, func, kwargs = args
    return df.apply(func, **kwargs)


def _apply_by_multiprocessing(df, func, workers=4, **kwargs):
    """
    Internal function to apply a function to a dataframe using
    multiprocessing.
    """
    # map the function in parallel
    with multiprocessing.Pool(processes=workers) as pool:
        result = pool.map(
            _apply_df, [(d, func, kwargs) for d in np.array_split(df, workers)]
        )

    # return the combined results
    return pd.concat(list(result))


def _find_matches(x, right_data, score_cutoff, scorer=fuzz.ratio, limit=10):
    """
    Use fuzzywuzzy to find the best matches.
    """
    return process.extractBests(
        x, right_data, limit=limit, score_cutoff=score_cutoff, scorer=scorer
    )


@pipeable
def fuzzy_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: str = None,
    left_on: str = None,
    right_on: str = None,
    workers: int = 4,
    score_cutoff: int = 90,
    scorer=fuzz.ratio,
    max_matches=1,
    suffixes=("_x", "_y"),
):
    """
    Merge two dataframes based on a fuzzy matching between two string columns.

    Notes
    -----
    -   This performs a "left" merge — all rows in the left data frame will be
        present in the returned data frame
    -   Data in the left data frame can match multiple values in the right column.

    Parameters
    ----------
    left : pandas.DataFrame
        the left data to merge
    right : pandas.DataFrame
        the right DataFrame to merge
    on : str, optional
        the column to merge on
    left_on : str, optional
        the name of the string column in the left data frame to merge on
    right_on : str, optional
        the name of the string column in the right data frame to merge on
    workers : int, optional
        the number of processes to apply
    score_cutoff : int, optional
        only match strings that score above this threshold
    scorer : callable, optional
        the fuzzywuzzy function to use to score the matches
    max_matches : int, optional
        the maximum number of matches to identify per row
    suffixes : tuple of (str, str), default ('_x', '_y')
        Suffix to apply to overlapping column names in the left and right
        side, respectively. To raise an exception on overlapping columns use
        (False, False).

    Returns
    -------
    merged : pandas.DataFrame
        the merged dataframe containg all rows in `left` and any matched data
        from the `right` data frame
    """
    if on is not None:
        left_on = right_on = on

    # Verify input parameters
    if left_on is None or right_on is None:
        raise ValueError("Please specify `on` or `left_on/right_on`")
    if left_on not in left.columns:
        raise ValueError(f"'{left_on}' is not a column in `left`")
    if right_on not in right.columns:
        raise ValueError(f"'{right_on}' is not a column in `right`")

    # get the left and right strings
    left_data = left[left_on].dropna().astype(str)
    right_data = right[right_on].dropna().astype(str).rename_axis("right_index")

    # get the fuzzy matches
    fuzzy_matches = (
        _apply_by_multiprocessing(
            left_data,
            _find_matches,
            right_data=right_data,
            score_cutoff=score_cutoff,
            workers=workers,
            scorer=scorer,
            limit=max_matches,
        )
        .reindex(left.index)
        .rename_axis("left_index")
        .reset_index()
    )

    # unstack the matches
    unstacked = (
        fuzzy_matches.apply(lambda x: pd.Series(x[left_data.name], dtype=str), axis=1)
        .stack()
        .reset_index(level=1, drop=True)
    )

    # join the matches
    matches = (
        fuzzy_matches.drop(left_data.name, axis=1)
        .join(
            pd.DataFrame(
                unstacked.tolist(),
                columns=[right_data.name, "score", "right_index"],
                index=unstacked.index,
            ),
            lsuffix=suffixes[0],
            rsuffix=suffixes[1],
        )
        .set_index("left_index")
        .dropna()
    )

    matches = (
        pd.merge(
            left.loc[matches.index]
            .assign(
                right_index=matches.right_index.values,
                match_probability=matches.score.values / 100.0,
            )
            .rename_axis("left_index")
            .reset_index()
            .set_index("right_index"),
            right,
            left_index=True,
            right_index=True,
            suffixes=suffixes,
        )
        .rename_axis("right_index")
        .reset_index()
        .set_index("left_index")
        .sort_index()
    )

    # the rows from the left dataframe that are unmatched
    unmatched = left.loc[left.index.difference(matches.index)]

    # rename any intersecting columns
    intersecting = left.columns.intersection(right.columns)
    for col in intersecting:
        unmatched = unmatched.rename(columns={col: f"{col}{suffixes[0]}"})

    # the name of the right columns, with suffixes
    right_cols = [
        col if col not in intersecting else f"{col}{suffixes[1]}"
        for col in right.columns
    ]

    # return all the data, with columns in the proper order
    out = pd.concat([matches, unmatched], sort=False).sort_index()
    return out.loc[
        :, list(unmatched.columns) + ["match_probability", "right_index"] + right_cols
    ]
