from __future__ import annotations
import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

import pandas as pd
import bcrypt

from .models import UploadRecord, UserPreferences, UserSession
from .utils import (
    get_user_hash, 
    ensure_directory_structure, 
    get_user_directory,
    generate_upload_filename,
    generate_upload_id,
    get_file_path,
    validate_file_path
)


class LocalStorageError(Exception):
    """Base exception for local storage operations"""
    pass


class AuthenticationError(LocalStorageError):
    """Exception for authentication-related errors"""
    pass


class StorageError(LocalStorageError):
    """Exception for file storage operations"""
    pass


class FileCorruptionError(StorageError):
    """Exception for corrupted file scenarios"""
    pass


class LocalStorageManager:
    """
    Local storage manager with directory auto-creation and secure user management
    """
    
    def __init__(self, base_path: str = "data"):
        """
        Initialize LocalStorageManager with automatic directory creation
        
        Args:
            base_path: Base path for data storage
        """
        self.base_path = base_path
        self.users_file = os.path.join(self.base_path, "users", "users.json")
        
        # Initialize directory structure
        self._initialize_storage()

    def _initialize_storage(self) -> None:
        """Initialize storage directory structure and default files"""
        try:
            # Create base directory structure
            ensure_directory_structure(self.base_path)
            
            # Initialize users.json if it doesn't exist
            if not os.path.exists(self.users_file):
                self._write_json(self.users_file, {"users": {}})
                
        except Exception as e:
            raise StorageError(f"Failed to initialize storage: {e}")

    def _get_user_hash(self, email: str) -> str:
        """
        Get secure hash for user email
        
        Args:
            email: User email address
            
        Returns:
            SHA256 hash of normalized email
            
        Raises:
            ValueError: If email is invalid
        """
        return get_user_hash(email)

    def _ensure_user_directory(self, user_hash: str) -> str:
        """
        Ensure user directory exists and return path
        
        Args:
            user_hash: User hash from _get_user_hash()
            
        Returns:
            Path to user directory
        """
        return get_user_directory(self.base_path, user_hash)

    def _read_json(self, path: str, default: Any = None) -> Any:
        """
        Safely read JSON file with error handling
        
        Args:
            path: Path to JSON file
            default: Default value if file doesn't exist
            
        Returns:
            Parsed JSON data or default value
            
        Raises:
            FileCorruptionError: If file exists but cannot be parsed
        """
        if not os.path.exists(path):
            return default
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise FileCorruptionError(f"Corrupted JSON file {path}: {e}")
        except Exception as e:
            raise StorageError(f"Failed to read JSON {path}: {e}")

    def _write_json(self, path: str, data: Any) -> None:
        """
        Safely write JSON file with atomic operation
        
        Args:
            path: Path to JSON file
            data: Data to write
            
        Raises:
            StorageError: If write operation fails
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Use temporary file for atomic write
        tmp_path = path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # Atomic replace
            os.replace(tmp_path, path)
            
        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
            raise StorageError(f"Failed to write JSON {path}: {e}")

    def save_user_credentials(self, email: str, password: str) -> bool:
        """
        Save user credentials with bcrypt password hashing
        
        Args:
            email: User email address
            password: Plain text password
            
        Returns:
            True if successful
            
        Raises:
            AuthenticationError: If email is invalid
            StorageError: If save operation fails
        """
        if not email or not email.strip():
            raise AuthenticationError("Email cannot be empty")
        
        if not password:
            raise AuthenticationError("Password cannot be empty")
        
        try:
            # Get user hash and ensure directory exists
            user_hash = self._get_user_hash(email)
            self._ensure_user_directory(user_hash)
            
            # Hash password with bcrypt
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            # Load existing users data
            users_data = self._read_json(self.users_file, {"users": {}})
            
            # Add or update user
            users_data["users"][user_hash] = {
                "email": email.strip().lower(),
                "password_hash": password_hash.decode('utf-8'),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": datetime.now(timezone.utc).isoformat()
            }
            
            # Save updated data
            self._write_json(self.users_file, users_data)
            
            return True
            
        except (AuthenticationError, StorageError):
            raise
        except Exception as e:
            raise StorageError(f"Failed to save user credentials: {e}")

    def verify_user_credentials(self, email: str, password: str) -> bool:
        """
        Verify user credentials against stored bcrypt hash
        
        Args:
            email: User email address
            password: Plain text password
            
        Returns:
            True if credentials are valid
            
        Raises:
            AuthenticationError: If email is invalid
            StorageError: If verification fails due to storage issues
        """
        if not email or not email.strip():
            raise AuthenticationError("Email cannot be empty")
        
        if not password:
            raise AuthenticationError("Password cannot be empty")
        
        try:
            # Get user hash
            user_hash = self._get_user_hash(email)
            
            # Load users data
            users_data = self._read_json(self.users_file, {"users": {}})
            
            # Check if user exists
            if user_hash not in users_data["users"]:
                return False
            
            user_data = users_data["users"][user_hash]
            stored_hash = user_data["password_hash"].encode('utf-8')
            
            # Verify password
            is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash)
            
            # Update last login if valid
            if is_valid:
                user_data["last_login"] = datetime.now(timezone.utc).isoformat()
                self._write_json(self.users_file, users_data)
            
            return is_valid
            
        except (AuthenticationError, StorageError):
            raise
        except Exception as e:
            raise StorageError(f"Failed to verify user credentials: {e}")

    def get_user_session(self, email: str) -> Optional[UserSession]:
        """
        Get user session data
        
        Args:
            email: User email address
            
        Returns:
            UserSession object or None if user doesn't exist
        """
        try:
            user_hash = self._get_user_hash(email)
            users_data = self._read_json(self.users_file, {"users": {}})
            
            if user_hash not in users_data["users"]:
                return None
            
            user_data = users_data["users"][user_hash]
            
            return UserSession(
                email=user_data["email"],
                user_hash=user_hash,
                logged_in=True,
                preferences={},
                created_at=datetime.fromisoformat(user_data["created_at"].replace('Z', '+00:00'))
            )
            
        except Exception as e:
            raise StorageError(f"Failed to get user session: {e}")

    def list_users(self) -> List[Dict[str, Any]]:
        """
        List all registered users (for admin purposes)
        
        Returns:
            List of user data (without password hashes)
        """
        try:
            users_data = self._read_json(self.users_file, {"users": {}})
            
            users_list = []
            for user_hash, user_data in users_data["users"].items():
                users_list.append({
                    "user_hash": user_hash,
                    "email": user_data["email"],
                    "created_at": user_data["created_at"],
                    "last_login": user_data["last_login"]
                })
            
            return users_list
            
        except Exception as e:
            raise StorageError(f"Failed to list users: {e}")

    # ---------- File Upload Operations ----------
    
    def save_file_upload(self, user_hash: str, df: pd.DataFrame, original_filename: str) -> UploadRecord:
        """
        Save uploaded file with timestamp naming and metadata tracking
        
        Args:
            user_hash: User hash from _get_user_hash()
            df: DataFrame to save
            original_filename: Original name of uploaded file
            
        Returns:
            UploadRecord with upload metadata
            
        Raises:
            StorageError: If save operation fails
        """
        try:
            # Ensure user directory exists
            user_dir = self._ensure_user_directory(user_hash)
            
            # Generate unique upload ID and timestamped filename
            upload_id = generate_upload_id()
            timestamp = datetime.now(timezone.utc)
            filename = generate_upload_filename(original_filename, timestamp)
            
            # Get file path
            file_path = get_file_path(user_dir, filename)
            
            # Validate file path for security
            if not validate_file_path(file_path, self.base_path):
                raise StorageError("Invalid file path")
            
            # Save CSV file
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            # Create upload record
            upload_record = UploadRecord(
                id=upload_id,
                filename=filename,
                original_filename=original_filename,
                upload_date=timestamp,
                n_rows=len(df),
                n_cols=len(df.columns),
                file_path=os.path.relpath(file_path, user_dir),  # Store relative path
                user_hash=user_hash
            )
            
            # Update metadata
            self._add_upload_to_metadata(user_dir, upload_record)
            
            return upload_record
            
        except Exception as e:
            raise StorageError(f"Failed to save file upload: {e}")

    def get_user_uploads(self, user_hash: str) -> List[UploadRecord]:
        """
        Get all upload records for a user
        
        Args:
            user_hash: User hash from _get_user_hash()
            
        Returns:
            List of UploadRecord objects, sorted by upload date (newest first)
            
        Raises:
            StorageError: If retrieval fails
        """
        try:
            user_dir = self._ensure_user_directory(user_hash)
            metadata_path = os.path.join(user_dir, "uploads", "metadata.json")
            
            # Load metadata
            metadata = self._read_json(metadata_path, {"uploads": []})
            
            # Convert to UploadRecord objects
            uploads = []
            for upload_data in metadata.get("uploads", []):
                try:
                    # Handle datetime parsing
                    if isinstance(upload_data.get("upload_date"), str):
                        upload_data["upload_date"] = datetime.fromisoformat(
                            upload_data["upload_date"].replace('Z', '+00:00')
                        )
                    
                    upload_record = UploadRecord(**upload_data)
                    uploads.append(upload_record)
                except Exception as e:
                    # Log corrupted record but continue
                    print(f"Warning: Skipping corrupted upload record: {e}")
                    continue
            
            # Sort by upload date (newest first)
            uploads.sort(key=lambda x: x.upload_date, reverse=True)
            
            return uploads
            
        except Exception as e:
            raise StorageError(f"Failed to get user uploads: {e}")

    def load_upload_data(self, user_hash: str, upload_id: str) -> Optional[pd.DataFrame]:
        """
        Load data from a specific upload
        
        Args:
            user_hash: User hash from _get_user_hash()
            upload_id: Upload ID from UploadRecord
            
        Returns:
            DataFrame with uploaded data or None if not found
            
        Raises:
            StorageError: If load operation fails
        """
        try:
            # Get user uploads
            uploads = self.get_user_uploads(user_hash)
            
            # Find the specific upload
            target_upload = None
            for upload in uploads:
                if upload.id == upload_id:
                    target_upload = upload
                    break
            
            if not target_upload:
                return None
            
            # Construct full file path
            user_dir = self._ensure_user_directory(user_hash)
            file_path = os.path.join(user_dir, target_upload.file_path)
            
            # Validate file path for security
            if not validate_file_path(file_path, self.base_path):
                raise StorageError("Invalid file path")
            
            # Check if file exists
            if not os.path.exists(file_path):
                return None
            
            # Load CSV file
            df = pd.read_csv(file_path, encoding='utf-8')
            return df
            
        except Exception as e:
            raise StorageError(f"Failed to load upload data: {e}")

    def get_latest_upload(self, user_hash: str) -> Optional[UploadRecord]:
        """
        Get the most recent upload for a user
        
        Args:
            user_hash: User hash from _get_user_hash()
            
        Returns:
            Most recent UploadRecord or None if no uploads
        """
        try:
            uploads = self.get_user_uploads(user_hash)
            return uploads[0] if uploads else None
        except Exception as e:
            raise StorageError(f"Failed to get latest upload: {e}")

    def delete_upload(self, user_hash: str, upload_id: str) -> bool:
        """
        Delete a specific upload and its file
        
        Args:
            user_hash: User hash from _get_user_hash()
            upload_id: Upload ID to delete
            
        Returns:
            True if successful, False if upload not found
            
        Raises:
            StorageError: If delete operation fails
        """
        try:
            user_dir = self._ensure_user_directory(user_hash)
            metadata_path = os.path.join(user_dir, "uploads", "metadata.json")
            
            # Load current metadata
            metadata = self._read_json(metadata_path, {"uploads": []})
            
            # Find and remove the upload
            uploads = metadata.get("uploads", [])
            target_upload = None
            updated_uploads = []
            
            for upload_data in uploads:
                if upload_data.get("id") == upload_id:
                    target_upload = upload_data
                else:
                    updated_uploads.append(upload_data)
            
            if not target_upload:
                return False
            
            # Delete the file
            file_path = os.path.join(user_dir, target_upload.get("file_path", ""))
            if os.path.exists(file_path) and validate_file_path(file_path, self.base_path):
                os.remove(file_path)
            
            # Update metadata
            metadata["uploads"] = updated_uploads
            self._write_json(metadata_path, metadata)
            
            return True
            
        except Exception as e:
            raise StorageError(f"Failed to delete upload: {e}")

    def _add_upload_to_metadata(self, user_dir: str, upload_record: UploadRecord) -> None:
        """
        Add upload record to user's metadata.json
        
        Args:
            user_dir: User directory path
            upload_record: UploadRecord to add
            
        Raises:
            StorageError: If metadata update fails
        """
        try:
            metadata_path = os.path.join(user_dir, "uploads", "metadata.json")
            
            # Load existing metadata
            metadata = self._read_json(metadata_path, {"uploads": []})
            
            # Convert upload record to dict
            upload_dict = {
                "id": upload_record.id,
                "filename": upload_record.filename,
                "original_filename": upload_record.original_filename,
                "upload_date": upload_record.upload_date.isoformat(),
                "n_rows": upload_record.n_rows,
                "n_cols": upload_record.n_cols,
                "file_path": upload_record.file_path,
                "user_hash": upload_record.user_hash
            }
            
            # Add to uploads list
            uploads = metadata.get("uploads", [])
            uploads.append(upload_dict)
            
            # Keep only last 50 uploads to prevent unlimited growth
            if len(uploads) > 50:
                # Sort by upload date and keep newest 50
                uploads.sort(key=lambda x: x.get("upload_date", ""), reverse=True)
                uploads = uploads[:50]
            
            metadata["uploads"] = uploads
            
            # Save updated metadata
            self._write_json(metadata_path, metadata)
            
        except Exception as e:
            raise StorageError(f"Failed to update upload metadata: {e}")

    # ---------- User Preferences Operations ----------
    
    def save_user_preferences(self, user_hash: str, preferences: Dict[str, Any]) -> bool:
        """
        Save user preferences to local storage
        
        Args:
            user_hash: User hash from _get_user_hash()
            preferences: Dictionary of user preferences
            
        Returns:
            True if successful
            
        Raises:
            StorageError: If save operation fails
        """
        try:
            user_dir = self._ensure_user_directory(user_hash)
            prefs_path = os.path.join(user_dir, "preferences", "settings.json")
            
            # Add timestamp
            preferences["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            # Save preferences
            self._write_json(prefs_path, preferences)
            
            return True
            
        except Exception as e:
            raise StorageError(f"Failed to save user preferences: {e}")

    def get_user_preferences(self, user_hash: str) -> Dict[str, Any]:
        """
        Get user preferences from local storage
        
        Args:
            user_hash: User hash from _get_user_hash()
            
        Returns:
            Dictionary of user preferences
        """
        try:
            user_dir = self._ensure_user_directory(user_hash)
            prefs_path = os.path.join(user_dir, "preferences", "settings.json")
            
            # Load preferences with defaults
            default_preferences = {
                "goal": 4.0,
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
            
            preferences = self._read_json(prefs_path, default_preferences)
            
            # Ensure all default keys exist
            for key, value in default_preferences.items():
                if key not in preferences:
                    preferences[key] = value
            
            return preferences
            
        except Exception as e:
            raise StorageError(f"Failed to get user preferences: {e}")

    # ---------- Legacy methods for compatibility ----------
    def demo_login(self, email: str) -> bool:
        """Legacy demo login method - now uses proper authentication"""
        try:
            # For demo purposes, create user if doesn't exist
            if not self.verify_user_credentials(email, "demo"):
                self.save_user_credentials(email, "demo")
            return True
        except:
            return False