"""create flashcard_set table

NOTE: At the time this migration was added, the rest of the project did not yet
use Alembic — existing tables (`opentutorai_support`, `opentutorai_support_file`)
are created via `Base.metadata.create_all()` in `init_database()`
(see open_tutorai/models/database.py). This file was added in response to PR
review feedback requesting a migration for the new `opentutorai_flashcard_set`
table. The table is also picked up by `create_all()` in dev, so the migration
is currently a safety net rather than the primary schema-management path.
"""

from alembic import op
import sqlalchemy as sa

from open_webui.internal.db import JSONField

# revision identifiers, used by Alembic.
revision = "0001_create_flashcard_set_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "opentutorai_flashcard_set",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source_label", sa.String(), nullable=True),
        sa.Column("support_id", sa.String(), nullable=True),
        sa.Column("model_used", sa.String(), nullable=True),
        sa.Column("cards", JSONField(), nullable=False),
        sa.Column("known_indices", JSONField(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_opentutorai_flashcard_set_user_id",
        "opentutorai_flashcard_set",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_opentutorai_flashcard_set_user_id", table_name="opentutorai_flashcard_set"
    )
    op.drop_table("opentutorai_flashcard_set")
