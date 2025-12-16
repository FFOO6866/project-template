"""
FastAPI Application - Dynamic Job Pricing Engine

Main application entry point with all middleware and route configuration.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from job_pricing.core.config import get_settings

logger = logging.getLogger(__name__)

# Initialize Sentry if configured
settings = get_settings()
if settings.sentry_enabled:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
        traces_sample_rate=1.0 if settings.is_development else 0.1,
        profiles_sample_rate=1.0 if settings.is_development else 0.1,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],
        # Send PII data
        send_default_pii=False,
        # Release tracking
        release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
    )

    logger.info(f"Sentry initialized for environment: {settings.ENVIRONMENT}")

# Import routers
from job_pricing.api.v1 import job_pricing, ai, salary_recommendation, external, applicants, internal_hris, auth, documents

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "Application starting",
        extra={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "database_configured": bool(settings.DATABASE_URL),
            "redis_configured": bool(settings.REDIS_URL),
        }
    )

    # Validate critical settings
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set in environment")
        raise RuntimeError("OPENAI_API_KEY is not set! Check your .env file.")

    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL is not set in environment")
        raise RuntimeError("DATABASE_URL is not set! Check your .env file.")

    logger.info("Application startup complete")
    yield

    # Shutdown
    logger.info("Application shutting down", extra={"app_name": settings.APP_NAME})


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Dynamic Job Pricing Engine",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan,
)

# Register rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --------------------------------------------------------------------------
# Middleware
# --------------------------------------------------------------------------

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Per-user rate limiting (only if enabled)
if settings.RATE_LIMIT_ENABLED:
    from job_pricing.middleware import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
    logger.info("Per-user rate limiting enabled")

# Prometheus monitoring (only if enabled)
if settings.PROMETHEUS_ENABLED:
    from job_pricing.middleware import PrometheusMiddleware, metrics_endpoint
    app.add_middleware(PrometheusMiddleware)
    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], tags=["Monitoring"])
    logger.info("Prometheus monitoring enabled")


# --------------------------------------------------------------------------
# Health Check Endpoints
# --------------------------------------------------------------------------


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Application health status
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint.

    Verifies that all dependencies are available and reachable.

    Returns:
        dict: Readiness status with detailed checks
    """
    import redis
    from sqlalchemy import text
    from job_pricing.core.database import engine

    checks = {
        "openai_api_key": False,
        "database": False,
        "redis": False,
    }

    # Check OpenAI API key is configured
    checks["openai_api_key"] = bool(settings.OPENAI_API_KEY)

    # Check database connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            checks["database"] = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        checks["database"] = False

    # Check Redis connectivity
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.ping()
        checks["redis"] = True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        checks["redis"] = False

    all_ready = all(checks.values())

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.

    Returns:
        dict: Welcome message
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_BASE_URL}/docs" if settings.is_development else None,
    }


# --------------------------------------------------------------------------
# API Routers
# --------------------------------------------------------------------------

app.include_router(
    job_pricing.router,
    prefix="/api/v1/job-pricing",
    tags=["Job Pricing"]
)

app.include_router(
    ai.router,
    prefix="/api/v1/ai",
    tags=["AI Generation"]
)

app.include_router(
    salary_recommendation.router,
    prefix="/api/v1/salary",
    tags=["Salary Recommendation"]
)

app.include_router(
    external.router,
    prefix="/api/v1/external",
    tags=["External Data Integration"]
)

app.include_router(
    applicants.router,
    prefix="/api/v1",
    tags=["External Applicants"]
)

app.include_router(
    internal_hris.router,
    prefix="/api/v1",
    tags=["Internal HRIS"]
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    documents.router,
    prefix="/api/v1/documents",
    tags=["Document Extraction"]
)

# Future routers (Phase 5+)
# app.include_router(
#     mercer.router,
#     prefix="/api/v1/mercer",
#     tags=["Mercer Integration"]
# )
#
# app.include_router(
#     skills.router,
#     prefix="/api/v1/skills",
#     tags=["Skills"]
# )
#
# app.include_router(
#     users.router,
#     prefix="/api/v1/users",
#     tags=["Users"]
# )


# --------------------------------------------------------------------------
# Exception Handlers
# --------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """
    HTTPException handler with consistent error format.

    Returns errors in the same format as the global exception handler
    for frontend consistency.
    """
    # Determine error code from status
    error_codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        413: "REQUEST_ENTITY_TOO_LARGE",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE"
    }

    error_code = error_codes.get(exc.status_code, "HTTP_ERROR")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": str(exc.detail),
                "details": None
            }
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler.

    Catches all unhandled exceptions and returns proper error response.
    """
    # Log the error with structured logging
    logger.error(
        "Unhandled exception",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal error occurred",
                "details": str(exc) if settings.DEBUG else None,
            },
        },
    )


if __name__ == "__main__":
    import uvicorn

    # Run with: python -m src.job_pricing.api.main
    uvicorn.run(
        "src.job_pricing.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.AUTO_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
