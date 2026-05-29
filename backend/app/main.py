import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.crawler.scheduler import setup_scheduler, scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="Brandshow API",
    version="1.0.0",
    description="Brand ranking data from chinapp.com",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import categories, crawler, brands  # noqa: E402

app.include_router(categories.router, prefix="/api/v1")
app.include_router(crawler.router, prefix="/api/v1")
app.include_router(brands.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
