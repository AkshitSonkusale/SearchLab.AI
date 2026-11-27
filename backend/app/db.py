import logging
import time
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_pool: pool.ThreadedConnectionPool = None

def get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        logger.info("Initializing PostgreSQL Connection Pool...")
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=settings.database_url,
            cursor_factory=RealDictCursor,
            connect_timeout=15
        )
    return _pool

@contextmanager
def get_db():
    """
    Context manager providing a pooled database connection.
    On error, rolls back and closes the connection if broken.
    """
    conn = None
    p = get_pool()
    try:
        conn = p.getconn()
        yield conn
        conn.commit()
        p.putconn(conn)
    except Exception as e:
        if conn:
            try:
                if not conn.closed:
                    conn.rollback()
                p.putconn(conn)
            except Exception:
                try:
                    p.putconn(conn, close=True)
                except Exception:
                    pass
        logger.error(f"Database error: {e}")
        raise e

def execute_query(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
    """
    Executes a SQL query using the connection pool with retry resilience.
    """
    for attempt in range(3):
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params or ())
                    if fetch_one:
                        return cur.fetchone()
                    if fetch_all:
                        return cur.fetchall()
                    return None
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.warning(f"Database transient error on attempt {attempt + 1}: {e}. Retrying in 1s...")
            time.sleep(1)
            if attempt == 2:
                raise e
        except Exception as e:
            raise e
