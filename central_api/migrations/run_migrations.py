#!/usr/bin/env python3
"""Database migration runner for Central API.

Applies SQL migrations to the SQLite database in order.
Tracks which migrations have been applied to avoid re-running.

Usage:
    python -m migrations.run_migrations [--db-path PATH]

Or from central_api directory:
    python migrations/run_migrations.py
"""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Default database path (relative to central_api directory)
DEFAULT_DB_PATH = Path("central_api_config.db")

# Migrations directory (relative to this script)
MIGRATIONS_DIR = Path(__file__).parent


def get_applied_migrations(conn: sqlite3.Connection) -> set[str]:
    """Get set of migration names that have been applied."""
    # Create migrations tracking table if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            name TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    cursor = conn.execute("SELECT name FROM _migrations")
    return {row[0] for row in cursor.fetchall()}


def apply_migration(conn: sqlite3.Connection, migration_path: Path) -> bool:
    """Apply a single migration file.

    Args:
        conn: Database connection
        migration_path: Path to .sql migration file

    Returns:
        True if migration was applied, False if it failed
    """
    migration_name = migration_path.name
    logger.info(f"Applying migration: {migration_name}")

    try:
        sql = migration_path.read_text()

        # Execute each statement separately (SQLite doesn't support multiple
        # statements in executescript when they might fail)
        for raw_stmt in sql.split(";"):
            stmt = raw_stmt.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError as e:
                    # Ignore "duplicate column" errors for idempotent migrations
                    if "duplicate column name" in str(e).lower():
                        logger.debug(f"Column already exists, skipping: {e}")
                    else:
                        raise

        # Record that migration was applied
        conn.execute(
            "INSERT OR REPLACE INTO _migrations (name) VALUES (?)",
            (migration_name,),
        )
        conn.commit()

    except Exception:
        logger.exception(f"✗ Migration failed: {migration_name}")
        conn.rollback()
        return False

    else:
        logger.info(f"✓ Migration applied: {migration_name}")
        return True


def run_migrations(db_path: Path) -> int:
    """Run all pending migrations.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Number of migrations applied (0 if all up to date, -1 on error)
    """
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        logger.info("Run the application first to create the database.")
        return -1

    # Find all migration files
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        logger.info("No migration files found.")
        return 0

    logger.info(f"Found {len(migration_files)} migration file(s)")

    conn = sqlite3.connect(str(db_path))
    try:
        applied = get_applied_migrations(conn)
        logger.info(f"Already applied: {len(applied)} migration(s)")

        pending = [f for f in migration_files if f.name not in applied]
        if not pending:
            logger.info("Database is up to date.")
            return 0

        logger.info(f"Pending migrations: {len(pending)}")
        applied_count = 0

        for migration_path in pending:
            if apply_migration(conn, migration_path):
                applied_count += 1
            else:
                logger.error("Migration failed, stopping.")
                return -1

        logger.info(f"Applied {applied_count} migration(s) successfully.")
        return applied_count

    finally:
        conn.close()


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run database migrations for Central API")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    args = parser.parse_args()

    result = run_migrations(args.db_path)
    return 0 if result >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
