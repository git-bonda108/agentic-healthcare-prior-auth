"""Configuration management for the Prior Authorization system."""
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Config:
    """Application configuration."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Batch Processing
    DEFAULT_BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "5"))
    MAX_BATCH_SIZE: int = 20
    
    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./data/prior_auths.db")
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = [".pdf", ".docx", ".txt", ".doc"]
    
    # Processing
    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: int = 300
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Please set it in .env file")
        return True
