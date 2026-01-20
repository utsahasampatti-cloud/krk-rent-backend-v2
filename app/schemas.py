from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from uuid import UUID


class Filters(BaseModel):
    city: str = Field(default="Kraków")
    districts: List[str] = Field(default_factory=list)
    price_max: Optional[int] = None
    rooms: Optional[int] = None


class SearchRequest(BaseModel):
    user_id: int
    filters: Filters
    limit: int = 10


class SearchResponse(BaseModel):
    job_id: str


class FeedItem(BaseModel):
    id: UUID
    source: str
    url: str
    title: str
    price_value: Optional[float] = None
    location: Optional[str] = None
    scraped_at: str


class FeedResponse(BaseModel):
    items: List[FeedItem]


class StateRequest(BaseModel):
    user_id: int
    listing_id: UUID
    state: Literal["liked", "skipped"]
