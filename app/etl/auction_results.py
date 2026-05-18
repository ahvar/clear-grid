from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import AuctionUnitResult


@dataclass(frozen=True)
class AuctionUnitResultUpsertResult:
    inserted: int = 0
    updated: int = 0


def upsert_auction_unit_results(
    session: Session,
    rows: list[dict[str, object]],
) -> AuctionUnitResultUpsertResult:
    inserted = 0
    updated = 0

    for row in rows:
        unit_result_id = row["unit_result_id"]
        existing = session.query(AuctionUnitResult).filter_by(
            unit_result_id=unit_result_id
        ).one_or_none()

        if existing is None:
            session.add(AuctionUnitResult(**row))
            inserted += 1
            continue

        for field, value in row.items():
            setattr(existing, field, value)

        updated += 1

    return AuctionUnitResultUpsertResult(inserted=inserted, updated=updated)