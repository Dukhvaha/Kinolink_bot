import asyncio
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.tmdb import resolve_roulette_title


router = APIRouter(prefix="/api/roulette", tags=["movie-roulette"])


class RouletteResolveItem(BaseModel):
    imdb_id: str | None = Field(default=None, max_length=24)
    title: str = Field(min_length=1, max_length=300)
    year: int | None = Field(default=None, ge=1870, le=2200)
    media_type: Literal["movie", "tv"] | None = None


class RouletteResolveBatch(BaseModel):
    items: list[RouletteResolveItem] = Field(min_length=1, max_length=100)


async def resolve_item(item: RouletteResolveItem, semaphore: asyncio.Semaphore) -> dict:
    error = None
    try:
        async with semaphore:
            resolved = await resolve_roulette_title(
                title=item.title,
                imdb_id=item.imdb_id,
                year=item.year,
                preferred_media_type=item.media_type,
            )
    except HTTPException as exc:
        resolved = None
        error = exc.detail
    return {
        "source": item.model_dump(),
        "match": resolved,
        "error": error,
    }


@router.post("/resolve")
async def resolve_roulette_items(payload: RouletteResolveBatch):
    semaphore = asyncio.Semaphore(5)
    results = await asyncio.gather(
        *(resolve_item(item, semaphore) for item in payload.items)
    )
    return {"items": results}
