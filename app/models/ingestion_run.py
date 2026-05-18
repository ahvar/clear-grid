from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db


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
