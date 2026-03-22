import httpx
from fastapi import HTTPException
from config import KINOPOISK_API_KEY, KINOPOISK_URL

headers = {
    "X-API-KEY": KINOPOISK_API_KEY,
}


async def search_movies(query: str):
    params = {"keyword": query}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(KINOPOISK_URL, headers=headers, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Ошибка поиска")

    data = response.json()

    return data.get("films", [])