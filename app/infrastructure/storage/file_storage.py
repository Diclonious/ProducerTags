from pathlib import Path
from datetime import datetime
from app.infrastructure.utils.time_utils import get_current_time
from fastapi import UploadFile
from typing import Optional


class FileStorageService:
    """Service for handling file uploads and storage"""

    def __init__(self, upload_dir: Path):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(exist_ok=True)

    def save_uploaded_file(self, file: UploadFile, prefix: str = "", user_id: Optional[int] = None) -> str:
        """Save uploaded file and return filename"""
        timestamp = get_current_time().strftime("%Y%m%d%H%M%S")
        safe_name = file.filename.replace(" ", "_")

        if user_id:
            filename = f"{prefix}_user{user_id}_{timestamp}_{safe_name}"
        else:
            filename = f"{prefix}_{timestamp}_{safe_name}"

        return filename

    def get_file_path(self, filename: str) -> Path:
        """Get full path for a filename"""
        return self.upload_dir / filename

    def file_exists(self, filename: str) -> bool:
        """Check if file exists"""
        return (self.upload_dir / filename).exists()

