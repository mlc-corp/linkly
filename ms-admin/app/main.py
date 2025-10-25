from fastapi import FastAPI
from app.routes import health, links
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MS Admin (FastAPI) - Linkly", version="1.0")


origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(links.router)
