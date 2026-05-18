from datetime import date
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.neso.client import NesoApiError, SyncNesoResultsClient
from app.neso.types import NesoUnitResultsQuery
from config import Config


class TestSyncNesoResultsClient:
    def setup_method(self):
        self.base_url = "https://example.test"
        self.query = NesoUnitResultsQuery(
            participant="HABITAT ENERGY LIMITED",
            delivery_date=date(2026, 5, 17),
        )
        self.client = None
        self.http_client = MagicMock(spec=httpx.Client)
        self.client_patch = patch(
            "app.neso.client.httpx.Client", return_value=self.http_client
        )
        self.mock_client_class = self.client_patch.start()

    def teardown_method(self):
        if self.client is not None:
            self.client.close()
        self.client_patch.stop()

    @staticmethod
    def _success_response(records: list[dict[str, int]]) -> httpx.Response:
        request = httpx.Request("GET", "https://example.test/datastore_search_sql")
        return httpx.Response(
            200,
            json={"success": True, "result": {"records": records}},
            request=request,
        )

    @staticmethod
    def _connect_error() -> httpx.ConnectError:
        request = httpx.Request("GET", "https://example.test/datastore_search_sql")
        return httpx.ConnectError("boom", request=request)

    def test_uses_config_resource_id_by_default(self):
        self.client = SyncNesoResultsClient(base_url=self.base_url)

        sql = self.client._build_sql(self.query, 0)

        assert f'FROM "{Config.NESO_RESOURCE_ID}"' in sql
        self.mock_client_class.assert_called_once_with(
            base_url=self.base_url,
            timeout=20.0,
        )

    def test_iterates_until_final_partial_page(self):
        self.http_client.get.side_effect = [
            self._success_response([{"id": 1}, {"id": 2}]),
            self._success_response([{"id": 3}]),
        ]
        self.client = SyncNesoResultsClient(base_url=self.base_url)
        query = NesoUnitResultsQuery(
            participant=self.query.participant,
            delivery_date=self.query.delivery_date,
            page_size=2,
        )

        pages = list(self.client.iter_unit_result_pages(query))

        assert pages == [[{"id": 1}, {"id": 2}], [{"id": 3}]]

    def test_wraps_request_errors(self):
        self.http_client.get.side_effect = self._connect_error()
        self.client = SyncNesoResultsClient(base_url=self.base_url)

        with pytest.raises(NesoApiError, match="NESO API request failed"):
            list(self.client.iter_unit_result_pages(self.query))
