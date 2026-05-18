import os
from app import db
from decimal import Decimal
from datetime import datetime, date
from typing import Any
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from config import Config


class IngestionRun(db.Model):
    """Tracks a single ingestion attempt for auction unit result data."""

    __tablename__ = "ingestion_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    participant_filter: Mapped[str | None] = mapped_column(String(255))
    delivery_date: Mapped[date | None] = mapped_column(Date)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="started")
    records_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)

    unit_results: Mapped[list["AuctionUnitResult"]] = relationship(
        back_populates="ingestion_run"
    )

    def to_dict(self):
        """Return a JSON-safe representation of the ingestion run."""

        return {
            "id": self.id,
            "source_name": self.source_name,
            "source_resource_id": self.source_resource_id,
            "participant_filter": self.participant_filter,
            "delivery_date": (
                self.delivery_date.isoformat() if self.delivery_date else None
            ),
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "status": self.status,
            "records_seen": self.records_seen,
            "records_inserted": self.records_inserted,
            "records_updated": self.records_updated,
            "error_message": self.error_message,
        }

    def __repr__(self):
        """Return a compact identifier for debugging output."""

        return (
            "IngestionRun("
            f"id={self.id}, "
            f"source_name={self.source_name!r}, "
            f"source_resource_id={self.source_resource_id!r}, "
            f"status={self.status!r}"
            ")"
        )


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
        Numeric[12, 2], nullable=False
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
    ingestion_run: Mapped[IngestionRun | None] = relationship(
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
