from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.movies import router as movies_router

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


@app.middleware("http")
async def disable_frontend_cache(request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.endswith((".html", ".js", ".css")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

#http://localhost:3000/index.html?id=5591410
