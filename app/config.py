from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    
    DATABASE_URL: str = "postgresql://postgres:parth@localhost:5432/file_to_db_mapper"
    
    OPENAI_API_KEY: str = "api key"
    GENAI_API_KEY: str = "api key"
    
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  
    ALLOWED_FILE_TYPES: list = ["pdf", "docx", "csv"]
    ALLOWED_MIME_TYPES: list = [
    "application/pdf",                              
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  
    "text/csv"                                      
    ]
    
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    API_PREFIX: str = "/file-parser/api"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()