"""
Database migrations for OpenTutorAI.
Handles schema updates for existing tables.
"""

import logging

from sqlalchemy import inspect, text

log = logging.getLogger(__name__)


def _add_missing_columns(engine, table_name, columns_to_add):
    try:
        inspector = inspect(engine)

        # Table may not exist yet (first run) — skip safely
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
    """
    Backfill course columns that may be missing from older SQLite databases.
    """
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
    """
    Ensures the enrollment table has all required columns.
    The table itself is created by Base.metadata.create_all().
    """
    _add_missing_columns(
        engine,
        "opentutorai_course_enrollment",
        {
            "status": "VARCHAR DEFAULT 'active'",
        },
    )


def run_migrations(engine):
    """
    Run all pending migrations.
    Call this during application startup after creating tables.
    """
    log.info("Running OpenTutorAI migrations...")
    migrate_course_columns(engine)
    migrate_enrollment_table(engine)
    log.info("All migrations completed")