"""Legal Metrology Compliance System - FastAPI Application Entrypoint."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup/shutdown tasks."""
    # Startup: ensure upload directories exist
    upload_dirs = [
        settings.upload_dir,
        os.path.join(settings.upload_dir, "regulations"),
        os.path.join(settings.upload_dir, "reports"),
    ]
    for d in upload_dirs:
        os.makedirs(d, exist_ok=True)

    yield

    # Shutdown tasks (if any)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-assisted Legal Metrology (Packaged Commodities) Rules, 2011 "
        "compliance inspection system. Built for Smart India Hackathon 2026."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
uploads_absolute = os.path.abspath(settings.upload_dir)
os.makedirs(uploads_absolute, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_absolute), name="uploads")

# Include API router
app.include_router(router)


# Global Exception Handlers
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to return clean JSON errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "error": str(exc) if settings.debug else "Internal Server Error",
        },
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with system metadata."""
    return {
        "system": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/health",
        "description": "Evidence-grounded Legal Metrology compliance inspection platform",
    }
