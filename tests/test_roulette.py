import unittest
from unittest.mock import AsyncMock, patch

from backend.services.tmdb import resolve_roulette_title


class RouletteTmdbTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolves_by_imdb_id_before_title_search(self):
        async def fake_tmdb_get(path, params=None):
            if path == "/find/tt0816692":
                return {
                    "movie_results": [{"id": 157336, "title": "Interstellar"}],
                    "tv_results": [],
                }
            if path == "/movie/157336":
                return {
                    "id": 157336,
                    "title": "Интерстеллар",
                    "release_date": "2014-11-05",
                    "poster_path": "/poster.jpg",
                    "vote_average": 8.4,
                    "overview": "Космическая экспедиция.",
                    "genres": [{"id": 18, "name": "Драма"}],
                    "production_countries": [{"iso_3166_1": "US"}],
                    "original_language": "en",
                    "external_ids": {"imdb_id": "tt0816692"},
                }
            self.fail(f"Unexpected TMDB path: {path}")

        with patch("backend.services.tmdb.tmdb_get", new=AsyncMock(side_effect=fake_tmdb_get)) as mocked:
            result = await resolve_roulette_title(
                title="Совсем другое название",
                imdb_id="tt0816692",
                year=2014,
                preferred_media_type="movie",
            )

        self.assertEqual(result["tmdb_id"], 157336)
        self.assertEqual(result["imdb_id"], "tt0816692")
        self.assertFalse(result["is_anime"])
        self.assertFalse(any(call.args[0].startswith("/search/") for call in mocked.await_args_list))

    async def test_falls_back_to_title_and_year_when_imdb_has_no_match(self):
        async def fake_tmdb_get(path, params=None):
            if path == "/find/tt0000000":
                return {"movie_results": [], "tv_results": []}
            if path == "/search/movie":
                self.assertEqual(params["year"], 1999)
                return {
                    "results": [
                        {"id": 1, "title": "Не Матрица", "release_date": "1999-01-01", "popularity": 100},
                        {"id": 603, "title": "Матрица", "release_date": "1999-03-30", "popularity": 80},
                    ]
                }
            if path == "/movie/603":
                return {
                    "id": 603,
                    "title": "Матрица",
                    "release_date": "1999-03-30",
                    "vote_average": 8.2,
                    "overview": "Выбор между двумя таблетками.",
                    "genres": [{"id": 28, "name": "Боевик"}],
                    "production_countries": [{"iso_3166_1": "US"}],
                    "original_language": "en",
                    "external_ids": {"imdb_id": "tt0133093"},
                }
            self.fail(f"Unexpected TMDB path: {path}")

        with patch("backend.services.tmdb.tmdb_get", new=AsyncMock(side_effect=fake_tmdb_get)):
            result = await resolve_roulette_title(
                title="Матрица",
                imdb_id="tt0000000",
                year=1999,
                preferred_media_type="movie",
            )

        self.assertEqual(result["tmdb_id"], 603)
        self.assertEqual(result["year"], 1999)

    async def test_japanese_animation_is_marked_as_anime(self):
        async def fake_tmdb_get(path, params=None):
            if path == "/find/tt0245429":
                return {
                    "movie_results": [{"id": 129, "title": "Spirited Away"}],
                    "tv_results": [],
                }
            if path == "/movie/129":
                return {
                    "id": 129,
                    "title": "Унесённые призраками",
                    "release_date": "2001-07-20",
                    "vote_average": 8.5,
                    "genres": [{"id": 16, "name": "Мультфильм"}],
                    "production_countries": [{"iso_3166_1": "JP"}],
                    "original_language": "ja",
                    "external_ids": {"imdb_id": "tt0245429"},
                }
            self.fail(f"Unexpected TMDB path: {path}")

        with patch("backend.services.tmdb.tmdb_get", new=AsyncMock(side_effect=fake_tmdb_get)):
            result = await resolve_roulette_title("Унесённые призраками", "tt0245429", 2001, "movie")

        self.assertTrue(result["is_anime"])
        self.assertEqual(result["media_type"], "movie")


if __name__ == "__main__":
    unittest.main()
