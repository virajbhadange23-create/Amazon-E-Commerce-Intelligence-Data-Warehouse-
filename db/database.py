"""
Database Access Layer for Amazon E-Commerce Data Warehouse
Supports both SQLAlchemy 2.0 ORM sessions and high-performance parameterized SQLite3 queries.
"""
import sqlite3
import logging
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import config
from db.models import Base

logger = logging.getLogger(__name__)

# SQLAlchemy 2.0 Engine & Session Factory
engine = create_engine(
    f"sqlite:///{config.DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """Yields or returns an active SQLAlchemy 2.0 session."""
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise


def get_db_connection() -> sqlite3.Connection:
    """Creates a new SQLite connection with foreign keys and dict row factory."""
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(force: bool = False) -> None:
    """Initializes the database using schema.sql and SQLAlchemy 2.0 metadata."""
    if force and config.DB_PATH.exists():
        try:
            config.DB_PATH.unlink()
            logger.info("Old database file removed for forced recreation.")
        except Exception as e:
            logger.warning(f"Could not remove old DB: {e}")

    # Create tables via SQL DDL
    with open(config.SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_db_connection() as conn:
        conn.executescript(schema_sql)
        conn.commit()

    # Sync SQLAlchemy 2.0 DeclarativeBase metadata
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully with Star Schema and SQLAlchemy 2.0.")


def query_db(query: str, args: tuple = (), one: bool = False) -> Union[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Executes a parameterized SELECT query and returns rows as dictionaries."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        rows = cur.fetchall()
        if one:
            return dict(rows[0]) if rows else None
        return [dict(r) for r in rows]
    finally:
        conn.close()


def execute_db(query: str, args: tuple = ()) -> int:
    """Executes an INSERT/UPDATE/DELETE query with parameters and returns the lastrowid."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def execute_many(query: str, args_list: List[tuple]) -> int:
    """Executes executemany with parameters and returns affected row count."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.executemany(query, args_list)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def get_table_counts() -> Dict[str, int]:
    """Returns the live row count for every table in the warehouse."""
    tables = [
        "dim_category",
        "dim_product",
        "dim_date",
        "fact_sales",
        "etl_log",
        "price_predictions",
        "product_clusters",
    ]
    counts = {}
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        for tbl in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {tbl}")
                counts[tbl] = cur.fetchone()[0]
            except Exception:
                counts[tbl] = 0
    finally:
        conn.close()
    return counts
