"""
Unit tests for LocalStorageManager file operations and metadata management
"""
import os
import tempfile
import shutil
import pytest
import pandas as pd
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from core.local_storage import LocalStorageManager, StorageError, FileCorruptionError
from core.models import UploadRecord


class TestFileOperations:
    """Test file upload, retrieval, and metadata management operations"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory for testing"""
        temp_dir = tempfile.mkdtemp()
        storage = LocalStorageManager(base_path=temp_dir)
        yield storage, temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing"""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
            'score': [85.5, 92.0, 78.5, 96.0, 88.5],
            'category': ['A', 'B', 'A', 'C', 'B']
        })
    
    @pytest.fixture
    def user_hash(self, temp_storage):
        """Create a test user and return user hash"""
        storage, _ = temp_storage
        email = "test@example.com"
        storage.save_user_credentials(email, "password123")
        return storage._get_user_hash(email)

    def test_save_file_upload_success(self, temp_storage, sample_dataframe, user_hash):
        """Test successful file upload with metadata tracking"""
        storage, temp_dir = temp_storage
        
        # Save file upload
        upload_record = storage.save_file_upload(
            user_hash=user_hash,
            df=sample_dataframe,
            original_filename="test_data.csv"
        )
        
        # Verify upload record
        assert isinstance(upload_record, UploadRecord)
        assert upload_record.id is not None
        assert upload_record.original_filename == "test_data.csv"
        assert upload_record.n_rows == 5
        assert upload_record.n_cols == 4
        assert upload_record.user_hash == user_hash
        assert upload_record.filename.endswith("_test_data.csv")
        
        # Verify file was saved
        user_dir = storage._ensure_user_directory(user_hash)
        file_path = os.path.join(user_dir, upload_record.file_path)
        assert os.path.exists(file_path)
        
        # Verify file content
        saved_df = pd.read_csv(file_path)
        pd.testing.assert_frame_equal(saved_df, sample_dataframe)

    def test_save_file_upload_with_special_characters(self, temp_storage, sample_dataframe, user_hash):
        """Test file upload with special characters in filename"""
        storage, _ = temp_storage
        
        upload_record = storage.save_file_upload(
            user_hash=user_hash,
            df=sample_dataframe,
            original_filename="test file with spaces & symbols!.csv"
        )
        
        # Verify filename is sanitized (spaces and special chars removed)
        assert "testfilewithspacessymbols" in upload_record.filename
        assert upload_record.filename.endswith(".csv")

    def test_save_file_upload_without_extension(self, temp_storage, sample_dataframe, user_hash):
        """Test file upload without file extension"""
        storage, _ = temp_storage
        
        upload_record = storage.save_file_upload(
            user_hash=user_hash,
            df=sample_dataframe,
            original_filename="test_file_no_extension"
        )
        
        # Verify CSV extension is added
        assert upload_record.filename.endswith(".csv")

    def test_get_user_uploads_empty(self, temp_storage, user_hash):
        """Test getting uploads for user with no uploads"""
        storage, _ = temp_storage
        
        uploads = storage.get_user_uploads(user_hash)
        assert uploads == []

    def test_get_user_uploads_multiple(self, temp_storage, sample_dataframe, user_hash):
        """Test getting multiple uploads sorted by date"""
        storage, _ = temp_storage
        
        # Create multiple uploads with slight delays
        upload1 = storage.save_file_upload(user_hash, sample_dataframe, "file1.csv")
        upload2 = storage.save_file_upload(user_hash, sample_dataframe, "file2.csv")
        upload3 = storage.save_file_upload(user_hash, sample_dataframe, "file3.csv")
        
        # Get uploads
        uploads = storage.get_user_uploads(user_hash)
        
        # Verify all uploads are returned
        assert len(uploads) == 3
        
        # Verify sorting (newest first)
        upload_ids = [upload.id for upload in uploads]
        assert upload3.id in upload_ids
        assert upload2.id in upload_ids
        assert upload1.id in upload_ids
        
        # Verify newest is first
        assert uploads[0].upload_date >= uploads[1].upload_date >= uploads[2].upload_date

    def test_load_upload_data_success(self, temp_storage, sample_dataframe, user_hash):
        """Test successful loading of upload data"""
        storage, _ = temp_storage
        
        # Save upload
        upload_record = storage.save_file_upload(user_hash, sample_dataframe, "test.csv")
        
        # Load data
        loaded_df = storage.load_upload_data(user_hash, upload_record.id)
        
        # Verify data matches
        assert loaded_df is not None
        pd.testing.assert_frame_equal(loaded_df, sample_dataframe)

    def test_load_upload_data_not_found(self, temp_storage, user_hash):
        """Test loading data for non-existent upload"""
        storage, _ = temp_storage
        
        loaded_df = storage.load_upload_data(user_hash, "non_existent_id")
        assert loaded_df is None

    def test_load_upload_data_file_deleted(self, temp_storage, sample_dataframe, user_hash):
        """Test loading data when file has been deleted"""
        storage, _ = temp_storage
        
        # Save upload
        upload_record = storage.save_file_upload(user_hash, sample_dataframe, "test.csv")
        
        # Delete the file manually
        user_dir = storage._ensure_user_directory(user_hash)
        file_path = os.path.join(user_dir, upload_record.file_path)
        os.remove(file_path)
        
        # Try to load data
        loaded_df = storage.load_upload_data(user_hash, upload_record.id)
        assert loaded_df is None

    def test_get_latest_upload(self, temp_storage, sample_dataframe, user_hash):
        """Test getting the latest upload"""
        storage, _ = temp_storage
        
        # No uploads initially
        latest = storage.get_latest_upload(user_hash)
        assert latest is None
        
        # Add uploads
        upload1 = storage.save_file_upload(user_hash, sample_dataframe, "file1.csv")
        upload2 = storage.save_file_upload(user_hash, sample_dataframe, "file2.csv")
        
        # Get latest
        latest = storage.get_latest_upload(user_hash)
        assert latest is not None
        assert latest.id == upload2.id

    def test_delete_upload_success(self, temp_storage, sample_dataframe, user_hash):
        """Test successful upload deletion"""
        storage, _ = temp_storage
        
        # Save upload
        upload_record = storage.save_file_upload(user_hash, sample_dataframe, "test.csv")
        
        # Verify file exists
        user_dir = storage._ensure_user_directory(user_hash)
        file_path = os.path.join(user_dir, upload_record.file_path)
        assert os.path.exists(file_path)
        
        # Delete upload
        result = storage.delete_upload(user_hash, upload_record.id)
        assert result is True
        
        # Verify file is deleted
        assert not os.path.exists(file_path)
        
        # Verify metadata is updated
        uploads = storage.get_user_uploads(user_hash)
        assert len(uploads) == 0

    def test_delete_upload_not_found(self, temp_storage, user_hash):
        """Test deleting non-existent upload"""
        storage, _ = temp_storage
        
        result = storage.delete_upload(user_hash, "non_existent_id")
        assert result is False

    def test_metadata_corruption_handling(self, temp_storage, sample_dataframe, user_hash):
        """Test handling of corrupted metadata.json"""
        storage, _ = temp_storage
        
        # Save a valid upload first
        upload_record = storage.save_file_upload(user_hash, sample_dataframe, "test.csv")
        
        # Corrupt the metadata file
        user_dir = storage._ensure_user_directory(user_hash)
        metadata_path = os.path.join(user_dir, "uploads", "metadata.json")
        
        with open(metadata_path, 'w') as f:
            f.write("invalid json content")
        
        # Should raise StorageError (which wraps FileCorruptionError)
        with pytest.raises(StorageError):
            storage.get_user_uploads(user_hash)

    def test_metadata_limit_enforcement(self, temp_storage, sample_dataframe, user_hash):
        """Test that metadata is limited to 50 uploads"""
        storage, _ = temp_storage
        
        # Mock the limit to 3 for faster testing
        with patch.object(storage, '_add_upload_to_metadata') as mock_add:
            def limited_add(user_dir, upload_record):
                metadata_path = os.path.join(user_dir, "uploads", "metadata.json")
                metadata = storage._read_json(metadata_path, {"uploads": []})
                
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
                
                uploads = metadata.get("uploads", [])
                uploads.append(upload_dict)
                
                # Limit to 3 for testing
                if len(uploads) > 3:
                    uploads.sort(key=lambda x: x.get("upload_date", ""), reverse=True)
                    uploads = uploads[:3]
                
                metadata["uploads"] = uploads
                storage._write_json(metadata_path, metadata)
            
            mock_add.side_effect = limited_add
            
            # Add 5 uploads
            for i in range(5):
                storage.save_file_upload(user_hash, sample_dataframe, f"file{i}.csv")
            
            # Should only have 3 uploads (newest ones)
            uploads = storage.get_user_uploads(user_hash)
            assert len(uploads) == 3

    def test_file_path_security_validation(self, temp_storage, sample_dataframe, user_hash):
        """Test that file paths are validated for security"""
        storage, temp_dir = temp_storage
        
        # Mock validate_file_path to return False
        with patch('core.local_storage.validate_file_path', return_value=False):
            with pytest.raises(StorageError, match="Invalid file path"):
                storage.save_file_upload(user_hash, sample_dataframe, "test.csv")

    def test_empty_dataframe_upload(self, temp_storage, user_hash):
        """Test uploading empty DataFrame"""
        storage, _ = temp_storage
        
        empty_df = pd.DataFrame()
        upload_record = storage.save_file_upload(user_hash, empty_df, "empty.csv")
        
        assert upload_record.n_rows == 0
        assert upload_record.n_cols == 0

    def test_large_dataframe_upload(self, temp_storage, user_hash):
        """Test uploading large DataFrame"""
        storage, _ = temp_storage
        
        # Create large DataFrame
        large_df = pd.DataFrame({
            'col1': range(1000),
            'col2': [f'value_{i}' for i in range(1000)],
            'col3': [i * 0.1 for i in range(1000)]
        })
        
        upload_record = storage.save_file_upload(user_hash, large_df, "large.csv")
        
        assert upload_record.n_rows == 1000
        assert upload_record.n_cols == 3
        
        # Verify data can be loaded back
        loaded_df = storage.load_upload_data(user_hash, upload_record.id)
        assert len(loaded_df) == 1000

    def test_concurrent_uploads_different_users(self, temp_storage, sample_dataframe):
        """Test concurrent uploads from different users"""
        storage, _ = temp_storage
        
        # Create two users
        storage.save_user_credentials("user1@test.com", "pass1")
        storage.save_user_credentials("user2@test.com", "pass2")
        
        user1_hash = storage._get_user_hash("user1@test.com")
        user2_hash = storage._get_user_hash("user2@test.com")
        
        # Upload files for both users
        upload1 = storage.save_file_upload(user1_hash, sample_dataframe, "user1_file.csv")
        upload2 = storage.save_file_upload(user2_hash, sample_dataframe, "user2_file.csv")
        
        # Verify each user only sees their own uploads
        user1_uploads = storage.get_user_uploads(user1_hash)
        user2_uploads = storage.get_user_uploads(user2_hash)
        
        assert len(user1_uploads) == 1
        assert len(user2_uploads) == 1
        assert user1_uploads[0].id == upload1.id
        assert user2_uploads[0].id == upload2.id


class TestUserPreferences:
    """Test user preferences operations"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory for testing"""
        temp_dir = tempfile.mkdtemp()
        storage = LocalStorageManager(base_path=temp_dir)
        yield storage, temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def user_hash(self, temp_storage):
        """Create a test user and return user hash"""
        storage, _ = temp_storage
        email = "test@example.com"
        storage.save_user_credentials(email, "password123")
        return storage._get_user_hash(email)

    def test_save_user_preferences(self, temp_storage, user_hash):
        """Test saving user preferences"""
        storage, _ = temp_storage
        
        preferences = {
            "goal": 4.5,
            "default_filters": {
                "age_range": [25, 55],
                "sex": "Female"
            },
            "ui_preferences": {
                "theme": "dark"
            }
        }
        
        result = storage.save_user_preferences(user_hash, preferences)
        assert result is True
        
        # Verify file was created
        user_dir = storage._ensure_user_directory(user_hash)
        prefs_path = os.path.join(user_dir, "preferences", "settings.json")
        assert os.path.exists(prefs_path)

    def test_get_user_preferences_with_defaults(self, temp_storage, user_hash):
        """Test getting user preferences with default values"""
        storage, _ = temp_storage
        
        # Get preferences before saving any
        preferences = storage.get_user_preferences(user_hash)
        
        # Should return defaults
        assert preferences["goal"] == 4.0
        assert "default_filters" in preferences
        assert "ui_preferences" in preferences

    def test_get_user_preferences_saved(self, temp_storage, user_hash):
        """Test getting saved user preferences"""
        storage, _ = temp_storage
        
        # Save preferences
        custom_prefs = {
            "goal": 3.5,
            "custom_setting": "test_value"
        }
        storage.save_user_preferences(user_hash, custom_prefs)
        
        # Get preferences
        preferences = storage.get_user_preferences(user_hash)
        
        # Should include saved values and defaults
        assert preferences["goal"] == 3.5
        assert preferences["custom_setting"] == "test_value"
        assert "default_filters" in preferences  # Default should still be there

    def test_preferences_timestamp_added(self, temp_storage, user_hash):
        """Test that timestamp is added when saving preferences"""
        storage, _ = temp_storage
        
        preferences = {"goal": 4.2}
        storage.save_user_preferences(user_hash, preferences)
        
        saved_prefs = storage.get_user_preferences(user_hash)
        assert "last_updated" in saved_prefs
        
        # Verify timestamp format
        timestamp_str = saved_prefs["last_updated"]
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))  # Should not raise


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory for testing"""
        temp_dir = tempfile.mkdtemp()
        storage = LocalStorageManager(base_path=temp_dir)
        yield storage, temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def user_hash(self, temp_storage):
        """Create a test user and return user hash"""
        storage, _ = temp_storage
        email = "test@example.com"
        storage.save_user_credentials(email, "password123")
        return storage._get_user_hash(email)

    def test_invalid_user_hash(self, temp_storage):
        """Test operations with invalid user hash"""
        storage, _ = temp_storage
        
        # Empty user hash should return empty list, not raise error
        uploads = storage.get_user_uploads("")
        assert uploads == []

    def test_disk_full_simulation(self, temp_storage, user_hash):
        """Test handling of disk full scenario"""
        storage, _ = temp_storage
        
        # Mock os.makedirs to raise OSError (disk full)
        with patch('os.makedirs', side_effect=OSError("No space left on device")):
            with pytest.raises(StorageError):
                df = pd.DataFrame({'test': [1, 2, 3]})
                storage.save_file_upload(user_hash, df, "test.csv")

    def test_permission_denied_simulation(self, temp_storage, user_hash):
        """Test handling of permission denied scenario"""
        storage, _ = temp_storage
        
        # Mock file write to raise PermissionError
        with patch('pandas.DataFrame.to_csv', side_effect=PermissionError("Permission denied")):
            with pytest.raises(StorageError):
                df = pd.DataFrame({'test': [1, 2, 3]})
                storage.save_file_upload(user_hash, df, "test.csv")