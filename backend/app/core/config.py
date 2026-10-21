"""
Application configuration and settings.
"""
import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RULES_DIR = BASE_DIR / "rules"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SCANS_DIR = DATA_DIR / "scans"
DB_PATH = DATA_DIR / "diffguard.db"

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SCANS_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseModel):
    """Application settings."""
    
    # Application
    app_name: str = "DiffGuard"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DIFFGUARD_DEBUG", "false").lower() == "true"
    enable_docs: bool = os.getenv("ENABLE_DOCS", "true").lower() == "true"
    
    # Security
    allowed_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # File upload limits
    max_upload_size_bytes: int = 100 * 1024 * 1024  # 100 MB
    max_file_count: int = 10000
    max_extracted_size_bytes: int = 500 * 1024 * 1024  # 500 MB
    max_compression_ratio: int = 100
    
    # AI Configuration
    ai_provider: str = os.getenv("AI_PROVIDER", "auto")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Scanner Configuration
    semgrep_binary: str = "semgrep"
    gitleaks_binary: str = "gitleaks"
    scanner_timeout_seconds: int = 120
    default_exclusions: list = [
        "node_modules", "venv", ".venv", "__pycache__",
        ".git", ".next", "dist", "build", ".pytest_cache"
    ]
    
    # Paths
    data_dir: Path = DATA_DIR
    upload_dir: Path = UPLOAD_DIR
    scans_dir: Path = SCANS_DIR
    db_path: Path = DB_PATH
    rules_dir: Path = RULES_DIR
    
    
settings = Settings()