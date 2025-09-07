"""
Integration tests for file operations with the complete LocalStorageManager
"""
import os
import tempfile
import shutil
import pytest
import pandas as pd
from datetime import datetime, timezone

from core.local_storage import LocalStorageManager


class TestFileOperationsIntegration:
    """Integration tests for complete file operations workflow"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory for testing"""
        temp_dir = tempfile.mkdtemp()
        storage = LocalStorageManager(base_path=temp_dir)
        yield storage, temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        return pd.DataFrame({
            'user_id': [1, 2, 3, 4, 5],
            'satisfaction_score': [4.2, 3.8, 4.5, 3.9, 4.1],
            'department': ['IT', 'HR', 'Finance', 'IT', 'Marketing'],
            'years_experience': [5, 3, 8, 2, 6]
        })

    def test_complete_user_workflow(self, temp_storage, sample_data):
        """Test complete workflow: register user, upload files, manage preferences"""
        storage, temp_dir = temp_storage
        
        # 1. Register user
        email = "user@company.com"
        password = "secure_password123"
        
        result = storage.save_user_credentials(email, password)
        assert result is True
        
        # 2. Verify user can login
        login_result = storage.verify_user_credentials(email, password)
        assert login_result is True
        
        # 3. Get user session
        user_session = storage.get_user_session(email)
        assert user_session is not None
        assert user_session.email == email
        
        user_hash = user_session.user_hash
        
        # 4. Upload first file
        upload1 = storage.save_file_upload(
            user_hash=user_hash,
            df=sample_data,
            original_filename="satisfaction_survey_q1.csv"
        )
        
        assert upload1.n_rows == 5
        assert upload1.n_cols == 4
        assert upload1.original_filename == "satisfaction_survey_q1.csv"
        
        # 5. Upload second file
        sample_data2 = sample_data.copy()
        sample_data2['satisfaction_score'] = sample_data2['satisfaction_score'] + 0.2
        
        upload2 = storage.save_file_upload(
            user_hash=user_hash,
            df=sample_data2,
            original_filename="satisfaction_survey_q2.csv"
        )
        
        # 6. Get upload history
        uploads = storage.get_user_uploads(user_hash)
        assert len(uploads) == 2
        
        # Should be sorted by date (newest first)
        assert uploads[0].id == upload2.id
        assert uploads[1].id == upload1.id
        
        # 7. Load specific upload data
        loaded_data1 = storage.load_upload_data(user_hash, upload1.id)
        assert loaded_data1 is not None
        pd.testing.assert_frame_equal(loaded_data1, sample_data)
        
        loaded_data2 = storage.load_upload_data(user_hash, upload2.id)
        assert loaded_data2 is not None
        pd.testing.assert_frame_equal(loaded_data2, sample_data2)
        
        # 8. Save user preferences
        preferences = {
            "goal": 4.2,
            "default_filters": {
                "department": "IT",
                "min_experience": 2
            },
            "ui_preferences": {
                "theme": "dark",
                "chart_type": "bar"
            }
        }
        
        pref_result = storage.save_user_preferences(user_hash, preferences)
        assert pref_result is True
        
        # 9. Get user preferences
        saved_prefs = storage.get_user_preferences(user_hash)
        assert saved_prefs["goal"] == 4.2
        assert saved_prefs["default_filters"]["department"] == "IT"
        assert saved_prefs["ui_preferences"]["theme"] == "dark"
        assert "last_updated" in saved_prefs
        
        # 10. Get latest upload
        latest = storage.get_latest_upload(user_hash)
        assert latest.id == upload2.id
        
        # 11. Delete an upload
        delete_result = storage.delete_upload(user_hash, upload1.id)
        assert delete_result is True
        
        # 12. Verify upload was deleted
        remaining_uploads = storage.get_user_uploads(user_hash)
        assert len(remaining_uploads) == 1
        assert remaining_uploads[0].id == upload2.id
        
        # 13. Verify file was actually deleted from filesystem
        user_dir = storage._ensure_user_directory(user_hash)
        file_path = os.path.join(user_dir, upload1.file_path)
        assert not os.path.exists(file_path)

    def test_multiple_users_isolation(self, temp_storage, sample_data):
        """Test that multiple users' data is properly isolated"""
        storage, _ = temp_storage
        
        # Create two users
        user1_email = "user1@company.com"
        user2_email = "user2@company.com"
        
        storage.save_user_credentials(user1_email, "password1")
        storage.save_user_credentials(user2_email, "password2")
        
        user1_hash = storage._get_user_hash(user1_email)
        user2_hash = storage._get_user_hash(user2_email)
        
        # Upload data for both users
        upload1_user1 = storage.save_file_upload(user1_hash, sample_data, "user1_data.csv")
        upload1_user2 = storage.save_file_upload(user2_hash, sample_data, "user2_data.csv")
        
        # Each user should only see their own uploads
        user1_uploads = storage.get_user_uploads(user1_hash)
        user2_uploads = storage.get_user_uploads(user2_hash)
        
        assert len(user1_uploads) == 1
        assert len(user2_uploads) == 1
        assert user1_uploads[0].id == upload1_user1.id
        assert user2_uploads[0].id == upload1_user2.id
        
        # Set different preferences for each user
        user1_prefs = {
            "goal": 4.0, 
            "ui_preferences": {"theme": "light"}
        }
        user2_prefs = {
            "goal": 3.5, 
            "ui_preferences": {"theme": "dark"}
        }
        
        storage.save_user_preferences(user1_hash, user1_prefs)
        storage.save_user_preferences(user2_hash, user2_prefs)
        
        saved_user1_prefs = storage.get_user_preferences(user1_hash)
        saved_user2_prefs = storage.get_user_preferences(user2_hash)
        
        assert saved_user1_prefs["goal"] == 4.0
        assert saved_user2_prefs["goal"] == 3.5
        assert saved_user1_prefs["ui_preferences"]["theme"] == "light"
        assert saved_user2_prefs["ui_preferences"]["theme"] == "dark"

    def test_data_persistence_across_sessions(self, temp_storage, sample_data):
        """Test that data persists when storage manager is recreated"""
        storage1, temp_dir = temp_storage
        
        # Create user and upload data with first storage instance
        email = "persistent@test.com"
        storage1.save_user_credentials(email, "password")
        user_hash = storage1._get_user_hash(email)
        
        upload = storage1.save_file_upload(user_hash, sample_data, "persistent_data.csv")
        preferences = {"goal": 4.3, "custom_setting": "test_value"}
        storage1.save_user_preferences(user_hash, preferences)
        
        # Create new storage instance (simulating app restart)
        storage2 = LocalStorageManager(base_path=temp_dir)
        
        # Verify user can still login
        login_result = storage2.verify_user_credentials(email, "password")
        assert login_result is True
        
        # Verify uploads are still accessible
        uploads = storage2.get_user_uploads(user_hash)
        assert len(uploads) == 1
        assert uploads[0].id == upload.id
        
        # Verify data can still be loaded
        loaded_data = storage2.load_upload_data(user_hash, upload.id)
        assert loaded_data is not None
        pd.testing.assert_frame_equal(loaded_data, sample_data)
        
        # Verify preferences are still accessible
        saved_prefs = storage2.get_user_preferences(user_hash)
        assert saved_prefs["goal"] == 4.3
        assert saved_prefs["custom_setting"] == "test_value"

    def test_error_recovery_scenarios(self, temp_storage, sample_data):
        """Test system behavior under various error conditions"""
        storage, temp_dir = temp_storage
        
        # Create user
        email = "error_test@test.com"
        storage.save_user_credentials(email, "password")
        user_hash = storage._get_user_hash(email)
        
        # Upload valid data
        upload = storage.save_file_upload(user_hash, sample_data, "test_data.csv")
        
        # Simulate file deletion (external process removes file)
        user_dir = storage._ensure_user_directory(user_hash)
        file_path = os.path.join(user_dir, upload.file_path)
        os.remove(file_path)
        
        # System should handle missing file gracefully
        loaded_data = storage.load_upload_data(user_hash, upload.id)
        assert loaded_data is None
        
        # Upload history should still work
        uploads = storage.get_user_uploads(user_hash)
        assert len(uploads) == 1
        assert uploads[0].id == upload.id

    def test_large_scale_operations(self, temp_storage):
        """Test system performance with larger datasets and multiple operations"""
        storage, _ = temp_storage
        
        # Create user
        email = "scale_test@test.com"
        storage.save_user_credentials(email, "password")
        user_hash = storage._get_user_hash(email)
        
        # Create larger dataset
        large_data = pd.DataFrame({
            'id': range(1000),
            'score': [i * 0.01 for i in range(1000)],
            'category': [f'cat_{i % 10}' for i in range(1000)],
            'timestamp': [datetime.now(timezone.utc) for _ in range(1000)]
        })
        
        # Upload multiple files
        uploads = []
        for i in range(5):
            upload = storage.save_file_upload(
                user_hash=user_hash,
                df=large_data,
                original_filename=f"large_dataset_{i}.csv"
            )
            uploads.append(upload)
        
        # Verify all uploads are tracked
        user_uploads = storage.get_user_uploads(user_hash)
        assert len(user_uploads) == 5
        
        # Verify data integrity for each upload
        for upload in uploads:
            loaded_data = storage.load_upload_data(user_hash, upload.id)
            assert loaded_data is not None
            assert len(loaded_data) == 1000
            assert len(loaded_data.columns) == 4
        
        # Test bulk operations
        latest = storage.get_latest_upload(user_hash)
        assert latest is not None
        
        # Delete some uploads
        for upload in uploads[:2]:
            result = storage.delete_upload(user_hash, upload.id)
            assert result is True
        
        # Verify remaining uploads
        remaining_uploads = storage.get_user_uploads(user_hash)
        assert len(remaining_uploads) == 3