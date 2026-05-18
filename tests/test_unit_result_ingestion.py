from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app import create_app, db
from app.etl.unit_result_ingestion import ingest_unit_results_for_day
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


class TestUnitResultIngestion:
    def setup_method(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.delivery_date = date(2026, 5, 17)
        self.resource_id = "resource-123"
        self.participant = "HABITAT ENERGY LIMITED"
        self.client_patch = patch("app.etl.unit_result_ingestion.SyncNesoResultsClient")
        self.mock_client_class = self.client_patch.start()
        self.mock_client = MagicMock()
        self.mock_client_class.return_value.__enter__.return_value = self.mock_client
        self.mock_client_class.return_value.__exit__.return_value = False

    def teardown_method(self):
        db.session.rollback()
        db.drop_all()
        self.client_patch.stop()
        self.app_context.pop()

    @staticmethod
    def _raw_record(
        *,
        unit_result_id: str = "HAB-UNIT-001#DCL#2026-05-17T00:00:00Z",
        executed_quantity: str = "5.0",
        clearing_price: str = "12.50",
    ):
        return {
            UNIT_RESULT_ID: unit_result_id,
            REGISTERED_AUCTION_PARTICIPANT: "HABITAT ENERGY LIMITED",
            AUCTION_UNIT: unit_result_id.split("#", maxsplit=1)[0],
            SERVICE_TYPE: "Response",
            AUCTION_PRODUCT: "Reserve",
            EXECUTED_QUANTITY: executed_quantity,
            CLEARING_PRICE: clearing_price,
            DELIVERY_START: "2026-05-17T00:00:00Z",
            DELIVERY_END: "2026-05-17T00:30:00Z",
            TECHNOLOGY_TYPE: "Battery",
            POST_CODE: "AB12 3CD",
        }

    def test_ingests_pages_and_persists_results(self):
        self.mock_client.iter_unit_result_pages.return_value = iter(
            [
                [
                    self._raw_record(
                        unit_result_id="HAB-UNIT-001#DCL#2026-05-17T00:00:00Z"
                    )
                ],
                [
                    self._raw_record(
                        unit_result_id="HAB-UNIT-002#DCL#2026-05-17T00:30:00Z"
                    )
                ],
            ]
        )

        run = ingest_unit_results_for_day(
            resource_id=self.resource_id,
            participant=self.participant,
            delivery_date=self.delivery_date,
        )

        persisted_run = db.session.get(IngestionRun, run.id)
        persisted_results = (
            db.session.query(AuctionUnitResult)
            .order_by(AuctionUnitResult.unit_result_id)
            .all()
        )

        assert persisted_run is not None
        assert persisted_run.status == "completed"
        assert persisted_run.records_seen == 2
        assert persisted_run.records_inserted == 2
        assert persisted_run.records_updated == 0
        assert len(persisted_results) == 2
        assert all(
            result.ingestion_run_id == persisted_run.id for result in persisted_results
        )
        assert persisted_results[0].source_resource_id == self.resource_id

    def test_updates_existing_unit_results(self):
        existing_run = IngestionRun(
            source_name="neso_response_reserve_results_by_unit",
            source_resource_id=self.resource_id,
            participant_filter=self.participant,
            delivery_date=self.delivery_date,
            status="completed",
        )
        existing_result = AuctionUnitResult(
            ingestion_run=existing_run,
            unit_result_id="HAB-UNIT-001#DCL#2026-05-17T00:00:00Z",
            registered_auction_participant=self.participant,
            auction_unit="HAB-UNIT-001",
            service_type="Response",
            auction_product="Reserve",
            executed_quantity_mw=Decimal("5.0"),
            clearing_price_gbp_per_mw_h=Decimal("12.50"),
            delivery_start_utc=datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc),
            delivery_end_utc=datetime(2026, 5, 17, 0, 30, tzinfo=timezone.utc),
            technology_type="Battery",
            post_code="AB12 3CD",
            source_resource_id=self.resource_id,
            raw_record=self._raw_record(),
        )
        db.session.add(existing_result)
        db.session.commit()

        self.mock_client.iter_unit_result_pages.return_value = iter(
            [
                [
                    self._raw_record(
                        unit_result_id="HAB-UNIT-001#DCL#2026-05-17T00:00:00Z",
                        clearing_price="19.75",
                    )
                ]
            ]
        )

        run = ingest_unit_results_for_day(
            resource_id=self.resource_id,
            participant=self.participant,
            delivery_date=self.delivery_date,
        )

        persisted_run = db.session.get(IngestionRun, run.id)
        persisted_result = (
            db.session.query(AuctionUnitResult)
            .filter_by(unit_result_id="HAB-UNIT-001#DCL#2026-05-17T00:00:00Z")
            .one()
        )

        assert persisted_run is not None
        assert persisted_run.status == "completed"
        assert persisted_run.records_seen == 1
        assert persisted_run.records_inserted == 0
        assert persisted_run.records_updated == 1
        assert persisted_result.clearing_price_gbp_per_mw_h == Decimal("19.75")
        assert persisted_result.ingestion_run_id == persisted_run.id

    def test_marks_run_failed_when_client_raises(self):
        self.mock_client.iter_unit_result_pages.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            ingest_unit_results_for_day(
                resource_id=self.resource_id,
                participant=self.participant,
                delivery_date=self.delivery_date,
            )

        persisted_runs = db.session.query(IngestionRun).order_by(IngestionRun.id).all()

        assert len(persisted_runs) == 1
        assert persisted_runs[0].status == "failed"
        assert persisted_runs[0].error_message == "boom"
        assert db.session.query(AuctionUnitResult).count() == 0
