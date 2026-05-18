# app/etl/unit_result_ingestion.py

from __future__ import annotations

from datetime import date

from app import db
from app.etl.auction_results import upsert_auction_unit_results
from app.etl.normalize import normalize_unit_result
from app.models import IngestionRun
from app.neso.client import SyncNesoResultsClient
from app.neso.types import NesoUnitResultsQuery


def ingest_unit_results_for_day(
    *,
    resource_id: str,
    participant: str,
    delivery_date: date,
) -> IngestionRun:
    run = IngestionRun(
        source_name="neso_response_reserve_results_by_unit",
        source_resource_id=resource_id,
        participant_filter=participant,
        delivery_date=delivery_date,
        status="started",
    )

    db.session.add(run)
    db.session.commit()

    try:
        query = NesoUnitResultsQuery(
            resource_id=resource_id,
            participant=participant,
            delivery_date=delivery_date,
            page_size=1000,
        )

        with SyncNesoResultsClient() as client:
            for page in client.iter_unit_result_pages(query):
                rows = [
                    normalize_unit_result(
                        record=record,
                        ingestion_run_id=run.id,
                        source_resource_id=resource_id,
                    )
                    for record in page
                ]

                result = upsert_auction_unit_results(db.session, rows)

                run.records_seen += len(page)
                run.records_inserted += result.inserted
                run.records_updated += result.updated

                db.session.commit()

        run.status = "completed"
        db.session.commit()

    except Exception as exc:
        db.session.rollback()
        run.status = "failed"
        run.error_message = str(exc)
        db.session.add(run)
        db.session.commit()
        raise

    return run
