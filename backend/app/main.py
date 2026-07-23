"""Main FastAPI application entry point."""

import hmac
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from redis.exceptions import RedisError

from app.config import settings
from app.core.logging import configure_logging
from app.database import engine
from app.redis import get_redis, close_redis
from app.api.v1.router import api_router

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Handles:
    - Database connection initialization
    - Redis connection initialization
    - Cleanup on shutdown
    """
    # Startup
    try:
        # Initialize Redis connection
        redis = await get_redis()
        await redis.ping()
        logger.info("Redis connection established")
    except RedisError:
        logger.warning("Redis connection failed at startup", exc_info=True)

    # Database engine is already initialized in database.py
    logger.info("Database engine initialized")

    yield

    # Shutdown
    await close_redis()
    await engine.dispose()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", settings.AUTH_CSRF_HEADER_NAME],
    expose_headers=["X-Total-Count"],
)


CSRF_EXEMPT_PATHS = {"/api/v1/auth/login"}
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@app.middleware("http")
async def csrf_cookie_protection(request: Request, call_next):
    """Validate double-submit CSRF token for unsafe API requests."""
    if (
        request.method in UNSAFE_METHODS
        and request.url.path.startswith("/api/v1")
        and request.url.path not in CSRF_EXEMPT_PATHS
    ):
        csrf_cookie = request.cookies.get(settings.AUTH_CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(settings.AUTH_CSRF_HEADER_NAME)
        if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid CSRF token"},
            )

    return await call_next(request)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.

    Returns:
        dict: Welcome message and API information
    """
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# Mount API routers
app.include_router(api_router, prefix="/api/v1")

# Serve uploaded images as static files
upload_dir = settings.UPLOAD_DIR
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")
