import httpx
from aiogram.types import BufferedInputFile

from config import BACKEND_URL


async def search_movies(query: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/search",
            params={"query": query}
        )

    if response.status_code != 200:
        return []

    return response.json()


async def get_movie(movie_id: int) -> dict | None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BACKEND_URL}/movies/{movie_id}")

    if response.status_code != 200:
        return None

    return response.json()


async def get_novelties() -> list:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BACKEND_URL}/novelties")

    if response.status_code != 200:
        return []

    return response.json()


async def get_poster_photo(poster_url: str | None) -> BufferedInputFile | None:
    if not poster_url:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(poster_url)
    except Exception:
        return None

    content_type = response.headers.get("content-type", "")
    if response.status_code != 200 or not content_type.startswith("image/"):
        return None

    return BufferedInputFile(response.content, filename="poster.jpg")


def build_movie_caption(movie: dict, title_prefix: str | None = None) -> str:
    name = movie.get("name") or "Без названия"
    year = movie.get("year") or ""
    rating = movie.get("rating", 0)
    description = movie.get("description") or "Описание отсутствует."
    short_description = description[:500]
    suffix = "..." if len(description) > 500 else ""

    title = f"🎬 {name} ({year})"
    if title_prefix:
        title = f"{title_prefix}\n\n{title}"

    return (
        f"{title}\n"
        f"⭐️ {rating}\n\n"
        f"{short_description}{suffix}"
    )
