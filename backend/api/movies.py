import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.services.kinopoisk_id import search_movies
from backend.services.kinopoisk_card import get_movie_by_id
from backend.models.movie import MovieFull, MovieShort
from config import KINOPOISK_API_KEY

router = APIRouter()


def parse_year(value):
    try:
        return int(value) if value and value != "null" else None
    except (TypeError, ValueError):
        return None


def parse_float(value):
    try:
        return float(value) if value and value != "null" else 0
    except (TypeError, ValueError):
        return 0


@router.get('/search', response_model=list[MovieShort])
async def search(query:str):
    films = await search_movies(query)
    result = []

    for film in films:
        movie_id = film.get("filmId") or film.get("kinopoiskId")
        if not movie_id:
            continue

        result.append(MovieShort(
            id=movie_id,
            name=film.get("nameRu") or film.get("nameEn") or "No title",
            year=parse_year(film.get("year")),
            poster=film.get("posterUrlPreview"),
        ))

    return result

@router.get('/movies/{movie_id}', response_model=MovieFull)
async def get_movie(movie_id: int):
    film = await get_movie_by_id(movie_id)
    kinopoisk_id = film.get("kinopoiskId") or film.get("filmId") or movie_id
    name = film.get("nameRu") or film.get("nameOriginal") or film.get("nameEn")

    if not kinopoisk_id or not name:
        raise HTTPException(status_code=502, detail="Некорректный ответ Кинопоиска")

    return MovieFull(
        id=kinopoisk_id,
        name=name,
        original_name=film.get("nameOriginal"),
        year=parse_year(film.get("year")),
        poster=film.get("posterUrl"),
        rating=parse_float(film.get("ratingKinopoisk")),
        rating_imdb=parse_float(film.get("ratingImdb")),
        description=film.get("description") or film.get("shortDescription"),
        genres=[g["genre"] for g in film.get("genres", [])],
        countries=[c["country"] for c in film.get("countries", [])],
        film_length=film.get("filmLength"),
    )

@router.get('/proxy/poster')
async def proxy_poster(url:str):
    headers = {'X-API-KEY':KINOPOISK_API_KEY}
    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=headers)
    return Response(content=response.content, media_type='image/jpeg')


@router.get('/novelties', response_model=list[MovieShort])
async def get_novelties():
    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    url = "https://kinopoiskapiunofficial.tech/api/v2.2/films/top"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers, params={"type": "TOP_100_POPULAR_FILMS", "page": 1})

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Ошибка получения новинок")

    films = response.json().get("films", [])
    result = []
    for film in films:
        movie_id = film.get("filmId") or film.get("kinopoiskId")
        if not movie_id:
            continue

        result.append(MovieShort(
            id=movie_id,
            name=film.get("nameRu") or film.get("nameEn") or "No title",
            year=parse_year(film.get("year")),
            poster=film.get("posterUrlPreview"),
        ))
    return result
