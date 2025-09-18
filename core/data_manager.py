from __future__ import annotations
import os
import logging
from typing import Optional, Dict, Any, List, Union
from pydantic import EmailStr
import pandas as pd

from .local_storage import LocalStorageManager, LocalStorageError, AuthenticationError, StorageError
from .models import UploadRecord, UserPreferences, UserSession

# Configure logging
logger = logging.getLogger(__name__)


class DataManagerError(Exception):
    """Base exception for DataManager operations"""
    pass


class BackendError(DataManagerError):
    """Exception for backend-related errors"""
    pass


class DataManager:
    """
    Local data manager for file-based storage operations
    
    Provides unified interface for data operations using local storage only.
    """
    
    def __init__(self):
        """
        Initialize DataManager with local storage only
        """
        # Configuration
        self.default_goal = float(os.getenv("DEFAULT_GOAL", "4.0"))
        
        # Initialize local storage
        storage_root = os.getenv("STORAGE_ROOT", "data")
        self.local = LocalStorageManager(base_path=storage_root)
        
        logger.info("DataManager initialized with local storage backend")

    # ---------- Authentication Methods ----------
    
    def authenticate_user(self, email: str, password: str) -> bool:
        """
        Authenticate user using local storage
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            return self.local.verify_user_credentials(email, password)
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {e}")

    def register_user(self, email: str, password: str) -> bool:
        """
        Register new user using local storage
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            True if registration successful
            
        Raises:
            AuthenticationError: If registration fails
        """
        try:
            return self.local.save_user_credentials(email, password)
        except Exception as e:
            raise AuthenticationError(f"Registration failed: {e}")

    def get_user_session(self, email: str) -> Optional[UserSession]:
        """
        Get user session data from local storage
        
        Args:
            email: User email address
            
        Returns:
            UserSession object or None if user doesn't exist
        """
        try:
            return self.local.get_user_session(email)
        except Exception:
            return None

    # ---------- Upload Management Methods ----------
    
    def save_upload(self, email: str, df: pd.DataFrame, original_filename: str) -> UploadRecord:
        """
        Save uploaded file to local storage
        
        Args:
            email: User email address
            df: DataFrame to save
            original_filename: Original name of uploaded file
            
        Returns:
            UploadRecord with upload metadata
            
        Raises:
            StorageError: If save operation fails
        """
        try:
            user_hash = self.local._get_user_hash(email)
            return self.local.save_file_upload(user_hash, df, original_filename)
        except Exception as e:
            raise StorageError(f"Save upload failed: {e}")

    def get_user_uploads(self, email: str) -> List[UploadRecord]:
        """
        Get all upload records for a user from local storage
        
        Args:
            email: User email address
            
        Returns:
            List of UploadRecord objects
        """
        try:
            user_hash = self.local._get_user_hash(email)
            return self.local.get_user_uploads(user_hash)
        except Exception:
            return []

    def load_upload_data(self, email: str, upload_id: str) -> Optional[pd.DataFrame]:
        """
        Load data from a specific upload from local storage
        
        Args:
            email: User email address
            upload_id: Upload ID from UploadRecord
            
        Returns:
            DataFrame with uploaded data or None if not found
        """
        try:
            user_hash = self.local._get_user_hash(email)
            return self.local.load_upload_data(user_hash, upload_id)
        except Exception:
            return None

    def get_latest_upload(self, email: str) -> Optional[UploadRecord]:
        """
        Get the most recent upload for a user
        
        Args:
            email: User email address
            
        Returns:
            Most recent UploadRecord or None if no uploads
        """
        uploads = self.get_user_uploads(email)
        return uploads[0] if uploads else None

    def delete_upload(self, email: str, upload_id: str) -> bool:
        """
        Delete a specific upload from local storage
        
        Args:
            email: User email address
            upload_id: Upload ID to delete
            
        Returns:
            True if successful, False if upload not found
        """
        try:
            user_hash = self.local._get_user_hash(email)
            return self.local.delete_upload(user_hash, upload_id)
        except Exception:
            return False

    # ---------- User Preferences Management ----------
    
    def get_user_preferences(self, email: str) -> Dict[str, Any]:
        """
        Get user preferences from local storage
        
        Args:
            email: User email address
            
        Returns:
            Dictionary of user preferences
        """
        try:
            user_hash = self.local._get_user_hash(email)
            return self.local.get_user_preferences(user_hash)
        except Exception:
            # Return default preferences if operation fails
            return {
                "goal": self.default_goal,
                "default_filters": {
                    "age_range": [18, 65],
                    "sex": "Todos",
                    "education": "Todos",
                    "public_servant": "Todos"
                },
                "ui_preferences": {
                    "theme": "default",
                    "chart_colors": ["#1f77b4", "#ff7f0e", "#2ca02c"]
                }
            }

    def save_user_preferences(self, email: str, preferences: Dict[str, Any]) -> bool:
        """
        Save user preferences to local storage
        
        Args:
            email: User email address
            preferences: Dictionary of user preferences
            
        Returns:
            True if successful
        """
        try:
            user_hash = self.local._get_user_hash(email)
            return self.local.save_user_preferences(user_hash, preferences)
        except Exception:
            return False

    # ---------- Backend Management ----------
    
    def get_backend_status(self) -> Dict[str, Any]:
        """
        Get status of local storage backend
        
        Returns:
            Dictionary with backend status information
        """
        return {
            "current_backend": "Local",
            "local_available": True,
            "storage_path": self.local.base_path
        }

    # ---------- Legacy Compatibility Methods ----------
    
    def demo_login(self, email: str) -> bool:
        """Legacy demo login method for backward compatibility"""
        try:
            # For demo purposes, create user if doesn't exist
            if not self.authenticate_user(email, "demo"):
                self.register_user(email, "demo")
            return True
        except:
            return False