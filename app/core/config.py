from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_MIN: int = 60 * 24 * 30
    MEDIA_DIR: str = "./media"
    PUBLIC_MEDIA_BASE: str = "https://quetzartpi.gpolufesa.com/media"
    BANK_NAME: str 
    BANK_ACCOUNT: str 
    BANK_CLABE: str 
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_USE_TLS: bool = True
    class Config:
        env_file = ".env"

settings = Settings()
