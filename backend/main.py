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


@app.get("/apps", include_in_schema=False)
async def mini_apps_panel():
    return FileResponse(FRONTEND_DIR / "apps.html")


@app.get("/apps/movie-roulette", include_in_schema=False)
async def movie_roulette_app():
    return FileResponse(FRONTEND_DIR / "roulette.html")


@app.middleware("http")
async def disable_frontend_cache(request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.endswith((".html", ".js", ".css")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


app.mount('/', StaticFiles(directory=FRONTEND_DIR, html=True), name='frontend')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

#http://localhost:3000/index.html?id=5591410
