"""
Kerala Cleanup Platform - Main Application
FastAPI backend for volunteer cleanup drive management.

Security Features:
- JWT authentication on all protected endpoints
- Role-based access control (RBAC)
- NoSQL injection prevention
- Rate limiting
- CORS protection
- Structured logging with request IDs

Privacy Features:
- Age-band instead of DOB collection
- Minimal data exposure to organizers
- No CSV exports
- In-app messaging proxy
"""

import logging
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.database import MongoDB
from app.routers import auth, users, drives, registrations, organizer


# Configure structured logging
logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Kerala Cleanup Platform API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    try:
        # Connect to MongoDB
        await MongoDB.connect()
        logger.info("Database connection established")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down Kerala Cleanup Platform API")
        await MongoDB.disconnect()
        logger.info("Database connection closed")


# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Privacy-first volunteer cleanup platform for Kerala",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,  # Disable docs in prod
    redoc_url="/redoc" if not settings.is_production else None
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)


# Request ID middleware for structured logging
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """
    Add unique request ID to each request for tracing.
    Request ID is added to response headers and logs.
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add request_id to logging context
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    logger.info(f"{request.method} {request.url.path}")
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    # Restore original factory
    logging.setLogRecordFactory(old_factory)
    
    return response


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all responses.
    OWASP recommended headers for API security.
    """
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Remove server header
    if "server" in response.headers:
        del response.headers["server"]
    
    return response


# Global exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors.
    Returns user-friendly error messages.
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    logger.warning(f"Validation error: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    Logs error and returns generic message to user.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Don't expose internal errors in production
    detail = str(exc) if not settings.is_production else "Internal server error"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": detail,
            "request_id": request_id
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancers.
    
    **Returns:**
    - 200: Service healthy
    - 503: Service unhealthy (database connection failed)
    
    **Response:**
    - status: "healthy" or "unhealthy"
    - environment: Current environment (dev/prod)
    - database: Database connection status
    """
    try:
        # Check database connection
        db = MongoDB.get_database()
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_status = "disconnected"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "environment": settings.ENVIRONMENT,
                "database": db_status
            }
        )
    
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": db_status
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Kerala Cleanup Platform API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if not settings.is_production else "disabled"
    }


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(drives.router, prefix=settings.API_V1_PREFIX)
app.include_router(registrations.router, prefix=settings.API_V1_PREFIX)
app.include_router(organizer.router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,
        log_level="info"
    )