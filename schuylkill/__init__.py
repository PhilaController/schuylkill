try:
    from importlib.metadata import version
except ImportError:
    # Running on pre-3.8 Python; use importlib-metadata package
    from importlib_metadata import version

from .exact import exact_merge
from .fuzzy import fuzzy_merge
from .tf_idf import tf_idf_merge
from .utils import clean_strings
