"""add_objectives_to_class_sessions

Revision ID: 96394a73af7d
Revises: 25d47d6be6ea
Create Date: 2026-06-22 20:34:40.953641

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "96394a73af7d"
down_revision: Union[str, None] = "25d47d6be6ea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("class_sessions", sa.Column("objectives", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("class_sessions", "objectives")
