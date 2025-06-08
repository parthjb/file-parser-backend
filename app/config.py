from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    DATABASE_URL: str
    OPENAI_API_KEY: str
    GENAI_API_KEY: str
    SUPABASE_KEY: str
    SUPABASE_URL: str
    
    UPLOAD_DIR: str = "uploads"
    CLOUD_UPLOAD_DIR: str = "cloud_uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  
    ALLOWED_FILE_TYPES: list = ["pdf", "docx", "csv", "tsv", "xlsx", "xls", "doc"]

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    API_PREFIX: str = "/file-parser/api"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()