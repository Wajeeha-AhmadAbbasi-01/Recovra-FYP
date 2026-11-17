"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-11-17
"""

from typing import Sequence, Union

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use scripts/bootstrap_db.py or autogenerate against a live Postgres for full migration history.
    pass


def downgrade() -> None:
    pass