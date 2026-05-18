from __future__ import annotations

from datetime import date

import click
from flask import current_app
from flask.cli import with_appcontext

from app.etl.unit_result_ingestion import ingest_unit_results_for_day


def register_cli(app):
    app.cli.add_command(ingest_unit_results)


def _config_value(name: str) -> str | None:
    value = current_app.config.get(name)
    if value is None:
        return None

    value = str(value).strip()
    return value or None


def _parse_delivery_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise click.BadParameter("must be a date in YYYY-MM-DD format") from exc


@click.command("ingest-unit-results")
@click.option(
    "--date",
    "delivery_date",
    help="Delivery date to ingest in YYYY-MM-DD format.",
)
@click.option(
    "--participant",
    help="Registered auction participant to ingest.",
)
@click.option(
    "--resource-id",
    help="NESO datastore resource id.",
)
@with_appcontext
def ingest_unit_results(
    delivery_date: str | None,
    participant: str | None,
    resource_id: str | None,
) -> None:
    delivery_date_value = delivery_date or _config_value("INGEST_DELIVERY_DATE")
    participant_value = participant or _config_value("INGEST_PARTICIPANT")
    resource_id_value = (
        resource_id
        or _config_value("INGEST_RESOURCE_ID")
        or _config_value("NESO_RESOURCE_ID")
    )

    if delivery_date_value is None:
        raise click.UsageError(
            "--date is required when INGEST_DELIVERY_DATE is not configured"
        )
    if participant_value is None:
        raise click.UsageError(
            "--participant is required when INGEST_PARTICIPANT is not configured"
        )
    if resource_id_value is None:
        raise click.UsageError(
            "--resource-id is required when INGEST_RESOURCE_ID and NESO_RESOURCE_ID "
            "are not configured"
        )

    run = ingest_unit_results_for_day(
        resource_id=resource_id_value,
        participant=participant_value,
        delivery_date=_parse_delivery_date(delivery_date_value),
    )

    click.echo(
        "Ingestion run "
        f"{run.id} {run.status}: "
        f"seen={run.records_seen} "
        f"inserted={run.records_inserted} "
        f"updated={run.records_updated}"
    )
