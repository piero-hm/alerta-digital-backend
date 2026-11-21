"""Pool de conexiones a PostgreSQL (Supabase, pooler en modo transacción)."""

from collections.abc import Iterator

from psycopg import Connection
from psycopg_pool import ConnectionPool

from core.config import get_settings

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Crea el pool de forma perezosa (máximo 5 conexiones)."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=5,
            open=False,
            timeout=10,
            kwargs={"prepare_threshold": None},
            check=ConnectionPool.check_connection,
        )
        _pool.open()
    return _pool


def close_pool() -> None:
    """Cierra el pool al apagar la aplicación."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def get_db() -> Iterator[Connection]:
    """Dependencia de FastAPI que entrega una conexión del pool."""
    with get_pool().connection() as conn:
        yield conn
