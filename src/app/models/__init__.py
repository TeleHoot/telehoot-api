import sys
from collections.abc import Sequence
from inspect import getmembers, isclass

from beanie import Document

from .membership import Membership, UserRoles
from .membership import Statuses as MembershipStatuses
from .organization import Organization
from .questions import Question
from .user import User
from .session import Session, SessionParticipant

__all__ = [
    "Membership",
    "MembershipStatuses",
    "Organization",
    "Question",
    "User",
    "UserRoles",
    "gather_documents",
    "Session",
    "SessionParticipant",
]


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
