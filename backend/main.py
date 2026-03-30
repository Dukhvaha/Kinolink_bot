from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.movies import router as movies_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies_router)
app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

#http://localhost:3000/index.html?id=5591410