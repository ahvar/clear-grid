from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


class AuctionUnitResult(db.Model):
    """Stores a single auction unit result record captured from an ingestion run."""

    __tablename__ = "auction_unit_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ingestion_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("ingestion_runs.id"), nullable=True
    )
    unit_result_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    registered_auction_participant: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    auction_unit: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    service_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    auction_product: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    executed_quantity_mw: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False
    )
    clearing_price_gbp_per_mw_h: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    delivery_start_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    delivery_end_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    technology_type: Mapped[str | None] = mapped_column(String(100))
    post_code: Mapped[str | None] = mapped_column(String(20))
    source_resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    raw_record: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    ingestion_run: Mapped["IngestionRun | None"] = relationship(
        back_populates="unit_results"
    )

    def to_dict(self):
        """Return a JSON-safe representation of the auction unit result."""

        return {
            "id": self.id,
            "ingestion_run_id": self.ingestion_run_id,
            "unit_result_id": self.unit_result_id,
            "registered_auction_participant": self.registered_auction_participant,
            "auction_unit": self.auction_unit,
            "service_type": self.service_type,
            "auction_product": self.auction_product,
            "executed_quantity_mw": str(self.executed_quantity_mw),
            "clearing_price_gbp_per_mw_h": str(self.clearing_price_gbp_per_mw_h),
            "delivery_start_utc": self.delivery_start_utc.isoformat(),
            "delivery_end_utc": self.delivery_end_utc.isoformat(),
            "technology_type": self.technology_type,
            "post_code": self.post_code,
            "source_resource_id": self.source_resource_id,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
            "raw_record": self.raw_record,
        }

    def __repr__(self):
        """Return a compact identifier for debugging output."""

        return (
            "AuctionUnitResult("
            f"id={self.id}, "
            f"unit_result_id={self.unit_result_id!r}, "
            f"auction_unit={self.auction_unit!r}, "
            f"auction_product={self.auction_product!r}"
            ")"
        )
