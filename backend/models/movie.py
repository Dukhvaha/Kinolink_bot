from pydantic import BaseModel
from typing import List, Optional


class MovieShort(BaseModel):
    id: int
    media_type: str = "movie"
    name: str
    year: Optional[int]
    poster: Optional[str]


class MovieFull(BaseModel):
    id: int
    media_type: str = "movie"
    name: str
    original_name: Optional[str]
    year: Optional[int]
    poster: Optional[str]
    rating: Optional[float]
    rating_imdb: Optional[float]
    description: Optional[str]
    genres: List[str]
    countries: List[str]
    film_length: Optional[int]
    imdb_id: Optional[str] = None
    player_type: str = "imdb"
    player_id: Optional[str] = None
