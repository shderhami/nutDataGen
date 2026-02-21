"""
PostgreSQL connection management.

Provides a single reusable connection with context manager support,
automatic reconnection, and proper resource cleanup.
"""
from contextlib import contextmanager
from typing import Any, Generator, Optional

import psycopg2
import psycopg2.extensions
import psycopg2.extras

from config import (
    DATABASE_HOST,
    DATABASE_NAME,
    DATABASE_PASSWORD,
    DATABASE_PORT,
    DATABASE_USER,
)


class DatabaseConnection:
    """Manages a single PostgreSQL connection with reconnection logic."""

    def __init__(
        self,
        host: str = DATABASE_HOST,
        port: int = DATABASE_PORT,
        dbname: str = DATABASE_NAME,
        user: str = DATABASE_USER,
        password: str = DATABASE_PASSWORD,
    ) -> None:
        self._host = host
        self._port = port
        self._dbname = dbname
        self._user = user
        self._password = password
        self._connection: Optional[psycopg2.extensions.connection] = None

    def _connect(self) -> psycopg2.extensions.connection:
        """Establish a new database connection."""
        return psycopg2.connect(
            host=self._host,
            port=self._port,
            dbname=self._dbname,
            user=self._user,
            password=self._password,
        )

    def get_connection(self) -> psycopg2.extensions.connection:
        """Get active connection, reconnecting if needed."""
        if self._connection is None or self._connection.closed:
            self._connection = self._connect()
        return self._connection

    @contextmanager
    def cursor(
        self, cursor_factory: Any = None
    ) -> Generator[psycopg2.extras.RealDictCursor, None, None]:
        """Context manager yielding a cursor; commits on success, rolls back on error."""
        conn = self.get_connection()
        factory = cursor_factory or psycopg2.extras.RealDictCursor
        cur = conn.cursor(cursor_factory=factory)
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    def close(self) -> None:
        """Close the database connection."""
        if self._connection is not None and not self._connection.closed:
            self._connection.close()
            self._connection = None


# Module-level singleton
_db: Optional[DatabaseConnection] = None


def get_db() -> DatabaseConnection:
    """Get the module-level DatabaseConnection singleton."""
    global _db
    if _db is None:
        _db = DatabaseConnection()
    return _db


def close_db() -> None:
    """Close the module-level connection."""
    global _db
    if _db is not None:
        _db.close()
        _db = None
