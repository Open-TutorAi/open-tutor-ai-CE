"""
Database migrations for OpenTutorAI.
Replace: backend/open_tutorai/models/migrations.py
"""

import logging

from sqlalchemy import inspect, text

log = logging.getLogger(__name__)


def _add_missing_columns(engine, table_name, columns_to_add):
    try:
        inspector = inspect(engine)

        if table_name not in inspector.get_table_names():
            log.debug("Table %s does not exist yet, skipping migration", table_name)
            return

        columns = {col["name"] for col in inspector.get_columns(table_name)}

        for column_name, column_sql in columns_to_add.items():
            if column_name in columns:
                log.debug(
                    "%s column already exists in %s table", column_name, table_name
                )
                continue

            log.info("Adding %s column to %s table...", column_name, table_name)
            with engine.connect() as conn:
                conn.execute(
                    text(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
                    )
                )
                conn.commit()
            log.info(
                "Successfully added %s column to %s table", column_name, table_name
            )
    except Exception as e:
        log.error("Error migrating %s table: %s", table_name, str(e))
        raise


def migrate_course_columns(engine):
    _add_missing_columns(
        engine,
        "opentutorai_course",
        {
            "custom_category": "VARCHAR",
            "meta_data": "TEXT",
            "model_used": "VARCHAR",
            "chat_id": "VARCHAR",
        },
    )


def migrate_enrollment_table(engine):
    _add_missing_columns(
        engine,
        "opentutorai_course_enrollment",
        {
            "status": "VARCHAR DEFAULT 'active'",
            # ← NEW: store chat_id so student can resume their AI session
            "chat_id": "VARCHAR",
            "is_hidden": "BOOLEAN DEFAULT FALSE",
        },
    )


def migrate_progress_table(engine):
    """
    The progress table is created by Base.metadata.create_all().
    This migration handles any schema additions needed after the fact.
    """
    _add_missing_columns(
        engine,
        "opentutorai_course_progress",
        {
            "completed_at": "DATETIME",
            "updated_at": "DATETIME",
        },
    )


def run_migrations(engine):
    log.info("Running OpenTutorAI migrations...")
    migrate_course_columns(engine)
    migrate_enrollment_table(engine)
    migrate_progress_table(engine)
    log.info("All migrations completed")
