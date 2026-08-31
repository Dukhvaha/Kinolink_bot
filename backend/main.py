from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.movies import router as movies_router
from backend.api.roulette import router as roulette_router


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "https://catalytical-cuticolor-della.ngrok-free.dev",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(movies_router)
app.include_router(roulette_router)


@app.get("/apps/movie-roulette", include_in_schema=False)
async def movie_roulette_app():
    return FileResponse(FRONTEND_DIR / "roulette.html")


@app.middleware("http")
async def set_frontend_cache_headers(request, call_next):
    response = await call_next(request)
    path = request.url.path.lower()

    if path == "/" or path.endswith(".html") or path.startswith("/apps/"):
        response.headers["Cache-Control"] = "no-cache"
    elif path.endswith((".woff2", ".woff")):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif path.endswith((".js", ".css", ".png", ".jpg", ".jpeg", ".webp", ".svg")):
        response.headers["Cache-Control"] = "public, max-age=86400"

    return response


app.mount('/', StaticFiles(directory=FRONTEND_DIR, html=True), name='frontend')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

#http://localhost:3000/index.html?id=5591410
