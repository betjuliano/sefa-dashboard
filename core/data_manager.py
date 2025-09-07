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
    Hybrid data manager with automatic backend selection and fallback
    
    Provides unified interface for data operations that works transparently
    across local storage and Supabase backends with automatic fallback.
    """
    
    def __init__(self, use_supabase: Optional[bool] = None):
        """
        Initialize DataManager with smart backend detection
        
        Args:
            use_supabase: Force Supabase usage (True), force local (False), 
                         or auto-detect (None)
        """
        # Configuration
        self.force_local = os.getenv("FORCE_LOCAL_STORAGE", "false").lower() in ("1", "true", "yes")
        self.default_goal = float(os.getenv("DEFAULT_GOAL", "4.0"))
        
        # Initialize local storage (always available)
        storage_root = os.getenv("STORAGE_ROOT", "data")
        self.local = LocalStorageManager(base_path=storage_root)
        
        # Determine backend strategy
        self.use_supabase = self._determine_backend_strategy(use_supabase)
        self.supabase_client = None
        
        # Initialize Supabase if needed
        if self.use_supabase:
            self.supabase_client = self._initialize_supabase()
            if not self.supabase_client:
                logger.warning("Supabase initialization failed, falling back to local storage")
                self.use_supabase = False
        
        logger.info(f"DataManager initialized with backend: {'Supabase' if self.use_supabase else 'Local'}")

    def _determine_backend_strategy(self, use_supabase: Optional[bool]) -> bool:
        """
        Determine which backend to use based on configuration and availability
        
        Args:
            use_supabase: User preference for backend
            
        Returns:
            True if should use Supabase, False for local storage
        """
        # Force local if explicitly set
        if self.force_local:
            return False
        
        # Use explicit preference if provided
        if use_supabase is not None:
            return use_supabase
        
        # Auto-detect based on environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        return bool(supabase_url and supabase_key)

    def _initialize_supabase(self):
        """
        Initialize Supabase client with error handling
        
        Returns:
            Supabase client or None if initialization fails
        """
        try:
            # Import Supabase (optional dependency)
            from supabase import create_client, Client
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                logger.warning("Supabase credentials not found in environment")
                return None
            
            client = create_client(supabase_url, supabase_key)
            
            # Test connection with a simple query
            try:
                # Try to access a table to verify connection
                client.table("users").select("*").limit(1).execute()
                logger.info("Supabase connection verified")
                return client
            except Exception as e:
                logger.warning(f"Supabase connection test failed: {e}")
                return None
                
        except ImportError:
            logger.warning("Supabase library not available")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            return None

    def _execute_with_fallback(self, operation_name: str, supabase_func, local_func, *args, **kwargs):
        """
        Execute operation with automatic fallback from Supabase to local
        
        Args:
            operation_name: Name of operation for logging
            supabase_func: Function to call for Supabase backend
            local_func: Function to call for local backend
            *args, **kwargs: Arguments to pass to the functions
            
        Returns:
            Result from the successful backend
            
        Raises:
            DataManagerError: If both backends fail
        """
        primary_backend = "Supabase" if self.use_supabase else "Local"
        
        try:
            if self.use_supabase and self.supabase_client:
                logger.debug(f"Executing {operation_name} on Supabase")
                return supabase_func(*args, **kwargs)
            else:
                logger.debug(f"Executing {operation_name} on Local")
                return local_func(*args, **kwargs)
                
        except Exception as e:
            logger.warning(f"{operation_name} failed on {primary_backend}: {e}")
            
            # Try fallback if primary was Supabase
            if self.use_supabase:
                try:
                    logger.info(f"Falling back to local storage for {operation_name}")
                    return local_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for {operation_name}: {fallback_error}")
                    raise DataManagerError(f"{operation_name} failed on both backends: {e}, {fallback_error}")
            else:
                raise DataManagerError(f"{operation_name} failed: {e}")

    # ---------- Authentication Methods ----------
    
    def authenticate_user(self, email: str, password: str) -> bool:
        """
        Authenticate user with automatic fallback
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails on all backends
        """
        def supabase_auth(email: str, password: str) -> bool:
            """Authenticate using Supabase"""
            try:
                response = self.supabase_client.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                return bool(response.user)
            except Exception as e:
                raise AuthenticationError(f"Supabase authentication failed: {e}")
        
        def local_auth(email: str, password: str) -> bool:
            """Authenticate using local storage"""
            return self.local.verify_user_credentials(email, password)
        
        try:
            return self._execute_with_fallback(
                "authenticate_user",
                supabase_auth,
                local_auth,
                email, password
            )
        except DataManagerError as e:
            raise AuthenticationError(str(e))

    def register_user(self, email: str, password: str) -> bool:
        """
        Register new user with automatic fallback
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            True if registration successful
            
        Raises:
            AuthenticationError: If registration fails on all backends
        """
        def supabase_register(email: str, password: str) -> bool:
            """Register using Supabase"""
            try:
                response = self.supabase_client.auth.sign_up({
                    "email": email,
                    "password": password
                })
                return bool(response.user)
            except Exception as e:
                raise AuthenticationError(f"Supabase registration failed: {e}")
        
        def local_register(email: str, password: str) -> bool:
            """Register using local storage"""
            return self.local.save_user_credentials(email, password)
        
        try:
            return self._execute_with_fallback(
                "register_user",
                supabase_register,
                local_register,
                email, password
            )
        except DataManagerError as e:
            raise AuthenticationError(str(e))

    def get_user_session(self, email: str) -> Optional[UserSession]:
        """
        Get user session data
        
        Args:
            email: User email address
            
        Returns:
            UserSession object or None if user doesn't exist
        """
        def supabase_session(email: str) -> Optional[UserSession]:
            """Get session from Supabase"""
            try:
                # Get current user from Supabase
                user = self.supabase_client.auth.get_user()
                if user and user.user and user.user.email == email:
                    return UserSession(
                        email=email,
                        user_hash=self.local._get_user_hash(email),  # Use local hash for consistency
                        logged_in=True,
                        preferences={},
                        created_at=user.user.created_at
                    )
                return None
            except Exception as e:
                raise StorageError(f"Failed to get Supabase session: {e}")
        
        def local_session(email: str) -> Optional[UserSession]:
            """Get session from local storage"""
            return self.local.get_user_session(email)
        
        try:
            return self._execute_with_fallback(
                "get_user_session",
                supabase_session,
                local_session,
                email
            )
        except DataManagerError:
            return None

    # ---------- Upload Management Methods ----------
    
    def save_upload(self, email: str, df: pd.DataFrame, original_filename: str) -> UploadRecord:
        """
        Save uploaded file with automatic fallback
        
        Args:
            email: User email address
            df: DataFrame to save
            original_filename: Original name of uploaded file
            
        Returns:
            UploadRecord with upload metadata
            
        Raises:
            StorageError: If save operation fails on all backends
        """
        def supabase_upload(email: str, df: pd.DataFrame, original_filename: str) -> UploadRecord:
            """Save upload to Supabase"""
            # For now, delegate to local storage even when using Supabase
            # This ensures file persistence and can be enhanced later for cloud storage
            user_hash = self.local._get_user_hash(email)
            return self.local.save_file_upload(user_hash, df, original_filename)
        
        def local_upload(email: str, df: pd.DataFrame, original_filename: str) -> UploadRecord:
            """Save upload to local storage"""
            user_hash = self.local._get_user_hash(email)
            return self.local.save_file_upload(user_hash, df, original_filename)
        
        try:
            return self._execute_with_fallback(
                "save_upload",
                supabase_upload,
                local_upload,
                email, df, original_filename
            )
        except DataManagerError as e:
            raise StorageError(str(e))

    def get_user_uploads(self, email: str) -> List[UploadRecord]:
        """
        Get all upload records for a user
        
        Args:
            email: User email address
            
        Returns:
            List of UploadRecord objects
        """
        def supabase_uploads(email: str) -> List[UploadRecord]:
            """Get uploads from Supabase"""
            # For now, delegate to local storage
            user_hash = self.local._get_user_hash(email)
            return self.local.get_user_uploads(user_hash)
        
        def local_uploads(email: str) -> List[UploadRecord]:
            """Get uploads from local storage"""
            user_hash = self.local._get_user_hash(email)
            return self.local.get_user_uploads(user_hash)
        
        try:
            return self._execute_with_fallback(
                "get_user_uploads",
                supabase_uploads,
                local_uploads,
                email
            )
        except DataManagerError:
            return []

    def load_upload_data(self, email: str, upload_id: str) -> Optional[pd.DataFrame]:
        """
        Load data from a specific upload
        
        Args:
            email: User email address
            upload_id: Upload ID from UploadRecord
            
        Returns:
            DataFrame with uploaded data or None if not found
        """
        def supabase_load(email: str, upload_id: str) -> Optional[pd.DataFrame]:
            """Load upload data from Supabase"""
            # For now, delegate to local storage
            user_hash = self.local._get_user_hash(email)
            return self.local.load_upload_data(user_hash, upload_id)
        
        def local_load(email: str, upload_id: str) -> Optional[pd.DataFrame]:
            """Load upload data from local storage"""
            user_hash = self.local._get_user_hash(email)
            return self.local.load_upload_data(user_hash, upload_id)
        
        try:
            return self._execute_with_fallback(
                "load_upload_data",
                supabase_load,
                local_load,
                email, upload_id
            )
        except DataManagerError:
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
        Delete a specific upload
        
        Args:
            email: User email address
            upload_id: Upload ID to delete
            
        Returns:
            True if successful, False if upload not found
        """
        def supabase_delete(email: str, upload_id: str) -> bool:
            """Delete upload from Supabase"""
            # For now, delegate to local storage
            user_hash = self.local._get_user_hash(email)
            return self.local.delete_upload(user_hash, upload_id)
        
        def local_delete(email: str, upload_id: str) -> bool:
            """Delete upload from local storage"""
            user_hash = self.local._get_user_hash(email)
            return self.local.delete_upload(user_hash, upload_id)
        
        try:
            return self._execute_with_fallback(
                "delete_upload",
                supabase_delete,
                local_delete,
                email, upload_id
            )
        except DataManagerError:
            return False

    # ---------- User Preferences Management ----------
    
    def get_user_preferences(self, email: str) -> Dict[str, Any]:
        """
        Get user preferences with automatic fallback
        
        Args:
            email: User email address
            
        Returns:
            Dictionary of user preferences
        """
        def supabase_prefs(email: str) -> Dict[str, Any]:
            """Get preferences from Supabase"""
            # For now, delegate to local storage for file persistence
            user_hash = self.local._get_user_hash(email)
            return self.local.get_user_preferences(user_hash)
        
        def local_prefs(email: str) -> Dict[str, Any]:
            """Get preferences from local storage"""
            user_hash = self.local._get_user_hash(email)
            return self.local.get_user_preferences(user_hash)
        
        try:
            return self._execute_with_fallback(
                "get_user_preferences",
                supabase_prefs,
                local_prefs,
                email
            )
        except DataManagerError:
            # Return default preferences if all backends fail
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
        Save user preferences with automatic fallback
        
        Args:
            email: User email address
            preferences: Dictionary of user preferences
            
        Returns:
            True if successful
        """
        def supabase_save_prefs(email: str, preferences: Dict[str, Any]) -> bool:
            """Save preferences to Supabase"""
            # For now, delegate to local storage for file persistence
            user_hash = self.local._get_user_hash(email)
            return self.local.save_user_preferences(user_hash, preferences)
        
        def local_save_prefs(email: str, preferences: Dict[str, Any]) -> bool:
            """Save preferences to local storage"""
            user_hash = self.local._get_user_hash(email)
            return self.local.save_user_preferences(user_hash, preferences)
        
        try:
            return self._execute_with_fallback(
                "save_user_preferences",
                supabase_save_prefs,
                local_save_prefs,
                email, preferences
            )
        except DataManagerError:
            return False

    # ---------- Backend Management ----------
    
    def get_backend_status(self) -> Dict[str, Any]:
        """
        Get status of both backends
        
        Returns:
            Dictionary with backend status information
        """
        status = {
            "current_backend": "Supabase" if self.use_supabase else "Local",
            "force_local": self.force_local,
            "local_available": True,  # Local is always available
            "supabase_available": False,
            "supabase_connected": False
        }
        
        # Check Supabase availability
        if self.supabase_client:
            status["supabase_available"] = True
            try:
                # Test connection
                self.supabase_client.table("users").select("*").limit(1).execute()
                status["supabase_connected"] = True
            except:
                status["supabase_connected"] = False
        
        return status

    def switch_backend(self, use_supabase: bool) -> bool:
        """
        Switch between backends
        
        Args:
            use_supabase: True to switch to Supabase, False for local
            
        Returns:
            True if switch was successful
        """
        if self.force_local and use_supabase:
            logger.warning("Cannot switch to Supabase: FORCE_LOCAL_STORAGE is enabled")
            return False
        
        if use_supabase and not self.supabase_client:
            # Try to initialize Supabase
            self.supabase_client = self._initialize_supabase()
            if not self.supabase_client:
                logger.error("Cannot switch to Supabase: initialization failed")
                return False
        
        self.use_supabase = use_supabase
        logger.info(f"Switched to {'Supabase' if use_supabase else 'Local'} backend")
        return True

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