import httpx
from fastapi import HTTPException
from config import KINOPOISK_API_KEY

headers = {
    "X-API-KEY": KINOPOISK_API_KEY,
}

async def get_movie_by_id(movie_id: int):
    url = f"https://kinopoiskapiunofficial.tech/api/v2.2/films/{movie_id}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Ошибка получения фильма")

    return response.json()