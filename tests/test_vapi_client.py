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
        mock_response.json.return_value = [{"id": "phone1", "number": "+1234567890"}]
        mock_get.return_value = mock_response
        
        client = VapiClient(api_key="test_key")
        result = client.health_check()
        
        assert result is True
        mock_get.assert_called_once_with("https://api.vapi.ai/phone-number", timeout=10)
    
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
        mock_response.json.return_value = [{"id": "phone1", "number": "+1234567890"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = VapiClient(api_key="test_key")
        result = client.get_account_info()
        
        assert result == {"phone_numbers": [{"id": "phone1", "number": "+1234567890"}], "count": 1}
        mock_get.assert_called_once_with("https://api.vapi.ai/phone-number", timeout=10)
    
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

    @patch('requests.Session.patch')
    def test_register_webhook_endpoint_success(self, mock_patch):
        """Test successful webhook endpoint registration."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "phone123", "serverUrl": "https://example.com/webhook"}
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response
        
        client = VapiClient(api_key="test_key")
        result = client.register_webhook_endpoint("phone123", "https://example.com/webhook")
        
        assert result["serverUrl"] == "https://example.com/webhook"
        mock_patch.assert_called_once_with(
            "https://api.vapi.ai/phone-number/phone123",
            json={"serverUrl": "https://example.com/webhook"},
            timeout=10
        )

    @patch('vapi_client.requests.Session.patch')
    def test_register_webhook_endpoint_error(self, mock_patch):
        """Test webhook endpoint registration with error."""
        mock_patch.side_effect = requests.exceptions.RequestException("API Error")
        
        client = VapiClient(api_key="test_key")
        
        with pytest.raises(VapiConnectionError, match="Failed to register webhook endpoint: API Error"):
            client.register_webhook_endpoint("phone123", "https://example.com/webhook")

    @patch('vapi_client.requests.Session.post')
    def test_create_assistant_success(self, mock_post):
        """Test successful assistant creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "asst_123", "name": "Test Assistant"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        client = VapiClient(api_key="test_key")
        assistant_config = {"name": "Test Assistant", "model": "gpt-3.5-turbo"}
        result = client.create_assistant(assistant_config)
        
        assert result["id"] == "asst_123"
        mock_post.assert_called_once_with(
            "https://api.vapi.ai/assistant",
            json=assistant_config,
            timeout=10
        )

    @patch('vapi_client.requests.Session.post')
    def test_create_assistant_error(self, mock_post):
        """Test assistant creation with error."""
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        
        client = VapiClient(api_key="test_key")
        
        with pytest.raises(VapiConnectionError, match="Failed to create assistant: API Error"):
            client.create_assistant({"name": "Test Assistant"})

    @patch('vapi_client.requests.Session.patch')
    def test_end_call_success(self, mock_patch):
        """Test successful call ending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "call_123", "status": "ended"}
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response
        
        client = VapiClient(api_key="test_key")
        result = client.end_call("call_123")
        
        assert result["status"] == "ended"
        mock_patch.assert_called_once_with(
            "https://api.vapi.ai/call/call_123",
            json={"status": "ended"},
            timeout=10
        )

    @patch('vapi_client.requests.Session.patch')
    def test_end_call_error(self, mock_patch):
        """Test call ending with error."""
        mock_patch.side_effect = requests.exceptions.RequestException("API Error")
        
        client = VapiClient(api_key="test_key")
        
        with pytest.raises(VapiConnectionError, match="Failed to end call: API Error"):
            client.end_call("call_123")

    @patch('vapi_client.requests.Session.get')
    def test_get_call_status_success(self, mock_get):
        """Test successful call status retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "call_123", "status": "in-progress"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = VapiClient(api_key="test_key")
        result = client.get_call_status("call_123")
        
        assert result["status"] == "in-progress"
        mock_get.assert_called_once_with("https://api.vapi.ai/call/call_123", timeout=10)

    @patch('vapi_client.requests.Session.get')
    def test_get_call_status_error(self, mock_get):
        """Test call status retrieval with error."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        client = VapiClient(api_key="test_key")
        
        with pytest.raises(VapiConnectionError, match="Failed to get call status: API Error"):
            client.get_call_status("call_123")


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