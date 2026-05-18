# app/neso/client.py

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID

import httpx

from config import Config
from app.neso.fields import (
    AUCTION_PRODUCT,
    AUCTION_UNIT,
    DELIVERY_START,
    UNIT_RESULT_FIELDS as NESO_UNIT_RESULT_FIELDS,
    REGISTERED_AUCTION_PARTICIPANT,
    UNIT_RESULT_ID,
)
from app.neso.types import NesoUnitResultsQuery, RawNesoRecord


class NesoApiError(RuntimeError):
    """Raised when NESO/CKAN returns an invalid or unsuccessful response."""


class BaseNesoResultsClient:
    REQUEST_PATH = "/datastore_search_sql"
    UNIT_RESULT_FIELDS = NESO_UNIT_RESULT_FIELDS

    def __init__(
        self,
        base_url: str = Config.NESO_API_BASE_URL,
        resource_id: str = Config.NESO_RESOURCE_ID,
    ) -> None:
        self.base_url = base_url
        self.resource_id = resource_id

    def _build_sql(self, query: NesoUnitResultsQuery, offset: int) -> str:
        self._validate_query(query)

        start = datetime.combine(
            query.delivery_date,
            time.min,
            tzinfo=timezone.utc,
        )
        end = start + timedelta(days=1)

        selected_fields = ", ".join(f'"{field}"' for field in self.UNIT_RESULT_FIELDS)
        resource_id = self._resource_id(query)

        return (
            f"SELECT {selected_fields} "
            f'FROM "{resource_id}" '
            f'WHERE "{REGISTERED_AUCTION_PARTICIPANT}" = {self._sql_literal(query.participant)} '
            f'AND "{DELIVERY_START}" >= {self._sql_literal(self._neso_datetime(start))} '
            f'AND "{DELIVERY_START}" < {self._sql_literal(self._neso_datetime(end))} '
            f'ORDER BY "{DELIVERY_START}", "{AUCTION_UNIT}", "{AUCTION_PRODUCT}", "{UNIT_RESULT_ID}" '
            f"LIMIT {query.page_size} "
            f"OFFSET {offset}"
        )

    def _extract_records(self, response: httpx.Response) -> list[RawNesoRecord]:
        try:
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise NesoApiError(f"NESO API request failed: {exc}") from exc
        except ValueError as exc:
            raise NesoApiError("NESO API response was not valid JSON") from exc

        if not payload.get("success"):
            raise NesoApiError(f"NESO API returned unsuccessful payload: {payload}")

        result = payload.get("result")
        if not isinstance(result, dict):
            raise NesoApiError(f"NESO API response missing result object: {payload}")

        records = result.get("records")
        if not isinstance(records, list):
            raise NesoApiError(f"NESO API response missing records list: {payload}")

        return records

    def _request_params(
        self, query: NesoUnitResultsQuery, offset: int
    ) -> dict[str, str]:
        return {"sql": self._build_sql(query, offset)}

    @staticmethod
    def _next_offset(
        current_offset: int,
        returned_records: int,
        page_size: int,
    ) -> int | None:
        if returned_records == 0 or returned_records < page_size:
            return None

        return current_offset + page_size

    def _resource_id(self, query: NesoUnitResultsQuery) -> str:
        return query.resource_id or self.resource_id

    def _raise_request_error(self, exc: httpx.RequestError) -> None:
        raise NesoApiError(f"NESO API request failed: {exc}") from exc

    def _validate_query(self, query: NesoUnitResultsQuery) -> None:
        # Prevent table-name injection into datastore_search_sql.
        UUID(self._resource_id(query))

        if not 1 <= query.page_size <= 32000:
            raise ValueError("page_size must be between 1 and 32000")

        if not query.participant.strip():
            raise ValueError("participant is required")

    @staticmethod
    def _sql_literal(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    @staticmethod
    def _neso_datetime(value: datetime) -> str:
        # NESO examples show ISO8601 datetimes. Keep this deterministic.
        return value.astimezone(timezone.utc).replace(tzinfo=None).isoformat()


class SyncNesoResultsClient(BaseNesoResultsClient):
    def __init__(
        self,
        *,
        base_url: str = Config.NESO_API_BASE_URL,
        resource_id: str = Config.NESO_RESOURCE_ID,
        timeout: float = 20.0,
    ) -> None:
        super().__init__(base_url=base_url, resource_id=resource_id)
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
        )

    def _get_page(
        self, query: NesoUnitResultsQuery, offset: int
    ) -> list[RawNesoRecord]:
        try:
            response = self._client.get(
                self.REQUEST_PATH,
                params=self._request_params(query, offset),
            )
        except httpx.RequestError as exc:
            self._raise_request_error(exc)

        return self._extract_records(response)

    def iter_unit_result_pages(
        self,
        query: NesoUnitResultsQuery,
    ) -> Iterator[list[RawNesoRecord]]:
        offset: int | None = 0

        while offset is not None:
            records = self._get_page(query, offset)
            if not records:
                return
            yield records
            offset = self._next_offset(offset, len(records), query.page_size)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SyncNesoResultsClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncNesoResultsClient(BaseNesoResultsClient):
    """Future async client stub for non-blocking orchestration use cases."""

    def __init__(
        self,
        *,
        base_url: str = Config.NESO_API_BASE_URL,
        resource_id: str = Config.NESO_RESOURCE_ID,
        timeout: float = 20.0,
    ) -> None:
        super().__init__(base_url=base_url, resource_id=resource_id)
        self.timeout = timeout

    async def aiter_unit_result_pages(
        self,
        query: NesoUnitResultsQuery,
    ) -> AsyncIterator[list[RawNesoRecord]]:
        raise NotImplementedError(
            "AsyncNesoResultsClient is a future stub; use SyncNesoResultsClient for now."
        )

    async def aclose(self) -> None:
        return None

    async def __aenter__(self) -> "AsyncNesoResultsClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
