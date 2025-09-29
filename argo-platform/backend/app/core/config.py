from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application
    app_name: str = "ARGO Oceanographic Data Platform"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://argo_user:argo_password@localhost:5432/argo_platform")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Chroma Vector DB
    chroma_url: str = os.getenv("CHROMA_URL", "http://localhost:8000")
    
    # API Keys
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    mistral_api_key: Optional[str] = os.getenv("MISTRAL_API_KEY")
    huggingface_api_key: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
    
    # JWT Configuration
    secret_key: str = os.getenv("SECRET_KEY", "your_secret_key_change_this_in_production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    backend_cors_origins: List[str] = ["http://localhost:8501", "http://localhost:3000"]
    
    # Firebase
    firebase_project_id: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
    firebase_private_key_id: Optional[str] = os.getenv("FIREBASE_PRIVATE_KEY_ID")
    firebase_private_key: Optional[str] = os.getenv("FIREBASE_PRIVATE_KEY")
    firebase_client_email: Optional[str] = os.getenv("FIREBASE_CLIENT_EMAIL")
    firebase_client_id: Optional[str] = os.getenv("FIREBASE_CLIENT_ID")
    firebase_client_x509_cert_url: Optional[str] = os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
    
    # Email Configuration for Alerts
    email_host: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    email_port: int = int(os.getenv("EMAIL_PORT", "587"))
    email_username: Optional[str] = os.getenv("EMAIL_USERNAME")
    email_password: Optional[str] = os.getenv("EMAIL_PASSWORD")
    alert_from_email: str = os.getenv("ALERT_FROM_EMAIL", "alerts@argo-platform.com")
    
    class Config:
        env_file = ".env"

settings = Settings()