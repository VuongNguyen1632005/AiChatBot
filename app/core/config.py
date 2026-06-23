from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Exam Generator Backend"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/my_database"
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
