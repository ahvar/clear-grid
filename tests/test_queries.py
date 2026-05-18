from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app import create_app, db
from app.etl import queries
from app.models import AuctionUnitResult
from tests.test_config import TestConfig


def _result(
    *,
    unit_result_id,
    participant="HABITAT ENERGY LIMITED",
    auction_unit="HAB-UNIT-001",
    service_type="Response",
    auction_product="DCL",
    executed_quantity_mw="5.0",
    clearing_price_gbp_per_mw_h="12.50",
    delivery_start_utc=datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc),
    delivery_end_utc=datetime(2026, 5, 17, 0, 30, tzinfo=timezone.utc),
    technology_type="Batteries",
    post_code="AB12",
):
    return AuctionUnitResult(
        unit_result_id=unit_result_id,
        registered_auction_participant=participant,
        auction_unit=auction_unit,
        service_type=service_type,
        auction_product=auction_product,
        executed_quantity_mw=Decimal(executed_quantity_mw),
        clearing_price_gbp_per_mw_h=Decimal(clearing_price_gbp_per_mw_h),
        delivery_start_utc=delivery_start_utc,
        delivery_end_utc=delivery_end_utc,
        technology_type=technology_type,
        post_code=post_code,
        source_resource_id="test-resource",
        raw_record={"unitResultID": unit_result_id},
    )


class TestAuctionUnitResultQueries:
    def setup_method(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        db.session.add_all(
            [
                _result(
                    unit_result_id="HAB-UNIT-001#DCL#2026-05-17T00:00:00Z",
                    auction_unit="HAB-UNIT-001",
                    auction_product="DCL",
                    executed_quantity_mw="5.0",
                    clearing_price_gbp_per_mw_h="12.50",
                    delivery_start_utc=datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc),
                    delivery_end_utc=datetime(2026, 5, 17, 0, 30, tzinfo=timezone.utc),
                    technology_type="Batteries",
                    post_code="AB12",
                ),
                _result(
                    unit_result_id="SPECIAL-RESULT-002",
                    auction_unit="HAB-UNIT-002",
                    auction_product="DCH",
                    executed_quantity_mw="3.0",
                    clearing_price_gbp_per_mw_h="15.25",
                    delivery_start_utc=datetime(
                        2026, 5, 17, 0, 30, tzinfo=timezone.utc
                    ),
                    delivery_end_utc=datetime(2026, 5, 17, 1, 0, tzinfo=timezone.utc),
                    technology_type="Solar",
                    post_code="ZZ77",
                ),
                _result(
                    unit_result_id="HAB-QUICK#NQR#2026-05-17T01:00:00Z",
                    auction_unit="HAB-QUICK",
                    service_type="Quick Reserve",
                    auction_product="NQR",
                    delivery_start_utc=datetime(2026, 5, 17, 1, 0, tzinfo=timezone.utc),
                    delivery_end_utc=datetime(2026, 5, 17, 1, 30, tzinfo=timezone.utc),
                ),
                _result(
                    unit_result_id="OTHER-UNIT-001#DCL#2026-05-17T01:30:00Z",
                    participant="OTHER PARTICIPANT",
                    auction_unit="OTHER-UNIT-001",
                    delivery_start_utc=datetime(
                        2026, 5, 17, 1, 30, tzinfo=timezone.utc
                    ),
                    delivery_end_utc=datetime(2026, 5, 17, 2, 0, tzinfo=timezone.utc),
                ),
            ]
        )
        db.session.commit()

    def teardown_method(self):
        db.session.rollback()
        db.drop_all()
        self.app_context.pop()

    def _paginated_results(self, *, start=None, length=None, sort=None, search=None):
        query = queries.paginated_auction_unit_results(start, length, sort, search)
        return db.session.execute(query).scalars().all()

    def test_paginated_results_only_include_habitat_response_rows(self):
        results = self._paginated_results()

        assert [result.auction_unit for result in results] == [
            "HAB-UNIT-001",
            "HAB-UNIT-002",
        ]
        assert all(
            result.registered_auction_participant == "HABITAT ENERGY LIMITED"
            for result in results
        )
        assert all(result.service_type == "Response" for result in results)

    @pytest.mark.parametrize(
        ("search", "expected_unit"),
        [
            ("UNIT-002", "HAB-UNIT-002"),
            ("DCH", "HAB-UNIT-002"),
            ("Solar", "HAB-UNIT-002"),
            ("ZZ77", "HAB-UNIT-002"),
            ("SPECIAL-RESULT", "HAB-UNIT-002"),
        ],
    )
    def test_paginated_results_searches_supported_fields(self, search, expected_unit):
        results = self._paginated_results(search=search)

        assert [result.auction_unit for result in results] == [expected_unit]

    def test_habitat_results_count_matches_paginated_filters(self):
        count = db.session.scalar(queries.habitat_results("DCH"))
        results = self._paginated_results(search="DCH")

        assert count == len(results) == 1

    @pytest.mark.parametrize(
        "sort",
        [
            "+date",
            "-participant",
            "+product",
            "-quantity",
            "+clearing_price",
            "-id",
        ],
    )
    def test_paginated_results_supports_expected_sort_columns(self, sort):
        results = self._paginated_results(sort=sort)

        assert len(results) == 2

    def test_paginated_results_sorts_and_paginates(self):
        results = self._paginated_results(start="0", length="1", sort="-quantity")

        assert [result.auction_unit for result in results] == ["HAB-UNIT-001"]

    def test_daily_auction_results_route_returns_result_collection(self):
        response = self.app.test_client().get("/api/daily-auction-results")

        assert response.status_code == 200
        payload = response.get_json()
        assert set(payload) == {"data", "total"}
        assert payload["total"] == 2
        assert [row["auction_unit"] for row in payload["data"]] == [
            "HAB-UNIT-001",
            "HAB-UNIT-002",
        ]
        assert payload["data"][0]["unit_result_id"] == (
            "HAB-UNIT-001#DCL#2026-05-17T00:00:00Z"
        )

    def test_daily_auction_results_route_passes_query_params_to_queries(self):
        response = self.app.test_client().get(
            "/api/daily-auction-results",
            query_string={
                "search": "DCH",
                "sort": "-quantity",
                "start": "0",
                "length": "1",
            },
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["total"] == 1
        assert [row["auction_unit"] for row in payload["data"]] == ["HAB-UNIT-002"]

    def test_root_is_no_longer_served_by_flask(self):
        response = self.app.test_client().get(
            "/", headers={"Accept": "application/json"}
        )

        assert response.status_code == 404
