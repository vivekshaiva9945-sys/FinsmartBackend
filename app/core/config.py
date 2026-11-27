import os
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FinSmart API"
    app_version: str = "1.0.0"
    environment: str = "development"
    
    # Database connection URL (PostgreSQL with asyncpg driver)
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://finsmart_app:change_me_app@database:5432/finsmart_db"
    )
    
    # JWT & Cryptography
    jwt_secret: str = os.getenv("JWT_SECRET", "super_secret_finsmart_jwt_key_at_least_32_characters_long_2026")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    
    # CORS Origins for Frontend Integration
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment == "production":
            insecure_defaults = [
                "super_secret_finsmart_jwt_key_at_least_32_characters_long_2026",
                "secret",
                "changeme",
            ]
            if self.jwt_secret in insecure_defaults or len(self.jwt_secret) < 32:
                raise ValueError(
                    "CRITICAL SECURITY: In production environment, JWT_SECRET must be configured with "
                    "a secure random secret at least 32 characters long."
                )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

