"""initial migration

Revision ID: 2b33b27957a8
Revises: 
Create Date: 2026-05-17 19:21:53.677336

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b33b27957a8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade(engine_name: str) -> None:
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name: str) -> None:
    globals()["downgrade_%s" % engine_name]()





def upgrade_() -> None:
    pass


def downgrade_() -> None:
    pass

