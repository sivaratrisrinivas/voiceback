"""
Test suite for Historical Echo Vapi Client.

This test file verifies the Vapi API integration functionality
including connectivity, authentication, and error handling.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import pytest
import requests

# Add src directory to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from vapi_client import VapiClient, VapiConnectionError, VapiAuthenticationError
except ImportError:
    pytest.skip("vapi_client module not yet implemented", allow_module_level=True)


class TestVapiClient:
    """Test cases for VapiClient functionality."""
    
    def test_init_with_api_key(self):
        """Test VapiClient initialization with provided API key."""
        client = VapiClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.base_url == "https://api.vapi.ai"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer test_key"
    
    @patch.dict(os.environ, {"VAPI_API_KEY": "env_test_key"})
    def test_init_with_env_var(self):
        """Test VapiClient initialization with environment variable."""
        client = VapiClient()
        assert client.api_key == "env_test_key"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_api_key(self):
        """Test VapiClient initialization without API key raises error."""
        with pytest.raises(ValueError, match="Vapi API key is required"):
            VapiClient()
    
    @patch('vapi_client.requests.Session.get')
    def test_health_check_success(self, mock_get):
        """Test successful health check."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "Test Account", "id": "test_id"}
        mock_get.return_value = mock_response
        
        client = VapiClient(api_key="test_key")
        result = client.health_check()
        
        assert result is True
        mock_get.assert_called_once_with("https://api.vapi.ai/account", timeout=10)
    
    @patch('vapi_client.requests.Session.get')
    def test_health_check_authentication_error_401(self, mock_get):
        """Test health check with authentication error (401)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        client = VapiClient(api_key="invalid_key")
        
        with pytest.raises(VapiAuthenticationError, match="Invalid API key"):
            client.health_check()
    
    @patch('vapi_client.requests.Session.get')
    def test_health_check_authentication_error_403(self, mock_get):
        """Test health check with forbidden error (403)."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response
        
        client = VapiClient(api_key="limited_key")
        
        with pytest.raises(VapiAuthenticationError, match="API key lacks required permissions"):
            client.health_check()
    
    @patch('vapi_client.requests.Session.get')
    def test_health_check_server_error(self, mock_get):
        """Test health check with server error (5xx)."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        client = VapiClient(api_key="test_key")
        
        with pytest.raises(VapiConnectionError, match="Vapi API server error: 500"):
            client.health_check()
    
    @patch('vapi_client.requests.Session.get')
    def test_health_check_unexpected_status(self, mock_get):
        """Test health check with unexpected status code (404 now returns False)."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        client = VapiClient(api_key="test_key")
        
        # With the simplified logic, 404 should return False
        result = client.health_check()
        assert result is False
        
        # Should only call the primary endpoint once (no fallback)
        assert mock_get.call_count == 1
    
    @patch('vapi_client.requests.Session.get')
    def test_health_check_timeout(self, mock_get):
        """Test health check with timeout error."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        client = VapiClient(api_key="test_key")
        
        with pytest.raises(VapiConnectionError, match="API request timed out"):
            client.health_check()
    
    @patch('vapi_client.requests.Session.get')
    def test_health_check_connection_error(self, mock_get):
        """Test health check with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        client = VapiClient(api_key="test_key")
        
        with pytest.raises(VapiConnectionError, match="Failed to connect to Vapi API"):
            client.health_check()
    
    @patch('vapi_client.requests.Session.get')
    def test_get_account_info_success(self, mock_get):
        """Test successful account info retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "Test Account", "id": "test_id"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = VapiClient(api_key="test_key")
        result = client.get_account_info()
        
        assert result == {"name": "Test Account", "id": "test_id"}
        mock_get.assert_called_once_with("https://api.vapi.ai/account", timeout=10)
    
    @patch('vapi_client.requests.Session.get')
    def test_get_account_info_error(self, mock_get):
        """Test account info retrieval with error."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        client = VapiClient(api_key="test_key")
        
        with pytest.raises(VapiConnectionError, match="Failed to get account info: API Error"):
            client.get_account_info()
    
    @patch('vapi_client.requests.Session.get')
    def test_get_phone_numbers_success(self, mock_get):
        """Test successful phone numbers retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "phone1", "number": "+1234567890"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = VapiClient(api_key="test_key")
        result = client.get_phone_numbers()
        
        assert result == [{"id": "phone1", "number": "+1234567890"}]
        mock_get.assert_called_once_with("https://api.vapi.ai/phone-number", timeout=10)
    
    @patch('vapi_client.requests.Session.get')
    def test_get_phone_numbers_error(self, mock_get):
        """Test phone numbers retrieval with error."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        client = VapiClient(api_key="test_key")
        
        with pytest.raises(VapiConnectionError, match="Failed to get phone numbers: API Error"):
            client.get_phone_numbers()
    
    def test_context_manager(self):
        """Test VapiClient as context manager."""
        with patch.object(VapiClient, 'close') as mock_close:
            with VapiClient(api_key="test_key") as client:
                assert isinstance(client, VapiClient)
            mock_close.assert_called_once()
    
    def test_close_method(self):
        """Test explicit close method."""
        client = VapiClient(api_key="test_key")
        mock_session = Mock()
        client.session = mock_session
        
        client.close()
        
        mock_session.close.assert_called_once()


class TestVapiClientIntegration:
    """Integration tests for VapiClient with main module."""
    
    @patch('main.VapiClient')
    def test_main_health_check_integration(self, mock_vapi_client_class):
        """Test integration with main module health check."""
        # Mock the VapiClient context manager
        mock_client = Mock()
        mock_client.health_check.return_value = True
        mock_vapi_client_class.return_value.__enter__.return_value = mock_client
        mock_vapi_client_class.return_value.__exit__.return_value = None
        
        # Import and test the check_vapi_connectivity function
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from main import check_vapi_connectivity
        
        result = check_vapi_connectivity()
        
        assert result is True
        mock_client.health_check.assert_called_once()
    
    @patch('main.VapiClient')
    def test_main_health_check_failure(self, mock_vapi_client_class):
        """Test integration with main module when health check fails."""
        # Mock VapiClient to raise an exception
        mock_vapi_client_class.side_effect = VapiConnectionError("Connection failed")
        
        # Import and test the check_vapi_connectivity function
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from main import check_vapi_connectivity
        
        result = check_vapi_connectivity()
        
        assert result is False


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"]) 