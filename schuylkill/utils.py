from functools import wraps
import inspect
import string
import pandas as pd


def clean_strings(df, cols, remove_punctuation=True, ignored=[]):
    """
    Clean the specified string columns in the input data frame.

    Parameters
    ----------
    df : DataFrame
        the input data 
    cols : list of str
        the list of column names to clean; these should all be string types
    remove_punctuation : bool, optional
        whether or not to remove punctuation from the strings
    ignored : list of str, optional
        a list of any words to remove from the strings
    
    Returns
    -------
    df : pandas.DataFrame
        a copy of `df` with the specified columns cleaned

    """
    # Check the inputs
    if not all(col in df.columns for col in cols):
        raise ValueError("Some of the input columns are not present in the data frame")
    if not all(hasattr(df[col], "str") for col in cols):
        raise ValueError("All specified columns should be of string types")

    # Return a copy
    out = df.copy()

    # Format each specified column
    for col in cols:

        # Make lower-cased and remove spaces
        X = out[col].dropna().str.lower().str.strip()

        # Remove punctuation
        if remove_punctuation:
            X = X.str.replace(f"[{string.punctuation}]", " ")

        # Remove ignored words
        out[col] = X.apply(
            lambda x: " ".join([w for w in x.split() if w not in ignored])
        ).str.strip()

    return out


def pipeable(f):
    """
    Make a function able to chained together to accomodate multiple
    merge steps.

    This allows the decorated function to be used with the `pandas.pipe` function.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):

        # First, see if supplied args/kwargs matches docstring
        process_merged = False
        try:
            bound_args = inspect.signature(f).bind(*args, **kwargs)
        except:
            process_merged = True
            try:
                # ignore first argument
                bound_args = inspect.signature(f).bind(*args[1:], **kwargs)
            except:
                raise ValueError("Incompatible arguments for merge. See docstring.")

        if not process_merged:
            return f(*args, **kwargs)
        else:

            # first three arguments: merged, left, right
            merged, left, right = args[:3]

            # find the subset of past merged that is already matched
            assert "right_index" in merged.columns
            matched = merged.dropna(subset=["right_index"])

            # drop the matches from the left dataframe
            left = left.loc[left.index.difference(matched.index)]

            # find the new matches
            new_matches = f(left, *args[2:], **kwargs)

            # return the subset
            return pd.concat([matched, new_matches], axis=0).sort_index()

    return wrapper
