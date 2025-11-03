"""FastAPI main application for Financial P2P API."""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging
import time

from .config import settings
from .api import auth, transfers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="P2P Financial Transfer API with Supabase Authentication",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Middleware
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Completed {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Duration: {process_time:.3f}s"
    )
    
    return response


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    errors = exc.errors()
    logger.warning(f"Validation error for {request.url}: {errors}")
    
    # Convert errors to JSON-serializable format
    serializable_errors = []
    for error in errors:
        error_dict = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        # Only include input if it's JSON serializable
        if "input" in error:
            try:
                import json
                json.dumps(error["input"])
                error_dict["input"] = error["input"]
            except (TypeError, ValueError):
                error_dict["input"] = str(error["input"])
        
        serializable_errors.append(error_dict)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": serializable_errors,
            "error_code": "validation_error",
            "message": "Invalid request data"
        }
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    errors = exc.errors()
    logger.warning(f"Pydantic validation error for {request.url}: {errors}")
    
    # Convert errors to JSON-serializable format
    serializable_errors = []
    for error in errors:
        error_dict = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        serializable_errors.append(error_dict)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": serializable_errors,
            "error_code": "validation_error",
            "message": "Invalid data"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled error for {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "internal_error",
            "message": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# ============================================================================
# Routes
# ============================================================================

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(transfers.router, prefix="/api", tags=["Transfers"])


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/", tags=["Health"])
def root():
    """Root endpoint with API information."""
    return {
        "message": "Financial P2P API",
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "auth": "/api/auth",
            "transfers": "/api/transfers"
        }
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check endpoint."""
    try:
        from .database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error(f"Database health check failed: {str(e)}")
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": settings.app_version,
        "timestamp": time.time()
    }


# ============================================================================
# Startup & Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    from .database import Base, engine
    
    logger.info("="*70)
    logger.info(f" {settings.app_name} v{settings.app_version}")
    logger.info("="*70)
    logger.info(f" Server: {settings.host}:{settings.port}")
    logger.info(f" Debug Mode: {settings.debug}")
    
    # Show database info (hide password)
    db_url_safe = settings.database_url.split('@')[0] if '@' in settings.database_url else settings.database_url.split('://')[0]
    logger.info(f" Database: {db_url_safe}...")
    
    logger.info(f" Docs: http://{settings.host}:{settings.port}/docs")
    
    # Check Supabase configuration
    if settings.is_configured:
        logger.info(" Auth Mode: Supabase (Production) ✓")
    else:
        logger.info(" Auth Mode: Local Development (No Supabase needed) ✓")
        logger.info(" Using local JWT authentication with SQLite")
    
    logger.info("="*70)
    
    # Create database tables
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified ✓")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"{settings.app_name} shutting down...")

