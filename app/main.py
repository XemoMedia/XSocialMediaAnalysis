"""
Main FastAPI application entry point.
Similar to Spring Boot's main application class.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import sentiment_routes
from app.services.sentiment_service import SentimentService
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI application (similar to @SpringBootApplication)
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Social Media Analysis API with Sentiment Analysis",
    docs_url="/swagger",
    redoc_url="/redoc"
)

# Configure CORS (if needed for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (similar to @RestController registration)
app.include_router(sentiment_routes.router)


@app.on_event("startup")
async def startup_event():
    """
    Initialize application on startup.
    This ensures:
    1. Database tables are created if they don't exist
    2. Sentiment analysis models are loaded
    """
    logger.info("Starting application initialization...")
    
    try:
        # Step 1: Check and create database tables
        logger.info("Checking database tables...")
        from app.database import check_and_create_tables
        check_and_create_tables()
        logger.info("Database tables verified/created")
        
        # Step 2: Initialize SentimentService to load ML models
        logger.info("Loading sentiment analysis models...")
        _ = SentimentService()
        logger.info("All sentiment analysis models loaded successfully")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during application startup: {e}", exc_info=True)
        raise


@app.get("/")
async def root():
    """
    Root endpoint for health check.
    
    Returns:
        Welcome message and API information
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running",
        "docs": "/swagger"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

