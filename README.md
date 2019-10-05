# schuylkill

[![Build Status](https://travis-ci.org/PhiladelphiaController/schuylkill.svg?branch=master)](https://travis-ci.org/PhiladelphiaController/schuylkill)
[![Coverage Status](https://coveralls.io/repos/github/PhiladelphiaController/schuylkill/badge.svg?branch=master)](https://coveralls.io/github/PhiladelphiaController/schuylkill?branch=master)
[![](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/download/releases/3.6.0/)
![t](https://img.shields.io/badge/status-stable-green.svg)
[![](https://img.shields.io/github/license/PhiladelphiaController/schuylkill.svg)](https://github.com/PhiladelphiaController/schuylkill/blob/master/LICENSE)
[![PyPi version](https://img.shields.io/pypi/v/schuylkill.svg)](https://pypi.python.org/pypi/schuylkill/)

Fixing human errors by matching those hard-to-spell words.

This Python utility merges `pandas` DataFrames based on two string columns using a variety of
matching techniques, including fuzzy merging (using the `fuzzywuzzy` package).

## Installation

Via PyPi:

```
pip install schuylkill
```

## Examples

### Exact Matching

You can merge data based on string functions: "exact", "startswith", "contains":

```python
>>> import schuylkill as skool
>>> import pandas as pd

# Create the data
>>> left = pd.DataFrame({"street": ["Wash", "road", "Test"], "x": [1, 2, 3]})
>>> right = pd.DataFrame({"street": ["Washington", "Market", "Broad"], "y": [1, 2, 3]})

# Merge based on "contains"
>>> merged = skool.exact_merge(left, right, on="street", how="contains")
  street_x  x  right_index    street_y    y
0     Wash  1          0.0  Washington  1.0
1     road  2          2.0       Broad  3.0
2     Test  3          NaN         NaN  NaN
```

You can also use the `pandas` `pipe()` function to chain multiple merges together:

```python

# Create the data
>>> left = pd.DataFrame({"street": ["Washington", "Mark", "road"], "x": [1, 2, 3]})
>>> right = pd.DataFrame({"street": ["Washington", "Market", "Broad"], "y": [4, 5, 6]})

# Combine multiple merges
>>> merged = (
    skool.exact_merge(left, right, on="street", how="exact")
    .pipe(skool.exact_merge, left, right, on="street", how="startswith")
    .pipe(skool.exact_merge, left, right, on="street", how="contains")
)
     street_x  x  right_index    street_y    y
0  Washington  1          0.0  Washington  4.0
1        Mark  2          1.0      Market  5.0
2        road  3          2.0       Broad  6.0
```

In the above example, each merge performed matches one row, and the final merged data frame has
three matches.

### Fuzzy Matching

Fuzzy matching based on a score threshold is also available:

```python
# Create the data
>>> left = pd.DataFrame({"street": ["Washington", "Market", "Broad"], "x": [1, 2, 3]})
>>> right = pd.DataFrame({"street": ["Washington", "Mrkt", "Brd"], "y": [4, 5, 6]})

# Perform a fuzzy merge
>>> merged = skool.fuzzy_merge(left, right, on="street", score_cutoff=70)
     street_x  x  match_probability  right_index    street_y    y
0  Washington  1               1.00          0.0  Washington  4.0
1      Market  2               0.80          1.0        Mrkt  5.0
2       Broad  3               0.75          2.0         Brd  6.0
```
