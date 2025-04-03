"""Add role column to auth table

Revision ID: d168b4c3f9a4
Revises: 3781e22d8b01
Create Date: 2025-04-02 14:21:49.043700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'd168b4c3f9a4'
down_revision: Union[str, None] = '3781e22d8b01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    # Add role column to auth table with default value 'student'
    op.add_column('auth', sa.Column('role', sa.String(), nullable=True, server_default='student'))


def downgrade() -> None:
    # Remove role column from auth table
    op.drop_column('auth', 'role') 