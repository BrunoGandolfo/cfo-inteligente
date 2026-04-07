"""Configuración centralizada del sistema vía pydantic-settings y variables de entorno."""

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

class Settings(BaseSettings):
    # Database
    database_url: str
    test_database_url: str = Field(default="postgresql://cfo_user:cfo_pass@localhost/cfo_test", alias="TEST_DATABASE_URL")
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 días
    
    # Environment
    environment: str = "development"
    
    # API Key - Usar Field(alias=...) para soportar MAYÚSCULAS en .env
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    capsolver_api_key: str = Field(default="", alias="CAPSOLVER_API_KEY")
    
    # SQL Engine: "haiku" (pipeline completo) | "claude" (bypass directo a Claude)
    sql_engine: str = Field(default="claude", alias="SQL_ENGINE")

    # CORS - Lee desde .env usando pydantic-settings
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:5174",
        alias="CORS_ORIGINS"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,  # Permite minúsculas y MAYÚSCULAS
        populate_by_name=True,  # Permite usar tanto el nombre como el alias
        extra="ignore"  # Ignora campos extra en variables de entorno
    )

settings = Settings()
