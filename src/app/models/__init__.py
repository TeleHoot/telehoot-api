import sys
from collections.abc import Sequence
from inspect import getmembers, isclass

from beanie import Document

# All database models must be imported here to be able to
# initialize them on startup.
from .questions import Question

__all__ = ["Question", "gather_documents"]


def gather_documents() -> Sequence[type[Document]]:
    """Returns a list of all MongoDB document models defined in `models` module.
    Returns:
        Sequence[type[DocType]]
    """

    return [
        doc
        for _, doc in getmembers(sys.modules[__name__], isclass)
        if issubclass(doc, Document) and doc.__name__ not in {"Document", "MongoBase"}
    ]
