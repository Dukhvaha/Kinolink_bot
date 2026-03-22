from pydantic import BaseModel
from typing import List, Optional


class MovieShort(BaseModel):
    id: int
    name: str
    year: Optional[int]
    poster: Optional[str]


class MovieFull(BaseModel):
    id: int
    name: str
    original_name: Optional[str]
    year: Optional[int]
    poster: Optional[str]
    rating: float
    description: Optional[str]
    genres: List[str]
    countries: List[str]
    film_length: Optional[int]