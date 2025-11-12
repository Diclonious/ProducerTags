from pydantic import BaseModel
import os
from pathlib import Path


class Settings(BaseModel):
    """Application settings and configuration"""
    
    # App Info
    app_name: str = "TaggedByBelle"
    app_version: str = "2.0.0"
    debug: bool = True
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    
    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    static_dir: Path = base_dir / "static"
    templates_dir: Path = base_dir / "templates"
    uploads_dir: Path = base_dir / "uploads"
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    # File Upload
    max_upload_size: int = 10 * 1024 * 1024  # 10 MB
    allowed_extensions: list = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".txt", ".zip", ".rar", ".wav", ".mp3"]
    
    # Email (for future use)
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    
    # Feature Flags
    enable_analytics: bool = True
    enable_reviews: bool = True
    enable_notifications: bool = False
    
    # UI Settings
    items_per_page: int = 20
    session_timeout: int = 24 * 60 * 60  # 24 hours in seconds
    
    # Business Logic
    auto_complete_hours: int = 72  # Auto-complete delivered orders after 72 hours
    default_currency: str = "EUR"
    default_currency_symbol: str = "€"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


# Export commonly used paths
BASE_DIR = settings.base_dir
STATIC_DIR = settings.static_dir
TEMPLATES_DIR = settings.templates_dir
UPLOADS_DIR = settings.uploads_dir
