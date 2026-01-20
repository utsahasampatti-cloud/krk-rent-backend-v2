import time
from typing import Any, Dict

import redis

from app.settings import settings
from app.utils import loads
from app.query_builder import build_olx_url
from app.olx_scraper import scrape_listings
from app.db import upsert_listing


def get_redis() -> redis.Redis:
    if not settings.REDIS_URL:
        raise RuntimeError("REDIS_URL is missing")
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def handle_job(job: Dict[str, Any]) -> None:
    filters = job["filters"]
    # filters already dict compatible with Pydantic model shape
    from app.schemas import Filters  # local import щоб не тягнути при старті

    olx_url = build_olx_url(Filters(**filters))

    items = scrape_listings(olx_url, max_pages=settings.WORKER_MAX_PAGES)

    for it in items:
        upsert_listing(it)


def main() -> None:
    r = get_redis()
    q = settings.REDIS_QUEUE_KEY

    print(f"[worker] started. queue={q} delay={settings.WORKER_REQUEST_DELAY_SECONDS}s max_pages={settings.WORKER_MAX_PAGES}")

    while True:
        # BLPOP: блокуємось, не спалюємо CPU
        res = r.blpop(q, timeout=30)
        if not res:
            continue

        _, payload = res
        try:
            job = loads(payload)
            handle_job(job)
        except Exception as e:
            print(f"[worker] job failed: {e}")
        finally:
            # rate limit (1 запит на 1–2 сек на воркер)
            time.sleep(settings.WORKER_REQUEST_DELAY_SECONDS)


if __name__ == "__main__":
    main()
