import csv
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from app import create_app, db
from app.models import AuctionUnitResult, IngestionRun
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
)
from tests.test_config import TestConfig

NESO_CSV_PATH = Path(__file__).resolve().parents[1] / "neso.csv"


def _read_neso_rows():
    with NESO_CSV_PATH.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _parse_utc_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _auction_unit_result_from_csv_row(row, source_resource_id="test-resource"):
    return AuctionUnitResult(
        unit_result_id=row[UNIT_RESULT_ID],
        registered_auction_participant=row[REGISTERED_AUCTION_PARTICIPANT],
        auction_unit=row[AUCTION_UNIT],
        service_type=row[SERVICE_TYPE],
        auction_product=row[AUCTION_PRODUCT],
        executed_quantity_mw=Decimal(row[EXECUTED_QUANTITY]),
        clearing_price_gbp_per_mw_h=Decimal(row[CLEARING_PRICE]),
        delivery_start_utc=_parse_utc_datetime(row[DELIVERY_START]),
        delivery_end_utc=_parse_utc_datetime(row[DELIVERY_END]),
        technology_type=row[TECHNOLOGY_TYPE],
        post_code=row[POST_CODE],
        source_resource_id=source_resource_id,
        raw_record=row,
    )


class TestAuctionUnitResult:
    def setup_method(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def teardown_method(self):
        self.app_context.pop()

    def test_to_dict_serializes_expected_fields(self):
        delivery_start = datetime(2026, 5, 17, 10, 0, tzinfo=timezone.utc)
        delivery_end = datetime(2026, 5, 17, 11, 0, tzinfo=timezone.utc)
        ingested_at = datetime(2026, 5, 17, 9, 30, tzinfo=timezone.utc)
        result = AuctionUnitResult(
            id=1,
            ingestion_run_id=2,
            unit_result_id="unit-123",
            registered_auction_participant="Participant A",
            auction_unit="Unit A",
            service_type="Response",
            auction_product="Reserve",
            executed_quantity_mw=Decimal("12.345"),
            clearing_price_gbp_per_mw_h=Decimal("99.99"),
            delivery_start_utc=delivery_start,
            delivery_end_utc=delivery_end,
            technology_type="Battery",
            post_code="AB12 3CD",
            source_resource_id="resource-123",
            ingested_at=ingested_at,
            raw_record={"key": "value"},
        )

        assert result.to_dict() == {
            "id": 1,
            "ingestion_run_id": 2,
            "unit_result_id": "unit-123",
            "registered_auction_participant": "Participant A",
            "auction_unit": "Unit A",
            "service_type": "Response",
            "auction_product": "Reserve",
            "executed_quantity_mw": "12.345",
            "clearing_price_gbp_per_mw_h": "99.99",
            "delivery_start_utc": delivery_start.isoformat(),
            "delivery_end_utc": delivery_end.isoformat(),
            "technology_type": "Battery",
            "post_code": "AB12 3CD",
            "source_resource_id": "resource-123",
            "ingested_at": ingested_at.isoformat(),
            "raw_record": {"key": "value"},
        }

    def test_builds_from_first_csv_row_with_expected_conversions(self):
        first_row = _read_neso_rows()[0]

        result = _auction_unit_result_from_csv_row(first_row)

        assert result.unit_result_id == "HAB-UNIT-001#DCL#2026-05-17T00:00:00Z"
        assert result.registered_auction_participant == "HABITAT ENERGY LIMITED"
        assert result.executed_quantity_mw == Decimal("5.0")
        assert result.clearing_price_gbp_per_mw_h == Decimal("12.50")
        assert result.delivery_start_utc == datetime(
            2026, 5, 17, 0, 0, tzinfo=timezone.utc
        )
        assert result.delivery_end_utc == datetime(
            2026, 5, 17, 0, 30, tzinfo=timezone.utc
        )
        assert result.raw_record == first_row


class TestIngestionRun:
    def setup_method(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def teardown_method(self):
        self.app_context.pop()

    def test_repr_includes_identifying_fields(self):
        run = IngestionRun(
            id=7,
            source_name="NESO",
            source_resource_id="resource-456",
            participant_filter="Participant A",
            delivery_date=date(2026, 5, 17),
            started_at=datetime(2026, 5, 17, 8, 0, tzinfo=timezone.utc),
            completed_at=None,
            status="completed",
            records_seen=10,
            records_inserted=8,
            records_updated=2,
            error_message=None,
        )

        assert repr(run) == (
            "IngestionRun("
            "id=7, "
            "source_name='NESO', "
            "source_resource_id='resource-456', "
            "status='completed'"
            ")"
        )

    def test_csv_filter_selects_only_habitat_energy_rows(self):
        rows = _read_neso_rows()

        filtered_results = [
            _auction_unit_result_from_csv_row(row)
            for row in rows
            if row[REGISTERED_AUCTION_PARTICIPANT] == "HABITAT ENERGY LIMITED"
        ]

        assert len(filtered_results) == 2
        assert [result.auction_unit for result in filtered_results] == [
            "HAB-UNIT-001",
            "HAB-UNIT-002",
        ]

    def test_persists_related_auction_unit_result_in_sqlite(self):
        db.create_all()

        try:
            ingestion_run = IngestionRun(
                source_name="NESO",
                source_resource_id="resource-456",
                participant_filter="HABITAT ENERGY LIMITED",
                delivery_date=date(2026, 5, 17),
                started_at=datetime(2026, 5, 17, 8, 0, tzinfo=timezone.utc),
                status="completed",
                records_seen=2,
                records_inserted=2,
                records_updated=0,
                error_message=None,
            )
            auction_unit_result = _auction_unit_result_from_csv_row(
                _read_neso_rows()[0],
                source_resource_id=ingestion_run.source_resource_id,
            )
            ingestion_run.unit_results.append(auction_unit_result)

            db.session.add(ingestion_run)
            db.session.commit()

            persisted_run = db.session.get(IngestionRun, ingestion_run.id)

            assert persisted_run is not None
            assert persisted_run.source_name == "NESO"
            assert len(persisted_run.unit_results) == 1
            assert persisted_run.unit_results[0].unit_result_id == (
                "HAB-UNIT-001#DCL#2026-05-17T00:00:00Z"
            )
            assert persisted_run.unit_results[0].ingestion_run_id == persisted_run.id
        finally:
            db.session.rollback()
            db.drop_all()
