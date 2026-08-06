"""Database initialization CLI script for Snowflake schema setup and optional seeding.

Usage::
    python -m database.init_db [--seed]
"""

import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path if needed
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config.settings import settings
from app.config.logging_config import setup_logging
from app.utils.logger import get_logger

setup_logging()
logger = get_logger("init_db")


def run_sql_script(conn, file_path: Path) -> None:
    """Read a SQL file, split by semicolon, and execute non-empty statements."""
    if not file_path.exists():
        logger.error(f"SQL file not found at: {file_path}")
        return

    logger.info(f"Reading SQL script: {file_path.name}")
    sql_text = file_path.read_text(encoding="utf-8")

    # Simple statement splitter on ';'
    statements = [stmt.strip() for stmt in sql_text.split(";") if stmt.strip()]

    cur = conn.cursor()
    try:
        for idx, stmt in enumerate(statements, 1):
            # Skip pure comment blocks
            lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
            clean_stmt = "\n".join(lines).strip()
            if not clean_stmt:
                continue

            logger.info(f"Executing statement {idx}/{len(statements)} from {file_path.name}")
            cur.execute(clean_stmt)
        conn.commit()
        logger.info(f"Successfully executed all statements in {file_path.name}")
    finally:
        cur.close()


def main():
    parser = argparse.ArgumentParser(description="Initialize Snowflake database schema and optional seed data.")
    parser.add_argument("--seed", action="store_true", help="Execute seed.sql after schema initialization")
    args = parser.parse_args()

    db_dir = Path(__file__).resolve().parent
    schema_file = db_dir / "schema.sql"
    seed_file = db_dir / "seed.sql"

    logger.info("Initializing Snowflake database...")
    try:
        from app.database.session import get_snowflake_connection
        conn = get_snowflake_connection()
    except Exception as e:
        logger.error(f"Failed to connect to Snowflake: {e}")
        logger.info("Please verify your SNOWFLAKE_* environment variables in .env")
        sys.exit(1)

    try:
        run_sql_script(conn, schema_file)
        if args.seed:
            run_sql_script(conn, seed_file)
        logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
