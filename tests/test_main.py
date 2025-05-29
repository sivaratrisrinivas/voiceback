"""
Test suite for Historical Echo main module.

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
    from main import setup_logging, validate_environment, health_check
except ImportError:
    pytest.skip("main module not yet implemented", allow_module_level=True)


class TestMainModule:
    """Test cases for the main application module."""
    
    def test_setup_logging(self):
        """Test that logging setup completes without errors."""
        # This should not raise any exceptions
        setup_logging()
        assert True  # If we get here, logging setup worked
    
    @patch.dict(os.environ, {"VAPI_API_KEY": "test_key", "PHONE_NUMBER": "test_number"})
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
    
    @patch('main.check_vapi_connectivity')
    @patch('main.validate_environment')
    def test_health_check_success(self, mock_validate_env, mock_vapi_check):
        """Test health check with successful validation."""
        mock_validate_env.return_value = True
        mock_vapi_check.return_value = True
        result = health_check()
        assert result is True
        mock_validate_env.assert_called_once()
        mock_vapi_check.assert_called_once()
    
    @patch('main.check_vapi_connectivity')
    @patch('main.validate_environment')
    def test_health_check_failure(self, mock_validate_env, mock_vapi_check):
        """Test health check with failed validation."""
        mock_validate_env.return_value = False
        # Vapi check shouldn't be called if environment validation fails
        result = health_check()
        assert result is False
        mock_validate_env.assert_called_once()
        mock_vapi_check.assert_not_called()
    
    @patch('main.check_vapi_connectivity')
    @patch('main.validate_environment')
    def test_health_check_vapi_failure(self, mock_validate_env, mock_vapi_check):
        """Test health check with failed Vapi connectivity."""
        mock_validate_env.return_value = True
        mock_vapi_check.return_value = False
        result = health_check()
        assert result is False
        mock_validate_env.assert_called_once()
        mock_vapi_check.assert_called_once()


class TestProjectStructure:
    """Test cases to verify project structure is correct."""
    
    def test_src_directory_exists(self):
        """Test that src directory exists."""
        src_path = Path(__file__).parent.parent / "src"
        assert src_path.exists()
        assert src_path.is_dir()
    
    def test_config_directory_exists(self):
        """Test that config directory exists."""
        config_path = Path(__file__).parent.parent / "config"
        assert config_path.exists()
        assert config_path.is_dir()
    
    def test_tests_directory_exists(self):
        """Test that tests directory exists."""
        tests_path = Path(__file__).parent.parent / "tests"
        assert tests_path.exists()
        assert tests_path.is_dir()
    
    def test_docs_directory_exists(self):
        """Test that docs directory exists."""
        docs_path = Path(__file__).parent.parent / "docs"
        assert docs_path.exists()
        assert docs_path.is_dir()
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists."""
        req_path = Path(__file__).parent.parent / "requirements.txt"
        assert req_path.exists()
        assert req_path.is_file()
    
    def test_env_template_exists(self):
        """Test that .env.template exists."""
        env_template_path = Path(__file__).parent.parent / ".env.template"
        assert env_template_path.exists()
        assert env_template_path.is_file()


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"]) 