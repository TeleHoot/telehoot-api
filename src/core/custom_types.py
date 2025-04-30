from uuid import UUID

from beanie import PydanticObjectId

type EntityID = int | str | UUID | dict[str, EntityID] | PydanticObjectId
