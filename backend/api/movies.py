from fastapi import APIRouter

from backend.services.tmdb import get_movie_by_id, get_popular, search_movies
from backend.models.movie import MovieFull, MovieShort

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
    normalized_query = query.casefold().strip()
    films = sorted(
        films,
        key=lambda film: (
            0 if (film.get("name") or "").casefold().strip() == normalized_query else 1,
            -float(film.get("popularity") or 0),
        ),
    )
    return [MovieShort(**film) for film in films]

@router.get('/movies/{movie_id}', response_model=MovieFull)
async def get_movie(movie_id: int):
    return await get_movie_by_media("movie", movie_id)


@router.get('/movies/{media_type}/{movie_id}', response_model=MovieFull)
async def get_movie_by_media(media_type: str, movie_id: int):
    movie = await get_movie_by_id(media_type, movie_id)
    return MovieFull(**movie)


@router.get('/novelties', response_model=list[MovieShort])
async def get_novelties():
    films = await get_popular()
    return [MovieShort(**film) for film in films]
