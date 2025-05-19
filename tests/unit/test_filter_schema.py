from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.core.schemas import BaseFilters


def test_validate_range_fields_match_success():
    class ValidFilters(BaseFilters):
        test_from: datetime | None = None
        test_to: datetime | None = None

    ValidFilters(
        test_from=datetime(2025, 1, 1, tzinfo=UTC), test_to=datetime(2025, 1, 2, tzinfo=UTC)
    )


def test_validate_range_fields_not_match():
    class InvalidFilters(BaseFilters):
        pudge_from: datetime | None = None
        something_to: datetime | None = None

    with pytest.raises(ValidationError) as e:
        InvalidFilters()

    assert "Some '_from' fields lack corresponding '_to' fields" in str(e.value)


def test_validate_ranges_with_valid_dates():
    class DateFilters(BaseFilters):
        start_from: datetime | None = None
        start_to: datetime | None = None

    DateFilters(
        start_from=datetime(2025, 1, 1, tzinfo=UTC), start_to=datetime(2025, 1, 2, tzinfo=UTC)
    )

    same_date = datetime(2025, 1, 1, tzinfo=UTC)
    DateFilters(start_from=same_date, start_to=same_date)


def test_validate_ranges_with_invalid_dates():
    class DateFilters(BaseFilters):
        period_from: datetime | None = None
        period_to: datetime | None = None

    with pytest.raises(ValidationError) as e:
        DateFilters(
            period_from=datetime(2025, 1, 1, tzinfo=UTC),
            period_to=datetime(2024, 1, 1, tzinfo=UTC),
        )

    assert "'period_to' must be greater than or equal to 'period_from'" in str(e.value)


def test_validate_ranges_with_partial_dates():
    class PartialFilters(BaseFilters):
        range_from: datetime | None = None
        range_to: datetime | None = None

    PartialFilters(range_from=datetime(2025, 1, 1, tzinfo=UTC))

    PartialFilters(range_to=datetime(2025, 1, 1, tzinfo=UTC))


def test_validate_ranges_with_int_type():
    class IntFilters(BaseFilters):
        value_from: int | None = None
        value_to: int | None = None

    IntFilters(value_from=5, value_to=10)

    with pytest.raises(ValidationError) as e:
        IntFilters(value_from=10, value_to=5)

    assert "'value_to' must be greater than or equal to 'value_from'" in str(e.value)


def test_validate_ranges_with_incomparable_types():
    class MixedFilters(BaseFilters):
        mixed_from: str | None = None
        mixed_to: int | None = None

    with pytest.raises(ValidationError) as e:
        MixedFilters(mixed_from="abc", mixed_to=123)

    assert "Types of 'mixed_from' and 'mixed_to' do not support comparison" in str(e.value)
