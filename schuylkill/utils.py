import inspect
import string
import warnings
from functools import wraps

import pandas as pd


def _remove_punctuation(s):
    """Remove punctuation from the input string."""
    translator = str.maketrans("", "", string.punctuation)
    return s.translate(translator)


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
            X = X.apply(_remove_punctuation)

        # Remove ignored words
        out[col] = X.apply(
            lambda x: " ".join([w for w in x.split() if w not in ignored])
        ).str.strip()

    return out


def check_calling_signature(f, args, kwargs):

    # Enforce calling signature
    sig = inspect.signature(f)
    bound_args = sig.bind(*args, **kwargs)

    # Enforce types
    types = f.__annotations__
    for param in bound_args.arguments:
        value = bound_args.arguments[param]
        if param in types:
            if not isinstance(value, types[param]):
                raise TypeError(
                    f"Wrong type for parameter {param}, expected {types[param]}, got {type(value)}"
                )


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
            check_calling_signature(f, args, kwargs)
        except:
            process_merged = True
            try:
                # ignore first argument
                check_calling_signature(f, args[1:], kwargs)
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

            # find the new matches (if we have any left to match)
            if len(left):
                new_matches = f(left, *args[2:], **kwargs)
                toret = pd.concat(
                    [matched, new_matches], axis=0, sort=False
                ).sort_index()
            else:
                warnings.warn(
                    "All rows in 'left' have a match, skipping additional merge function call"
                )
                toret = merged

            return toret

    return wrapper
