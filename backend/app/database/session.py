"""Snowflake connection layer replacing SQLAlchemy."""

import asyncio
from typing import Any, Dict, List, Optional

import snowflake.connector
from snowflake.connector import DictCursor

from app.config.settings import settings

_connection_params: Dict[str, str] = {}


def _get_connection_params() -> Dict[str, str]:
    global _connection_params
    if not _connection_params:
        _connection_params = {
            "account": settings.SNOWFLAKE_ACCOUNT,
            "user": settings.SNOWFLAKE_USER,
            "password": settings.SNOWFLAKE_PASSWORD,
            "warehouse": settings.SNOWFLAKE_WAREHOUSE,
            "database": settings.SNOWFLAKE_DATABASE,
            "schema": settings.SNOWFLAKE_SCHEMA,
            "role": settings.SNOWFLAKE_ROLE,
        }
    return _connection_params


def get_snowflake_connection() -> snowflake.connector.SnowflakeConnection:
    """Create and return a new Snowflake connection."""
    return snowflake.connector.connect(**_get_connection_params())


def _execute_query_sync(sql: str, params: Optional[tuple] = None) -> Optional[List[Dict[str, Any]]]:
    """Execute a query synchronously and return results if any."""
    conn = get_snowflake_connection()
    try:
        cur = conn.cursor(DictCursor)
        try:
            cur.execute(sql, params)
            if cur.description:
                return cur.fetchall()
            return None
        finally:
            cur.close()
    finally:
        conn.close()


def _fetch_one_sync(sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
    """Fetch a single row synchronously."""
    conn = get_snowflake_connection()
    try:
        cur = conn.cursor(DictCursor)
        try:
            cur.execute(sql, params)
            return cur.fetchone()
        finally:
            cur.close()
    finally:
        conn.close()


def _fetch_all_sync(sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Fetch all rows synchronously."""
    conn = get_snowflake_connection()
    try:
        cur = conn.cursor(DictCursor)
        try:
            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            cur.close()
    finally:
        conn.close()


async def execute_query(sql: str, params: Optional[tuple] = None) -> Optional[List[Dict[str, Any]]]:
    """Execute a query asynchronously (runs in thread pool)."""
    return await asyncio.to_thread(_execute_query_sync, sql, params)


async def fetch_one(sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
    """Fetch a single row asynchronously."""
    return await asyncio.to_thread(_fetch_one_sync, sql, params)


async def fetch_all(sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Fetch all rows asynchronously."""
    return await asyncio.to_thread(_fetch_all_sync, sql, params)
