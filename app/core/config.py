from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Exam Generator Backend"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/my_database"
    REDIS_URL: str = "redis://localhost:6379/0"
    GEMINI_API_KEY: str = ""
    
    # Auth & Security
    SECRET_KEY: str = "supersecretkeychangeinproduction"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
