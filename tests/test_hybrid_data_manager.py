"""
Comprehensive tests for hybrid DataManager with backend switching and fallback scenarios
"""
import pytest
import os
import tempfile
import shutil
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from core.data_manager import DataManager, DataManagerError, BackendError
from core.local_storage import LocalStorageManager, AuthenticationError, StorageError
from core.models import UserSession, UploadRecord


class TestHybridDataManager:
    """Test suite for hybrid DataManager functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        client = Mock()
        client.auth = Mock()
        client.table = Mock()
        return client
    
    @pytest.fixture
    def local_data_manager(self, temp_dir):
        """DataManager configured for local storage only"""
        with patch.dict(os.environ, {
            'FORCE_LOCAL_STORAGE': 'true',
            'STORAGE_ROOT': temp_dir,
            'DEFAULT_GOAL': '4.0'
        }):
            return DataManager()
    
    @pytest.fixture
    def sample_dataframe(self):
        """Sample DataFrame for testing uploads"""
        return pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c'],
            'col3': [1.1, 2.2, 3.3]
        })

    def test_initialization_local_only(self, temp_dir):
        """Test DataManager initialization with local storage only"""
        with patch.dict(os.environ, {
            'FORCE_LOCAL_STORAGE': 'true',
            'STORAGE_ROOT': temp_dir
        }):
            dm = DataManager()
            
            assert not dm.use_supabase
            assert dm.force_local
            assert dm.supabase_client is None
            assert isinstance(dm.local, LocalStorageManager)
            assert dm.local.base_path == temp_dir

    def test_initialization_auto_detect_no_supabase(self, temp_dir):
        """Test auto-detection when Supabase credentials are not available"""
        with patch.dict(os.environ, {
            'STORAGE_ROOT': temp_dir,
            'SUPABASE_URL': '',
            'SUPABASE_ANON_KEY': ''
        }, clear=True):
            dm = DataManager()
            
            assert not dm.use_supabase
            assert dm.supabase_client is None

    @patch('core.data_manager.DataManager._initialize_supabase')
    def test_initialization_with_supabase_success(self, mock_init_supabase, temp_dir, mock_supabase_client):
        """Test successful Supabase initialization"""
        # Setup mock
        mock_init_supabase.return_value = mock_supabase_client
        
        with patch.dict(os.environ, {
            'STORAGE_ROOT': temp_dir,
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            dm = DataManager()
            
            assert dm.use_supabase
            assert dm.supabase_client is not None
            mock_init_supabase.assert_called_once()

    @patch('core.data_manager.DataManager._initialize_supabase')
    def test_initialization_supabase_connection_fails(self, mock_init_supabase, temp_dir, mock_supabase_client):
        """Test fallback when Supabase connection test fails"""
        # Setup mock to fail initialization
        mock_init_supabase.return_value = None
        
        with patch.dict(os.environ, {
            'STORAGE_ROOT': temp_dir,
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            dm = DataManager()
            
            assert not dm.use_supabase
            assert dm.supabase_client is None

    def test_backend_determination_force_local(self, temp_dir):
        """Test backend determination when FORCE_LOCAL_STORAGE is set"""
        with patch.dict(os.environ, {
            'FORCE_LOCAL_STORAGE': 'true',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            dm = DataManager()
            assert not dm.use_supabase

    def test_backend_determination_explicit_preference(self, temp_dir):
        """Test explicit backend preference override"""
        with patch.dict(os.environ, {'STORAGE_ROOT': temp_dir}):
            # Force local despite having Supabase credentials
            dm = DataManager(use_supabase=False)
            assert not dm.use_supabase

    def test_authenticate_user_local_success(self, local_data_manager):
        """Test successful authentication with local storage"""
        email = "test@example.com"
        password = "testpass"
        
        # Register user first
        assert local_data_manager.register_user(email, password)
        
        # Test authentication
        assert local_data_manager.authenticate_user(email, password)

    def test_authenticate_user_local_failure(self, local_data_manager):
        """Test failed authentication with local storage"""
        email = "test@example.com"
        password = "wrongpass"
        
        # Should return False for invalid credentials, not raise exception
        result = local_data_manager.authenticate_user(email, password)
        assert result is False

    def test_authenticate_user_supabase_with_fallback(self, temp_dir, mock_supabase_client):
        """Test authentication with Supabase failure and local fallback"""
        # Setup Supabase mock to fail
        mock_supabase_client.auth.sign_in_with_password.side_effect = Exception("Supabase auth failed")
        
        with patch.dict(os.environ, {
            'STORAGE_ROOT': temp_dir,
            'FORCE_LOCAL_STORAGE': 'false'
        }):
            dm = DataManager()
            dm.use_supabase = True  # Force Supabase usage for test
            dm.supabase_client = mock_supabase_client
            
            email = "test@example.com"
            password = "testpass"
            
            # Register user in local storage first
            dm.local.save_user_credentials(email, password)
            
            # Should fallback to local authentication
            assert dm.authenticate_user(email, password)

    def test_register_user_local(self, local_data_manager):
        """Test user registration with local storage"""
        email = "newuser@example.com"
        password = "newpass"
        
        assert local_data_manager.register_user(email, password)
        
        # Verify user can authenticate
        assert local_data_manager.authenticate_user(email, password)

    def test_get_user_session_local(self, local_data_manager):
        """Test getting user session from local storage"""
        email = "test@example.com"
        password = "testpass"
        
        # Register and authenticate user
        local_data_manager.register_user(email, password)
        local_data_manager.authenticate_user(email, password)
        
        session = local_data_manager.get_user_session(email)
        
        assert session is not None
        assert isinstance(session, UserSession)
        assert session.email == email
        assert session.logged_in

    def test_save_upload_local(self, local_data_manager, sample_dataframe):
        """Test saving upload with local storage"""
        email = "test@example.com"
        password = "testpass"
        filename = "test_data.csv"
        
        # Register user first
        local_data_manager.register_user(email, password)
        
        # Save upload
        upload_record = local_data_manager.save_upload(email, sample_dataframe, filename)
        
        assert isinstance(upload_record, UploadRecord)
        assert upload_record.original_filename == filename
        assert upload_record.n_rows == len(sample_dataframe)
        assert upload_record.n_cols == len(sample_dataframe.columns)

    def test_get_user_uploads_local(self, local_data_manager, sample_dataframe):
        """Test getting user uploads from local storage"""
        email = "test@example.com"
        password = "testpass"
        
        # Register user and save upload
        local_data_manager.register_user(email, password)
        upload_record = local_data_manager.save_upload(email, sample_dataframe, "test.csv")
        
        # Get uploads
        uploads = local_data_manager.get_user_uploads(email)
        
        assert len(uploads) == 1
        assert uploads[0].id == upload_record.id

    def test_load_upload_data_local(self, local_data_manager, sample_dataframe):
        """Test loading upload data from local storage"""
        email = "test@example.com"
        password = "testpass"
        
        # Register user and save upload
        local_data_manager.register_user(email, password)
        upload_record = local_data_manager.save_upload(email, sample_dataframe, "test.csv")
        
        # Load data
        loaded_df = local_data_manager.load_upload_data(email, upload_record.id)
        
        assert loaded_df is not None
        pd.testing.assert_frame_equal(loaded_df, sample_dataframe)

    def test_get_latest_upload(self, local_data_manager, sample_dataframe):
        """Test getting latest upload"""
        email = "test@example.com"
        password = "testpass"
        
        # Register user
        local_data_manager.register_user(email, password)
        
        # Save multiple uploads
        upload1 = local_data_manager.save_upload(email, sample_dataframe, "test1.csv")
        upload2 = local_data_manager.save_upload(email, sample_dataframe, "test2.csv")
        
        # Get latest upload
        latest = local_data_manager.get_latest_upload(email)
        
        assert latest is not None
        assert latest.id == upload2.id  # Should be the most recent

    def test_delete_upload_local(self, local_data_manager, sample_dataframe):
        """Test deleting upload from local storage"""
        email = "test@example.com"
        password = "testpass"
        
        # Register user and save upload
        local_data_manager.register_user(email, password)
        upload_record = local_data_manager.save_upload(email, sample_dataframe, "test.csv")
        
        # Delete upload
        assert local_data_manager.delete_upload(email, upload_record.id)
        
        # Verify upload is gone
        uploads = local_data_manager.get_user_uploads(email)
        assert len(uploads) == 0

    def test_user_preferences_local(self, local_data_manager):
        """Test user preferences management with local storage"""
        email = "test@example.com"
        password = "testpass"
        
        # Register user
        local_data_manager.register_user(email, password)
        
        # Get default preferences
        prefs = local_data_manager.get_user_preferences(email)
        assert "goal" in prefs
        assert prefs["goal"] == 4.0
        
        # Update preferences
        new_prefs = prefs.copy()
        new_prefs["goal"] = 3.5
        new_prefs["custom_setting"] = "test_value"
        
        assert local_data_manager.save_user_preferences(email, new_prefs)
        
        # Verify preferences were saved
        saved_prefs = local_data_manager.get_user_preferences(email)
        assert saved_prefs["goal"] == 3.5
        assert saved_prefs["custom_setting"] == "test_value"

    def test_get_backend_status_local_only(self, local_data_manager):
        """Test backend status reporting for local-only setup"""
        status = local_data_manager.get_backend_status()
        
        assert status["current_backend"] == "Local"
        assert status["local_available"] is True
        assert status["supabase_available"] is False
        assert status["supabase_connected"] is False

    @patch('supabase.create_client')
    def test_get_backend_status_with_supabase(self, mock_create_client, temp_dir, mock_supabase_client):
        """Test backend status reporting with Supabase"""
        mock_create_client.return_value = mock_supabase_client
        mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = []
        
        with patch.dict(os.environ, {
            'STORAGE_ROOT': temp_dir,
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            dm = DataManager()
            status = dm.get_backend_status()
            
            assert status["current_backend"] == "Supabase"
            assert status["local_available"] is True
            assert status["supabase_available"] is True
            assert status["supabase_connected"] is True

    def test_switch_backend_success(self, local_data_manager):
        """Test successful backend switching"""
        # Start with local
        assert local_data_manager.get_backend_status()["current_backend"] == "Local"
        
        # Switch to local (should succeed even without Supabase)
        assert local_data_manager.switch_backend(False)
        assert local_data_manager.get_backend_status()["current_backend"] == "Local"

    def test_switch_backend_force_local_prevents_supabase(self, local_data_manager):
        """Test that FORCE_LOCAL_STORAGE prevents switching to Supabase"""
        # Try to switch to Supabase (should fail due to FORCE_LOCAL_STORAGE)
        assert not local_data_manager.switch_backend(True)
        assert local_data_manager.get_backend_status()["current_backend"] == "Local"

    def test_demo_login_compatibility(self, local_data_manager):
        """Test legacy demo_login method for backward compatibility"""
        email = "demo@example.com"
        
        # Demo login should work
        assert local_data_manager.demo_login(email)
        
        # Should be able to authenticate with demo password
        assert local_data_manager.authenticate_user(email, "demo")

    def test_error_handling_invalid_email(self, local_data_manager):
        """Test error handling for invalid email addresses"""
        with pytest.raises(AuthenticationError):
            local_data_manager.authenticate_user("", "password")
        
        with pytest.raises(AuthenticationError):
            local_data_manager.register_user("", "password")

    def test_error_handling_empty_password(self, local_data_manager):
        """Test error handling for empty passwords"""
        with pytest.raises(AuthenticationError):
            local_data_manager.authenticate_user("test@example.com", "")
        
        with pytest.raises(AuthenticationError):
            local_data_manager.register_user("test@example.com", "")

    def test_fallback_preferences_on_error(self, local_data_manager):
        """Test that default preferences are returned when storage fails"""
        # Mock the local storage to fail
        with patch.object(local_data_manager.local, 'get_user_preferences', side_effect=Exception("Storage failed")):
            prefs = local_data_manager.get_user_preferences("test@example.com")
            
            # Should return default preferences
            assert "goal" in prefs
            assert prefs["goal"] == 4.0
            assert "default_filters" in prefs

    def test_upload_operations_with_nonexistent_user(self, local_data_manager, sample_dataframe):
        """Test upload operations with non-existent user"""
        email = "nonexistent@example.com"
        
        # Should still work (creates user directory automatically)
        upload_record = local_data_manager.save_upload(email, sample_dataframe, "test.csv")
        assert upload_record is not None
        
        # Should be able to retrieve uploads
        uploads = local_data_manager.get_user_uploads(email)
        assert len(uploads) == 1

    @patch('supabase.create_client')
    def test_supabase_fallback_on_operation_failure(self, mock_create_client, temp_dir, mock_supabase_client):
        """Test fallback to local storage when Supabase operations fail"""
        # Setup Supabase mock
        mock_create_client.return_value = mock_supabase_client
        mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = []
        
        with patch.dict(os.environ, {
            'STORAGE_ROOT': temp_dir,
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            dm = DataManager()
            dm.use_supabase = True
            dm.supabase_client = mock_supabase_client
            
            email = "test@example.com"
            password = "testpass"
            
            # Setup Supabase auth to fail
            mock_supabase_client.auth.sign_in_with_password.side_effect = Exception("Supabase down")
            
            # Register user in local storage for fallback
            dm.local.save_user_credentials(email, password)
            
            # Authentication should fallback to local
            assert dm.authenticate_user(email, password)

    def test_concurrent_backend_operations(self, local_data_manager, sample_dataframe):
        """Test that operations work correctly with concurrent access patterns"""
        email = "concurrent@example.com"
        password = "testpass"
        
        # Register user
        local_data_manager.register_user(email, password)
        
        # Simulate concurrent operations
        uploads = []
        for i in range(5):
            upload = local_data_manager.save_upload(email, sample_dataframe, f"test_{i}.csv")
            uploads.append(upload)
        
        # Verify all uploads are accessible
        retrieved_uploads = local_data_manager.get_user_uploads(email)
        assert len(retrieved_uploads) == 5
        
        # Verify data integrity
        for upload in uploads:
            data = local_data_manager.load_upload_data(email, upload.id)
            assert data is not None
            pd.testing.assert_frame_equal(data, sample_dataframe)


if __name__ == "__main__":
    pytest.main([__file__])