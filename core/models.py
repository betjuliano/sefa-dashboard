from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, field_validator


@dataclass
class UserSession:
    """User session data with validation"""
    email: str
    user_hash: str
    logged_in: bool = False
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate email format and user_hash"""
        if not self.email or '@' not in self.email:
            raise ValueError("Invalid email format")
        if not self.user_hash:
            raise ValueError("User hash cannot be empty")


@dataclass
class UploadRecord:
    """Upload record with metadata and validation"""
    id: str
    filename: str
    original_filename: str
    upload_date: datetime
    n_rows: int
    n_cols: int
    file_path: str
    user_hash: str
    
    def __post_init__(self):
        """Validate upload record data"""
        if not self.id:
            raise ValueError("Upload ID cannot be empty")
        if not self.filename:
            raise ValueError("Filename cannot be empty")
        if not self.original_filename:
            raise ValueError("Original filename cannot be empty")
        if self.n_rows < 0:
            raise ValueError("Number of rows cannot be negative")
        if self.n_cols < 0:
            raise ValueError("Number of columns cannot be negative")
        if not self.file_path:
            raise ValueError("File path cannot be empty")
        if not self.user_hash:
            raise ValueError("User hash cannot be empty")


class UserPreferences(BaseModel):
    """User preferences with validation (keeping Pydantic for complex validation)"""
    user_email: str
    goal_global: float = Field(4.0, ge=1.0, le=5.0)
    goal_by_dimension: Dict[str, float] = Field(default_factory=dict)
    saved_filters: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("goal_by_dimension")
    @classmethod
    def validate_goals(cls, v: Dict[str, float]) -> Dict[str, float]:
        for k, val in v.items():
            if not (1.0 <= float(val) <= 5.0):
                raise ValueError(f"Meta inválida para dimensão {k}: {val}")
        return v