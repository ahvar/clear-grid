# app/neso/types.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, TypeAlias

RawNesoRecord: TypeAlias = dict[str, Any]


@dataclass(frozen=True)
class NesoUnitResultsQuery:
    participant: str
    delivery_date: date
    resource_id: str | None = None
    page_size: int = 1000
