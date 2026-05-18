# app/etl/normalize.py

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from app.neso.fields import (
    AUCTION_PRODUCT,
    AUCTION_UNIT,
    CLEARING_PRICE,
    DELIVERY_END,
    DELIVERY_START,
    EXECUTED_QUANTITY,
    POST_CODE,
    REGISTERED_AUCTION_PARTICIPANT,
    SERVICE_TYPE,
    TECHNOLOGY_TYPE,
    UNIT_RESULT_ID,
    UNIT_RESULT_FIELD_MAP,
)


class SourceRecordError(ValueError):
    """Raised when a NESO source record cannot be normalized."""


def require_str(record: dict[str, Any], field: str) -> str:
    value = record.get(field)

    if value is None:
        raise SourceRecordError(f"{field} is required")

    value = str(value).strip()

    if not value:
        raise SourceRecordError(f"{field} cannot be blank")

    return value


def optional_str(record: dict[str, Any], field: str) -> str | None:
    value = record.get(field)

    if value is None:
        return None

    value = str(value).strip()
    return value or None


def parse_decimal(record: dict[str, Any], field: str) -> Decimal:
    value = record.get(field)

    if value is None:
        raise SourceRecordError(f"{field} is required")

    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise SourceRecordError(f"{field} must be a decimal-compatible value") from exc


def parse_utc_datetime(record: dict[str, Any], field: str) -> datetime:
    value = record.get(field)

    if not isinstance(value, str) or not value.strip():
        raise SourceRecordError(f"{field} must be a non-empty ISO8601 string")

    normalized = value.strip().replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SourceRecordError(f"{field} must be a valid ISO8601 datetime") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


REQUIRED_UNIT_RESULT_FIELD_NORMALIZERS = (
    (UNIT_RESULT_ID, require_str),
    (REGISTERED_AUCTION_PARTICIPANT, require_str),
    (AUCTION_UNIT, require_str),
    (SERVICE_TYPE, require_str),
    (AUCTION_PRODUCT, require_str),
    (EXECUTED_QUANTITY, parse_decimal),
    (CLEARING_PRICE, parse_decimal),
    (DELIVERY_START, parse_utc_datetime),
    (DELIVERY_END, parse_utc_datetime),
)

OPTIONAL_UNIT_RESULT_FIELD_NORMALIZERS = (
    (TECHNOLOGY_TYPE, optional_str),
    (POST_CODE, optional_str),
)

REQUIRED_UNIT_RESULT_FIELDS = frozenset(
    field for field, _ in REQUIRED_UNIT_RESULT_FIELD_NORMALIZERS
)


def normalize_unit_result(
    record: dict[str, Any],
    *,
    source_resource_id: str,
    ingestion_run_id: int | None = None,
) -> dict[str, Any]:
    missing = REQUIRED_UNIT_RESULT_FIELDS - record.keys()
    if missing:
        raise SourceRecordError(
            f"NESO unit result record missing required fields: {sorted(missing)}"
        )

    normalized = {
        "ingestion_run_id": ingestion_run_id,
        "source_resource_id": source_resource_id,
        "raw_record": record,
    }

    for field, normalizer in REQUIRED_UNIT_RESULT_FIELD_NORMALIZERS:
        normalized[UNIT_RESULT_FIELD_MAP[field]] = normalizer(record, field)

    for field, normalizer in OPTIONAL_UNIT_RESULT_FIELD_NORMALIZERS:
        normalized[UNIT_RESULT_FIELD_MAP[field]] = normalizer(record, field)

    return normalized
