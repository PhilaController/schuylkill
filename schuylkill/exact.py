import pandas as pd
from .utils import pipeable


@pipeable
def exact_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: str = None,
    left_on: str = None,
    right_on: str = None,
    how: str = "exact",
    suffixes=("_x", "_y"),
):
    """
    Merge two dataframes based on two string columns and the specified matching
    technique. Techniques currently available:

    1. "exact" : strings must match exactly
    2. "contains" : the right string must contain the left string
    3. "startswith" : the right string must start with the left string

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
    exact : str, optional
        the merging method, one of 'exact', 'contains', or 'startswith'
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

    def contains(row, right):
        return right.loc[
            right[right_on].str.contains(row[left_on], na=False, regex=False)
        ]

    def exact(row, right):
        return right.loc[right[right_on] == row[left_on]]

    def startswith(row, right):
        return right.loc[right[right_on].str.startswith(row[left_on], na=False)]

    if how == "exact":
        comparison = exact
    elif how == "contains":
        comparison = contains
    elif how == "startswith":
        comparison = startswith
    else:
        raise ValueError("how should be one of: 'exact', 'contains', 'startswith'")

    # rename the index
    right = right.rename_axis("right_index").reset_index()

    merged = pd.concat(
        left.apply(
            lambda row: comparison(row, right).assign(index_left=row.name), axis=1
        ).tolist()
    )
    return left.merge(
        merged.set_index("index_left"),
        left_index=True,
        right_index=True,
        how="left",
        suffixes=suffixes,
    )

