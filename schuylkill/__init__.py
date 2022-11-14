from importlib.metadata import version

__version__ = version(__package__)

from .exact import exact_merge
from .fuzzy import fuzzy_merge
from .tf_idf import tf_idf_merge
from .utils import clean_strings
