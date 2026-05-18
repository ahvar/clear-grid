"""initial migration

Revision ID: 2b33b27957a8
Revises:
Create Date: 2026-05-17 19:21:53.677336

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2b33b27957a8"
down_revision = None
branch_labels = None
depends_on = None


def upgrade(engine_name: str) -> None:
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name: str) -> None:
    globals()["downgrade_%s" % engine_name]()


def upgrade_() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("source_resource_id", sa.String(length=100), nullable=False),
        sa.Column("participant_filter", sa.String(length=255), nullable=True),
        sa.Column("delivery_date", sa.Date(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("records_seen", sa.Integer(), nullable=False),
        sa.Column("records_inserted", sa.Integer(), nullable=False),
        sa.Column("records_updated", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "auction_unit_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=True),
        sa.Column("unit_result_id", sa.String(length=255), nullable=False),
        sa.Column(
            "registered_auction_participant",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("auction_unit", sa.String(length=100), nullable=False),
        sa.Column("service_type", sa.String(length=50), nullable=False),
        sa.Column("auction_product", sa.String(length=100), nullable=False),
        sa.Column("executed_quantity_mw", sa.Numeric(12, 3), nullable=False),
        sa.Column(
            "clearing_price_gbp_per_mw_h",
            sa.Numeric(12, 2),
            nullable=False,
        ),
        sa.Column("delivery_start_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivery_end_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("technology_type", sa.String(length=100), nullable=True),
        sa.Column("post_code", sa.String(length=20), nullable=True),
        sa.Column("source_resource_id", sa.String(length=100), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("raw_record", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("unit_result_id"),
    )
    op.create_index(
        op.f("ix_auction_unit_results_auction_product"),
        "auction_unit_results",
        ["auction_product"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auction_unit_results_auction_unit"),
        "auction_unit_results",
        ["auction_unit"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auction_unit_results_delivery_start_utc"),
        "auction_unit_results",
        ["delivery_start_utc"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auction_unit_results_registered_auction_participant"),
        "auction_unit_results",
        ["registered_auction_participant"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auction_unit_results_service_type"),
        "auction_unit_results",
        ["service_type"],
        unique=False,
    )


def downgrade_() -> None:
    op.drop_index(
        op.f("ix_auction_unit_results_service_type"),
        table_name="auction_unit_results",
    )
    op.drop_index(
        op.f("ix_auction_unit_results_registered_auction_participant"),
        table_name="auction_unit_results",
    )
    op.drop_index(
        op.f("ix_auction_unit_results_delivery_start_utc"),
        table_name="auction_unit_results",
    )
    op.drop_index(
        op.f("ix_auction_unit_results_auction_unit"),
        table_name="auction_unit_results",
    )
    op.drop_index(
        op.f("ix_auction_unit_results_auction_product"),
        table_name="auction_unit_results",
    )
    op.drop_table("auction_unit_results")
    op.drop_table("ingestion_runs")
