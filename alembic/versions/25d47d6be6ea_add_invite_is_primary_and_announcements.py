"""add_invite_is_primary_and_announcements

Revision ID: 25d47d6be6ea
Revises: d020e02dee83
Create Date: 2026-06-20 15:00:05.254761

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "25d47d6be6ea"
down_revision: Union[str, None] = "d020e02dee83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "invites",
        sa.Column(
            "is_primary", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.create_table(
        "announcements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("classroom_id", sa.String(length=36), nullable=False),
        sa.Column("author_id", sa.String(length=36), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"]),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("announcements")
    op.drop_column("invites", "is_primary")
