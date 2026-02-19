from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_MIN: int = 60 * 24 * 30
    MEDIA_DIR: str = "./media"
    PUBLIC_MEDIA_BASE: str = "http://localhost:8000/media"
    BANK_NAME: str 
    BANK_ACCOUNT: str 
    BANK_CLABE: str 
    class Config:
        env_file = ".env"

settings = Settings()
