from typing import Annotated

from fastapi import Depends

from src import core

Pagination = Annotated[core.schemas.PaginationParams, Depends()]
