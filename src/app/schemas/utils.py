from typing import Any


def validate_non_empty(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Field should be string")  # noqa: TRY004

    if len(stripped := value.strip()) == 0:
        raise ValueError("Empty input")

    return stripped


def convert_str(value: Any) -> str:
    try:
        return str(value)
    except Exception as e:
        raise ValueError(f"Cannot convert value to string: {value}") from e
