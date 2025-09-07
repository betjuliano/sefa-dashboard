"""
Utility functions for file path management and secure user hashing
"""
import os
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path


def get_user_hash(email: str) -> str:
    """
    Generate a secure hash for user email to use as directory name
    
    Args:
        email: User email address
        
    Returns:
        SHA256 hash of normalized email
        
    Raises:
        ValueError: If email is empty or invalid
    """
    if not email or not email.strip():
        raise ValueError("Email cannot be empty")
    
    # Normalize email: strip whitespace and convert to lowercase
    normalized_email = email.strip().lower()
    
    # Generate SHA256 hash
    return hashlib.sha256(normalized_email.encode('utf-8')).hexdigest()


def ensure_directory_structure(base_path: str) -> None:
    """
    Create the base directory structure for local data storage
    
    Args:
        base_path: Base path for data storage
    """
    directories = [
        base_path,
        os.path.join(base_path, "users"),
        os.path.join(base_path, "shared"),
        os.path.join(base_path, "backups")
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def get_user_directory(base_path: str, user_hash: str) -> str:
    """
    Get user-specific directory path and ensure it exists
    
    Args:
        base_path: Base data storage path
        user_hash: User hash from get_user_hash()
        
    Returns:
        Path to user directory
    """
    user_dir = os.path.join(base_path, "users", user_hash)
    
    # Create user subdirectories
    subdirs = [
        user_dir,
        os.path.join(user_dir, "uploads"),
        os.path.join(user_dir, "uploads", "files"),
        os.path.join(user_dir, "preferences")
    ]
    
    for subdir in subdirs:
        os.makedirs(subdir, exist_ok=True)
    
    return user_dir


def generate_upload_filename(original_filename: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate a timestamped filename for uploads
    
    Args:
        original_filename: Original name of uploaded file
        timestamp: Optional timestamp (defaults to current time)
        
    Returns:
        Timestamped filename
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    # Extract file extension
    name, ext = os.path.splitext(original_filename)
    if not ext:
        ext = '.csv'  # Default to CSV
    
    # Generate timestamp string
    timestamp_str = timestamp.strftime("%Y-%m-%d_%H%M%S")
    
    # Clean original filename (remove special characters)
    clean_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).strip()
    if not clean_name:
        clean_name = "upload"
    
    return f"{timestamp_str}_{clean_name}{ext}"


def generate_upload_id() -> str:
    """
    Generate a unique ID for upload records
    
    Returns:
        UUID4 string
    """
    return str(uuid.uuid4())


def get_file_path(user_dir: str, filename: str) -> str:
    """
    Get the full file path for an uploaded file
    
    Args:
        user_dir: User directory path
        filename: Name of the file
        
    Returns:
        Full path to the file
    """
    return os.path.join(user_dir, "uploads", "files", filename)


def validate_file_path(file_path: str, base_path: str) -> bool:
    """
    Validate that a file path is within the allowed base path (security check)
    
    Args:
        file_path: File path to validate
        base_path: Base path that should contain the file
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        # Resolve both paths to absolute paths
        abs_file_path = os.path.abspath(file_path)
        abs_base_path = os.path.abspath(base_path)
        
        # Check if file path starts with base path
        return abs_file_path.startswith(abs_base_path)
    except (OSError, ValueError):
        return False


def get_backup_directory(base_path: str, timestamp: Optional[datetime] = None) -> str:
    """
    Get backup directory path with timestamp
    
    Args:
        base_path: Base data storage path
        timestamp: Optional timestamp (defaults to current time)
        
    Returns:
        Path to backup directory
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(base_path, "backups", timestamp_str)
    os.makedirs(backup_dir, exist_ok=True)
    
    return backup_dir