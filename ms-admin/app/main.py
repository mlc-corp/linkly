from fastapi import FastAPI
from app.routes import health, links

app = FastAPI(title="MS Admin (FastAPI) - Linkly", version="1.0")

app.include_router(health.router)
app.include_router(links.router)
