# app/db.py
import logging
from typing import Generator
from psycopg2 import pool, OperationalError
import psycopg2.extras

from .config import settings

logger = logging.getLogger(__name__)

_pg_pool: pool.SimpleConnectionPool | None = None


def init_db_pool():
    global _pg_pool
    if _pg_pool is None:
        try:
            _pg_pool = pool.SimpleConnectionPool(
                minconn=int(settings.DB_MINCONN),
                maxconn=int(settings.DB_MAXCONN),
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
            )
            logger.info("Postgres connection pool created.")
        except OperationalError as e:
            logger.exception("Failed to create DB pool: %s", e)
            raise


def close_db_pool():
    global _pg_pool
    if _pg_pool:
        try:
            _pg_pool.closeall()
            logger.info("Postgres pool closed.")
        except Exception:
            logger.exception("Error closing DB pool")


def get_conn():
    """Get a connection from the pool."""
    if _pg_pool is None:
        init_db_pool()
    conn = _pg_pool.getconn()
    # use dict cursor by default
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def put_conn(conn):
    if _pg_pool and conn:
        _pg_pool.putconn(conn)


def ensure_schema():
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id SERIAL PRIMARY KEY,
                device_id TEXT NOT NULL,
                accel_x DOUBLE PRECISION,
                accel_y DOUBLE PRECISION,
                accel_z DOUBLE PRECISION,
                gyro_x DOUBLE PRECISION,
                gyro_y DOUBLE PRECISION,
                gyro_z DOUBLE PRECISION,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                speed DOUBLE PRECISION,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_device_time ON sensor_data (device_id, timestamp);")
        conn.commit()
        cur.close()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            put_conn(conn)
