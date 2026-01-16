"""
FastAPI Backend Server - Minimal ML Analysis API
Serves REST API for ML problem analysis and code generation
"""

# Import required libraries
import os  # Operating system utilities for file path handling
from fastapi import FastAPI  # FastAPI web framework
from fastapi.middleware.cors import CORSMiddleware  # Cross-origin request support
from fastapi.staticfiles import StaticFiles  # Static file serving for HTML/CSS/JS
from api.routes import router  # Import all API endpoints from routes module
from config import config  # Import configuration settings
import uvicorn  # ASGI server for running the application

# Compute absolute path to static files directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get directory containing this file
STATIC_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")  # Built React app

# Create FastAPI application instance
app = FastAPI(
    title="Smart ML Solution Advisor API",  # Title shown in API documentation
    description="AI-powered ML problem analysis and code generation",  # API description
    version="1.0.0"  # API version number
)

# Configure CORS (Cross-Origin Resource Sharing) to allow frontend API calls
app.add_middleware(
    CORSMiddleware,  # Add CORS middleware for cross-origin requests
    allow_origins=config.CORS_ORIGINS,  # Allow specified origins from config
    allow_credentials=True,  # Allow credentials like cookies and auth tokens
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, DELETE, etc)
    allow_headers=["*"],  # Allow all request headers
)

# Include all API routes from routes module
app.include_router(router)  # Register all endpoints defined in api/routes.py

# Mount built React app as static files
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    print(f"Warning: React dist directory not found at {STATIC_DIR}")


@app.get("/")
async def root():
    """
    Health check endpoint
    Returns API status and list of available endpoints
    """
    return {
        "message": "Smart ML Solution Advisor API",  # Friendly greeting
        "version": "1.0.0",  # Current API version
        "status": "running",  # Server is operational
        "docs": "/docs"  # Link to interactive Swagger documentation
    }


# Entry point when script is run directly
if __name__ == "__main__":
    # Minimal, professional startup message
    print("Starting Smart ML Solution Advisor API at http://localhost:8000 (docs: /docs)")

    # Start the Uvicorn ASGI server
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False
    )
