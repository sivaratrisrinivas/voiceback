"""
Test suite for Voiceback main module.

This test file verifies the basic setup and functionality
of the main application entry point.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add src directory to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from main import setup_logging, validate_environment, check_vapi_connectivity
except ImportError:
    pytest.skip("main module not yet implemented", allow_module_level=True)


class TestMainModule:
    """Test cases for the main application module."""
    
    def test_setup_logging(self):
        """Test that logging setup completes without errors."""
        # This should not raise any exceptions
        setup_logging()
        assert True  # If we get here, logging setup worked
    
    @patch.dict(os.environ, {"VAPI_API_KEY": "test_key", "PHONE_NUMBER": "test_number", "OPENAI_API_KEY": "openai_key"})
    def test_validate_environment_success(self):
        """Test environment validation with valid variables."""
        result = validate_environment()
        assert result is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_environment_missing_vars(self):
        """Test environment validation with missing variables."""
        result = validate_environment()
        assert result is False
    
    @patch.dict(os.environ, {"VAPI_API_KEY": "test_key"}, clear=True)
    def test_validate_environment_partial_vars(self):
        """Test environment validation with some missing variables."""
        result = validate_environment()
        assert result is False
    
    @patch.dict(os.environ, {"VAPI_API_KEY": "test_key", "PHONE_NUMBER": "test_number"}, clear=True)
    def test_validate_environment_missing_llm_key(self):
        """Test environment validation with missing LLM API key."""
        result = validate_environment()
        assert result is False
    
    @patch('main.VapiClient')
    def test_check_vapi_connectivity_success(self, mock_vapi_client):
        """Test Vapi connectivity check with successful connection."""
        # Mock successful health check
        mock_client = MagicMock()
        mock_client.health_check.return_value = True
        mock_vapi_client.return_value.__enter__.return_value = mock_client
        
        result = check_vapi_connectivity()
        assert result is True
    
    @patch('main.VapiClient')
    def test_check_vapi_connectivity_failure(self, mock_vapi_client):
        """Test Vapi connectivity check with failed connection."""
        # Mock failed health check
        mock_client = MagicMock()
        mock_client.health_check.return_value = False
        mock_vapi_client.return_value.__enter__.return_value = mock_client
        
        result = check_vapi_connectivity()
        assert result is False


class TestProjectStructure:
    """Test cases to verify project structure is correct."""
    
    def test_src_directory_exists(self):
        """Test that src directory exists."""
        src_path = Path(__file__).parent.parent / "src"
        assert src_path.exists()
        assert src_path.is_dir()
    
    def test_tests_directory_exists(self):
        """Test that tests directory exists."""
        tests_path = Path(__file__).parent.parent / "tests"
        assert tests_path.exists()
        assert tests_path.is_dir()
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists."""
        req_path = Path(__file__).parent.parent / "requirements.txt"
        assert req_path.exists()
        assert req_path.is_file()
    
    def test_env_template_exists(self):
        """Test that .env.template exists."""
        env_template_path = Path(__file__).parent.parent / "env.template"
        assert env_template_path.exists()
        assert env_template_path.is_file()


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"]) 