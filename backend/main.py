from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import sys
from contextlib import asynccontextmanager

from config import settings
from database import init_db
from api.routes import router as api_router
from news_aggregator import news_aggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting TrendPulse API...")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Initialize news sources
        news_aggregator.initialize_sources()
        logger.info("News sources initialized")
        
        # Initial news fetch (optional)
        if settings.DEBUG:
            logger.info("Performing initial news fetch...")
            try:
                count = news_aggregator.fetch_and_process_news()
                logger.info(f"Initial fetch completed: {count} articles processed")
            except Exception as e:
                logger.warning(f"Initial news fetch failed: {e}")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down TrendPulse API...")

# Create FastAPI application
app = FastAPI(
    title="TrendPulse API",
    description="API for tracking news topic trends across time and geography",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.CORS_ORIGINS,  # Allow all origins in debug mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure this properly for production
    )

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TrendPulse API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running"
    }

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "api_version": "v1",
        "endpoints": {
            "topics": "/api/v1/topics",
            "trends": "/api/v1/trends/{topic}",
            "countries": "/api/v1/countries/{country}/topics",
            "live": "/api/v1/live",
            "predictions": "/api/v1/predictions",
            "articles": "/api/v1/articles/search",
            "recent": "/api/v1/articles/recent",
            "statistics": "/api/v1/statistics",
            "health": "/api/v1/health"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Not Found",
        "message": "The requested resource was not found",
        "status_code": 404
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    if settings.DEBUG:
        import traceback
        return {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "status_code": 500,
            "debug_info": {
                "exception": str(exc),
                "traceback": traceback.format_exc()
            }
        }
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "status_code": 500
    } 