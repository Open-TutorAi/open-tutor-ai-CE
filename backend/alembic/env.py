from __future__ import with_statement

import logging
from logging.config import fileConfig

from alembic import context

import open_webui.internal.db as open_webui_db
from open_tutorai.models.database import Base

config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# If your open_webui package is installed, use its shared engine.
engine = open_webui_db.engine

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = str(engine.url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
