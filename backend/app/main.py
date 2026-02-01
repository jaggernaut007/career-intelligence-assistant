"""
Career Intelligence Assistant - FastAPI Application.

Main entry point for the backend API.
"""

# Load environment variables FIRST, before any other imports
# This ensures HF_TOKEN is set before HuggingFace libraries check for it
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Literal, TypedDict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.guardrails.rate_limiter import slowapi_limiter as limiter

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Rate limiter imported from app.guardrails.rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting Career Intelligence Assistant API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"OpenAI Model: {settings.openai_model}")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down Career Intelligence Assistant API...")


# Create FastAPI app
app = FastAPI(
    title="Career Intelligence Assistant API",
    description="AI-powered career intelligence for resume analysis and job matching",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Add rate limiter to app state
app.state.limiter = limiter


# ============================================================================
# Middleware
# ============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = datetime.utcnow()
    response = await call_next(request)
    duration = (datetime.utcnow() - start_time).total_seconds() * 1000

    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.2f}ms"
    )
    return response


# Rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# Health Check
# ============================================================================

HEALTH_CHECK_TIMEOUT = 5.0  # seconds


class DependencyStatus(TypedDict):
    status: Literal["ok", "error"]
    latency_ms: float
    message: str | None


async def _check_neo4j() -> DependencyStatus:
    """Check Neo4j connectivity."""
    from app.services.neo4j_store import get_neo4j_store

    start = time.perf_counter()
    try:
        store = get_neo4j_store()
        if store.is_connected():
            latency = (time.perf_counter() - start) * 1000
            return {"status": "ok", "latency_ms": round(latency, 2), "message": None}

        # Not connected - try sync driver verification
        driver = store._driver or store._get_driver()
        driver.verify_connectivity()
        latency = (time.perf_counter() - start) * 1000
        return {"status": "ok", "latency_ms": round(latency, 2), "message": None}
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return {"status": "error", "latency_ms": round(latency, 2), "message": str(e)}


async def _check_openai() -> DependencyStatus:
    """Check OpenAI API connectivity."""
    from openai import AsyncOpenAI
    from app.config import get_settings

    start = time.perf_counter()
    try:
        settings = get_settings()
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        # Retrieve a single known model - faster than listing all
        await client.models.retrieve(settings.openai_model)
        latency = (time.perf_counter() - start) * 1000
        return {"status": "ok", "latency_ms": round(latency, 2), "message": None}
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return {"status": "error", "latency_ms": round(latency, 2), "message": str(e)}


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Verifies connectivity to critical dependencies concurrently with timeout.
    Returns appropriate HTTP status codes:
    - 200: All dependencies healthy
    - 503: One or more dependencies unavailable
    """
    # Run checks concurrently with timeout
    try:
        neo4j_result, openai_result = await asyncio.wait_for(
            asyncio.gather(
                _check_neo4j(),
                _check_openai(),
                return_exceptions=True,
            ),
            timeout=HEALTH_CHECK_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("Health check timed out")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "error": f"Health check timed out after {HEALTH_CHECK_TIMEOUT}s",
            },
        )

    # Handle exceptions from gather
    if isinstance(neo4j_result, Exception):
        neo4j_result = {"status": "error", "latency_ms": 0, "message": str(neo4j_result)}
    if isinstance(openai_result, Exception):
        openai_result = {"status": "error", "latency_ms": 0, "message": str(openai_result)}

    # Determine overall status
    all_ok = neo4j_result["status"] == "ok" and openai_result["status"] == "ok"

    # Log warnings for failures
    if neo4j_result["status"] == "error":
        logger.warning(f"Neo4j health check failed: {neo4j_result['message']}")
    if openai_result["status"] == "error":
        logger.warning(f"OpenAI health check failed: {openai_result['message']}")

    response_data = {
        "status": "healthy" if all_ok else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "dependencies": {
            "neo4j": neo4j_result,
            "openai": openai_result,
        },
    }

    if all_ok:
        return response_data
    return JSONResponse(status_code=503, content=response_data)


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.exception(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "details": str(exc) if not settings.is_production else None
        }
    )


# ============================================================================
# API Routes
# ============================================================================

# Import and include routers
from app.api.routes import router as api_router
from app.api.websocket import router as websocket_router

app.include_router(api_router)
app.include_router(websocket_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production
    )
