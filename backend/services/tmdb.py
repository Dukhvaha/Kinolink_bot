import httpx
from fastapi import HTTPException

from config import TMDB_API_BASE, TMDB_READ_TOKEN

IMAGE_BASE = "https://image.tmdb.org/t/p"


def tmdb_headers() -> dict:
    if not TMDB_READ_TOKEN:
        raise HTTPException(status_code=500, detail="TMDB token is not configured")

    return {
        "Authorization": f"Bearer {TMDB_READ_TOKEN}",
        "accept": "application/json",
    }


def poster_url(path: str | None, size: str = "w500") -> str | None:
    if not path:
        return None
    return f"{IMAGE_BASE}/{size}{path}"


def parse_year(date_value: str | None) -> int | None:
    if not date_value:
        return None
    try:
        return int(date_value[:4])
    except (TypeError, ValueError):
        return None


def normalize_short(item: dict) -> dict | None:
    media_type = item.get("media_type")
    if media_type not in {"movie", "tv"}:
        return None

    name = item.get("title") or item.get("name") or item.get("original_title") or item.get("original_name")
    if not name:
        return None

    return {
        "id": item.get("id"),
        "media_type": media_type,
        "name": name,
        "year": parse_year(item.get("release_date") or item.get("first_air_date")),
        "poster": poster_url(item.get("poster_path"), "w342"),
        "popularity": float(item.get("popularity") or 0),
    }


def rank_result(item: dict, query: str) -> tuple:
    name = (item.get("name") or "").casefold().strip()
    normalized_query = query.casefold().strip()

    if name == normalized_query:
        match_rank = 0
    elif name.startswith(normalized_query):
        match_rank = 1
    elif normalized_query in name:
        match_rank = 2
    else:
        match_rank = 3

    return (match_rank, -float(item.get("popularity") or 0), item.get("year") or 9999)


async def tmdb_get(path: str, params: dict | None = None) -> dict:
    url = f"{TMDB_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=tmdb_headers(), params=params)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="TMDB temporarily unavailable") from exc

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Movie not found")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="TMDB returned an error")

    return response.json()


async def search_movies(query: str) -> list[dict]:
    data = await tmdb_get(
        "/search/multi",
        {
            "query": query,
            "language": "ru-RU",
            "include_adult": "false",
            "page": 1,
        },
    )

    results = []
    seen = set()
    for item in data.get("results", []):
        movie = normalize_short(item)
        if not movie or not movie.get("id"):
            continue

        key = (movie["media_type"], movie["id"])
        if key in seen:
            continue

        seen.add(key)
        results.append(movie)

    return sorted(results, key=lambda item: rank_result(item, query))


async def get_movie_by_id(media_type: str, tmdb_id: int) -> dict:
    if media_type not in {"movie", "tv"}:
        raise HTTPException(status_code=404, detail="Unsupported media type")

    details = await tmdb_get(
        f"/{media_type}/{tmdb_id}",
        {
            "language": "ru-RU",
            "append_to_response": "external_ids",
        },
    )

    name = details.get("title") or details.get("name") or details.get("original_title") or details.get("original_name")
    if not name:
        raise HTTPException(status_code=502, detail="Invalid TMDB response")

    countries = [
        country.get("name")
        for country in details.get("production_countries", [])
        if country.get("name")
    ]
    if not countries:
        countries = details.get("origin_country", []) or []

    runtime = details.get("runtime")
    if runtime is None and details.get("episode_run_time"):
        runtime = details["episode_run_time"][0]

    return {
        "id": details.get("id"),
        "media_type": media_type,
        "name": name,
        "original_name": details.get("original_title") or details.get("original_name"),
        "year": parse_year(details.get("release_date") or details.get("first_air_date")),
        "poster": poster_url(details.get("poster_path"), "w500"),
        "rating": round(float(details.get("vote_average") or 0), 1),
        "rating_imdb": 0,
        "description": details.get("overview"),
        "genres": [genre["name"] for genre in details.get("genres", []) if genre.get("name")],
        "countries": countries,
        "film_length": runtime,
        "imdb_id": (details.get("external_ids") or {}).get("imdb_id"),
        "player_type": "imdb",
        "player_id": (details.get("external_ids") or {}).get("imdb_id"),
    }


async def get_popular() -> list[dict]:
    movies = await tmdb_get("/movie/popular", {"language": "ru-RU", "page": 1})
    tv = await tmdb_get("/tv/popular", {"language": "ru-RU", "page": 1})

    items = []
    for item in movies.get("results", [])[:10]:
        item["media_type"] = "movie"
        normalized = normalize_short(item)
        if normalized:
            items.append(normalized)

    for item in tv.get("results", [])[:10]:
        item["media_type"] = "tv"
        normalized = normalize_short(item)
        if normalized:
            items.append(normalized)

    return items[:12]
