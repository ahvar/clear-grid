from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from app import create_app
from tests.test_config import TestConfig


class CliConfig(TestConfig):
    INGEST_DELIVERY_DATE = "2026-05-17"
    INGEST_PARTICIPANT = "HABITAT ENERGY LIMITED"
    INGEST_RESOURCE_ID = "resource-from-config"
    NESO_RESOURCE_ID = "neso-resource-from-config"


class CliFallbackConfig(TestConfig):
    INGEST_DELIVERY_DATE = None
    INGEST_PARTICIPANT = None
    INGEST_RESOURCE_ID = None
    NESO_RESOURCE_ID = "neso-resource-from-config"


def _completed_run():
    return SimpleNamespace(
        id=42,
        status="completed",
        records_seen=3,
        records_inserted=2,
        records_updated=1,
    )


def test_ingest_unit_results_uses_config_defaults():
    app = create_app(CliConfig)

    with patch(
        "app.cli.ingest_unit_results_for_day", return_value=_completed_run()
    ) as ingest:
        result = app.test_cli_runner().invoke(args=["ingest-unit-results"])

    assert result.exit_code == 0
    assert "Ingestion run 42 completed" in result.output
    ingest.assert_called_once_with(
        resource_id="resource-from-config",
        participant="HABITAT ENERGY LIMITED",
        delivery_date=date(2026, 5, 17),
    )


def test_ingest_unit_results_uses_options_and_neso_resource_fallback():
    app = create_app(CliFallbackConfig)

    with patch(
        "app.cli.ingest_unit_results_for_day", return_value=_completed_run()
    ) as ingest:
        result = app.test_cli_runner().invoke(
            args=[
                "ingest-unit-results",
                "--date",
                "2026-05-18",
                "--participant",
                "ACME ENERGY",
            ]
        )

    assert result.exit_code == 0
    ingest.assert_called_once_with(
        resource_id="neso-resource-from-config",
        participant="ACME ENERGY",
        delivery_date=date(2026, 5, 18),
    )


def test_ingest_unit_results_rejects_invalid_date():
    app = create_app(CliConfig)

    result = app.test_cli_runner().invoke(
        args=["ingest-unit-results", "--date", "2026/05/17"]
    )

    assert result.exit_code != 0
    assert "must be a date in YYYY-MM-DD format" in result.output
