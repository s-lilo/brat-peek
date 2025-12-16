"""
brat-peek: utilities to read/write brat standoff annotation files.
"""

from . import ann_structure
from . import rwsl
from . import metrics
from . import stats
from . import txt

# Export main classes and functions for convenience
from .ann_structure import (
    AnnCorpus,
    AnnDocument,
    AnnSentence,
    Entity,
    Relation,
    Event,
    Attribute,
    Note,
    Normalization,
    Placeholder,
)

__version__ = "0.1.2"
__all__ = [
    "AnnCorpus",
    "AnnDocument",
    "AnnSentence",
    "Entity",
    "Relation",
    "Event",
    "Attribute",
    "Note",
    "Normalization",
    "Placeholder",
    "ann_structure",
    "peek",
    "rwsl",
    "metrics",
    "stats",
    "txt",
]
