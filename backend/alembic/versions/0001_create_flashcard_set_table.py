from alembic import op
import sqlalchemy as sa

from open_webui.internal.db import JSONField

# revision identifiers, used by Alembic.
revision = '0001_create_flashcard_set_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'opentutorai_flashcard_set',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('source_label', sa.String(), nullable=True),
        sa.Column('support_id', sa.String(), nullable=True),
        sa.Column('model_used', sa.String(), nullable=True),
        sa.Column('cards', JSONField(), nullable=False),
        sa.Column('known_indices', JSONField(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(
        'ix_opentutorai_flashcard_set_user_id',
        'opentutorai_flashcard_set',
        ['user_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_opentutorai_flashcard_set_user_id', table_name='opentutorai_flashcard_set')
    op.drop_table('opentutorai_flashcard_set')
