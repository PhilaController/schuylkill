import re
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
import sparse_dot_topn.sparse_dot_topn as ct
from sklearn.feature_extraction.text import TfidfVectorizer
from .utils import pipeable

__all__ = ["tf_idf_merge"]


def _format_matches(sparse_matrix, name_vector_unique, unique_index, left_size):
    """
    Internal function to format the sparse matrix of matches 
    into a pandas DataFrame.
    """
    non_zeros = sparse_matrix.nonzero()

    sparserows = non_zeros[0]
    sparsecols = non_zeros[1]
    nr_matches = sparsecols.size

    out = []

    for index in range(0, nr_matches):

        # the left/right string match
        left_side = name_vector_unique.iloc[sparserows[index]]
        right_side = name_vector_unique.iloc[sparsecols[index]]

        # the index in name vector
        lidx = name_vector_unique.index[sparserows[index]]
        ridx = name_vector_unique.index[sparsecols[index]]

        # the original index
        left_index = unique_index[lidx]
        right_index = unique_index[ridx]

        # similarity
        similarity = sparse_matrix.data[index]

        if lidx != ridx and lidx < left_size and ridx > left_size:
            out.append([left_index, right_index, left_side, right_side, similarity])

    return pd.DataFrame(
        out,
        columns=["left_index", "right_index", "left_side", "right_side", "similarity"],
    )


def _fast_cossim_top(A, B, ntop, lower_bound=0):
    """
    Calculate the cosine similarity for the top matches.
    """
    # force A and B as a CSR matrix.
    # If they have already been CSR, there is no overhead
    A = A.tocsr()
    B = B.tocsr()
    M, _ = A.shape
    _, N = B.shape

    idx_dtype = np.int32

    nnz_max = M * ntop

    indptr = np.zeros(M + 1, dtype=idx_dtype)
    indices = np.zeros(nnz_max, dtype=idx_dtype)
    data = np.zeros(nnz_max, dtype=A.dtype)

    ct.sparse_dot_topn(
        M,
        N,
        np.asarray(A.indptr, dtype=idx_dtype),
        np.asarray(A.indices, dtype=idx_dtype),
        A.data,
        np.asarray(B.indptr, dtype=idx_dtype),
        np.asarray(B.indices, dtype=idx_dtype),
        B.data,
        ntop,
        lower_bound,
        indptr,
        indices,
        data,
    )

    return csr_matrix((data, indices, indptr), shape=(M, N))


def _ngrams(string, n=3):
    """
    Calculate n-grams for the input string.
    """
    string = re.sub(r"[,-./]|\sBD", r"", string)
    ngrams = zip(*[string[i:] for i in range(n)])
    return ["".join(ngram) for ngram in ngrams]


@pipeable
def tf_idf_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: str = None,
    left_on: str = None,
    right_on: str = None,
    score_cutoff: int = 90,
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

    # Merge together into single Series
    all_data = pd.concat([left_data, right_data], axis=0)

    # save the index and then reset it
    all_data_index = all_data.index
    all_data = all_data.reset_index(drop=True)

    # Do the TF-IDF vectorization
    vectorizer = TfidfVectorizer(min_df=1, analyzer=_ngrams)
    tf_idf_matrix = vectorizer.fit_transform(all_data.values)

    # Get the matches as a sparse matrix
    matches = _fast_cossim_top(
        tf_idf_matrix,
        tf_idf_matrix.transpose(),
        ntop=max_matches + 1,
        lower_bound=score_cutoff / 100,
    )

    # Format the matches into a DataFrame
    left_size = len(left_data)
    matches_df = _format_matches(matches, all_data, all_data_index, left_size)

    # Merge in the right
    matches_df = (
        pd.merge(
            left,
            pd.merge(
                matches_df,
                right.rename_axis("right_index").reset_index(),
                on="right_index",
            ).set_index("left_index"),
            how="left",
            left_index=True,
            right_index=True,
            suffixes=suffixes,
        )
        .drop(labels=["left_side", "right_side"], axis=1)
        .rename(columns={"similarity": "match_probability"})
    )

    return matches_df
