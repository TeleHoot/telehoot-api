from typing import Any


def validate_non_empty(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Field should be string")  # noqa: TRY004

    if len(stripped := value.strip()) == 0:
        raise ValueError("Empty input")

    return stripped
