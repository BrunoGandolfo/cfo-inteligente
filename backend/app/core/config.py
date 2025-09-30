from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str
    database_test_url: str = ""
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Environment
    environment: str = "development"
    
    # API Keys (opcionales)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_ai_key: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
