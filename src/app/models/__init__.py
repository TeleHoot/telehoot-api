import sys
from collections.abc import Sequence
from inspect import getmembers, isclass

from beanie import Document

from .organization import Organization
from .questions import Question
from .user import User

__all__ = ["Organization", "Question", "User", "gather_documents"]


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
