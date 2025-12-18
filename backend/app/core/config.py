from pydantic_settings import BaseSettings
from pydantic import Field

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
    
    # API Keys - Usar Field(alias=...) para soportar MAYÚSCULAS en .env
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    google_ai_key: str = Field(default="", alias="GOOGLE_AI_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False  # Permite minúsculas y MAYÚSCULAS
        populate_by_name = True  # Permite usar tanto el nombre como el alias

settings = Settings()
