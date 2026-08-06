import logging
from pathlib import Path

from app.database.session import execute_query

logger = logging.getLogger(__name__)


async def init_snowflake_tables() -> None:
    """Run CREATE TABLE IF NOT EXISTS for all application tables using database/schema.sql."""
    schema_path = Path(__file__).resolve().parent.parent.parent / "database" / "schema.sql"
    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}, skipping table initialization.")
        return

    try:
        sql_text = schema_path.read_text(encoding="utf-8")
        statements = [stmt.strip() for stmt in sql_text.split(";") if stmt.strip()]

        for stmt in statements:
            lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
            clean_stmt = "\n".join(lines).strip()
            if clean_stmt:
                await execute_query(clean_stmt)
        logger.info("Snowflake tables initialized successfully from schema.sql.")
    except Exception as e:
        logger.warning(f"Skipping Snowflake table initialization (connection unconfigured or failed): {e}")


