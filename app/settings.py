from pydantic import BaseModel
import os


class Settings(BaseModel):
    # Required in Railway (set them)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # Worker behavior
    WORKER_REQUEST_DELAY_SECONDS: float = float(os.getenv("WORKER_REQUEST_DELAY_SECONDS", "1.5"))
    WORKER_MAX_PAGES: int = int(os.getenv("WORKER_MAX_PAGES", "2"))

    # Scraper
    OLX_BASE_URL: str = os.getenv("OLX_BASE_URL", "https://www.olx.pl")
    OLX_USER_AGENT: str = os.getenv(
        "OLX_USER_AGENT",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )

    # Queue
    REDIS_QUEUE_KEY: str = os.getenv("REDIS_QUEUE_KEY", "queue:search_jobs")


settings = Settings()
