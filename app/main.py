from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.connection import Base, engine
from app.db import models  # noqa: F401


app = FastAPI(
    title="AlphaSync API",
    version="1.0.0",
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def on_startup():
    # cria as tabelas automaticamente
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}