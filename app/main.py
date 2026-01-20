from fastapi import FastAPI, HTTPException
import redis

from app.settings import settings
from app.schemas import SearchRequest, SearchResponse, FeedResponse, StateRequest
from app.utils import new_job_id, dumps
from app.db import health_check_db, fetch_feed, mark_seen, set_state


app = FastAPI(title="krk-rent-backend", version="1.0.0")


def get_redis() -> redis.Redis:
    if not settings.REDIS_URL:
        raise RuntimeError("REDIS_URL is missing")
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


@app.get("/health")
def health():
    # DB
    db_ok = False
    try:
        db_ok = health_check_db()
    except Exception:
        db_ok = False

    # Redis
    redis_ok = False
    try:
        r = get_redis()
        redis_ok = (r.ping() is True)
    except Exception:
        redis_ok = False

    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {"status": status, "db": db_ok, "redis": redis_ok}


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    if not settings.REDIS_URL:
        raise HTTPException(status_code=500, detail="REDIS_URL is missing")
    if not settings.DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL is missing")

    job_id = new_job_id()
    payload = {
        "job_id": job_id,
        "user_id": req.user_id,
        "filters": req.filters.model_dump(),
        "limit": req.limit,
    }

    r = get_redis()
    r.rpush(settings.REDIS_QUEUE_KEY, dumps(payload))
    return SearchResponse(job_id=job_id)


@app.get("/feed", response_model=FeedResponse)
def feed(user_id: int, limit: int = 10):
    rows = fetch_feed(user_id=user_id, limit=limit)

    # IMPORTANT: при видачі одразу seen
    items = []
    for row in rows:
        mark_seen(user_id=user_id, listing_id=row["id"])
        items.append(
            {
                "id": row["id"],
                "source": row["source"],
                "url": row["url"],
                "title": row["title"],
                "price_value": float(row["price_value"]) if row["price_value"] is not None else None,
                "location": row["location"],
                "scraped_at": row["scraped_at"].isoformat(),
            }
        )

    return FeedResponse(items=items)


@app.post("/state")
def state(req: StateRequest):
    # liked / skipped (seen ставиться автоматом у /feed)
    set_state(user_id=req.user_id, listing_id=req.listing_id, state=req.state)
    return {"ok": True}
