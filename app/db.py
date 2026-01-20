from typing import Any, Dict, List, Optional
from uuid import UUID

from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

from app.settings import settings


_pool: Optional[ConnectionPool] = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        if not settings.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is missing")
        _pool = ConnectionPool(conninfo=settings.DATABASE_URL, min_size=1, max_size=5, kwargs={"row_factory": dict_row})
    return _pool


def health_check_db() -> bool:
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 as ok;")
            row = cur.fetchone()
            return bool(row and row["ok"] == 1)


def upsert_listing(listing: Dict[str, Any]) -> UUID:
    """
    listing keys: url, title, price_value, location, scraped_at (optional)
    Returns listing.id
    """
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO listings (source, url, title, price_value, location, scraped_at)
                VALUES ('olx', %(url)s, %(title)s, %(price_value)s, %(location)s, COALESCE(%(scraped_at)s, now()))
                ON CONFLICT (url) DO UPDATE SET
                  title = EXCLUDED.title,
                  price_value = EXCLUDED.price_value,
                  location = EXCLUDED.location,
                  scraped_at = EXCLUDED.scraped_at
                RETURNING id;
                """,
                listing,
            )
            row = cur.fetchone()
            conn.commit()
            return row["id"]


def mark_seen(user_id: int, listing_id: UUID) -> None:
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_listing_state (user_id, listing_id, state, updated_at)
                VALUES (%s, %s, 'seen', now())
                ON CONFLICT (user_id, listing_id) DO NOTHING;
                """,
                (user_id, listing_id),
            )
            conn.commit()


def set_state(user_id: int, listing_id: UUID, state: str) -> None:
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_listing_state (user_id, listing_id, state, updated_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT (user_id, listing_id) DO UPDATE SET
                  state = EXCLUDED.state,
                  updated_at = now();
                """,
                (user_id, listing_id, state),
            )
            conn.commit()


def fetch_feed(user_id: int, limit: int) -> List[Dict[str, Any]]:
    """
    Return newest listings not yet seen/liked/skipped by user.
    """
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT l.*
                FROM listings l
                LEFT JOIN user_listing_state s
                  ON s.listing_id = l.id AND s.user_id = %s
                WHERE s.listing_id IS NULL
                ORDER BY l.scraped_at DESC
                LIMIT %s;
                """,
                (user_id, limit),
            )
            return cur.fetchall()
