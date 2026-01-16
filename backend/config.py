"""
Configuration settings for the ML Solution Advisor
Centralized settings for API, LLM, file handling, and data analysis
"""

import os  # Operating system utilities for path handling
from typing import Optional  # Type hints for optional values


class Config:
    """
    Application configuration class
    Contains all settings used by the API
    """
    
    # LLM Model Settings (for Ollama or similar)
    LLM_MODEL: str = "llama3.2"  # Model name to use for AI analysis
    LLM_TEMPERATURE: float = 0.7  # Temperature controls randomness (0-1, higher = more creative)
    LLM_BASE_URL: str = "http://localhost:11434"  # URL to Ollama server
    
    # API Server Settings
    API_HOST: str = "0.0.0.0"  # Listen on all network interfaces
    API_PORT: int = 8000  # Port for the web server
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]  # Allowed frontend origins
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # Maximum upload size: 50MB
    ALLOWED_EXTENSIONS: set = {".csv", ".xlsx", ".json"}  # File types users can upload
    UPLOAD_DIR: str = "uploads"  # Directory to store uploaded files
    
    # Agent Settings (for ML workflows)
    MAX_RETRIES: int = 3  # How many times to retry failed operations
    TIMEOUT_SECONDS: int = 300  # Maximum time to wait for analysis (5 minutes)
    
    # Data Analysis Settings
    MAX_ROWS_TO_ANALYZE: int = 10000  # Analyze only first 10,000 rows if file is larger
    SAMPLE_SIZE: int = 100  # Sample size for statistical analysis
    
    @classmethod
    def get_upload_path(cls, filename: str) -> str:
        """
        Get full path for uploaded file
        Creates upload directory if it doesn't exist
        Args: filename (str) - name of the file
        Returns: Full path to the file in uploads directory
        """
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)  # Create directory if missing
        return os.path.join(cls.UPLOAD_DIR, filename)  # Return full path


# Create global config instance used throughout the application
config = Config()
