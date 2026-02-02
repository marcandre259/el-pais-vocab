from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routers import (
    vocabulary_router,
    articles_router,
    themes_router,
    audio_router,
    sync_router,
    tasks_router,
)

app = FastAPI(
    title="El País Vocabulary Builder API",
    description="REST API for extracting Spanish vocabulary from El País articles and managing themed vocabulary.",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vocabulary_router, prefix=settings.api_prefix)
app.include_router(articles_router, prefix=settings.api_prefix)
app.include_router(themes_router, prefix=settings.api_prefix)
app.include_router(audio_router, prefix=settings.api_prefix)
app.include_router(sync_router, prefix=settings.api_prefix)
app.include_router(tasks_router, prefix=settings.api_prefix)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "el-pais-vocab-api"}


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": "El País Vocabulary Builder API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
