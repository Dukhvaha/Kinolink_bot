from services.zona_parser import ZonaParser

parser = ZonaParser()

async def get_video_url(movie_title: str) -> str | None:
    return await parser.search_movie(movie_title)
