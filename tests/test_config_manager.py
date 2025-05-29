"""
Tests for the ConfigManager class.

Tests configuration loading, validation, caching, reload capability,
and integration with data models.
"""

import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch, mock_open
import pytest

import sys
from pathlib import Path

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager, ConfigurationError
from models import EmotionResponse, HistoricalFigure, ConfigurationStats


class TestConfigManager(unittest.TestCase):
    """Test suite for ConfigManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_config = {
            "anxiety": [
                {
                    "figure": "Seneca",
                    "context_lines": [
                        "the Stoic philosopher who wrote about facing anxiety with courage",
                        "who often wrote about finding peace in uncertain times"
                    ],
                    "quote": "We suffer more often in imagination than in reality.",
                    "encouragement_lines": [
                        "You have the strength to face what lies ahead.",
                        "Trust in your ability to handle whatever comes."
                    ]
                }
            ],
            "sadness": [
                {
                    "figure": "Marcus Aurelius",
                    "context_lines": [
                        "the Roman emperor who found wisdom through great personal losses"
                    ],
                    "quote": "Very little is needed to make a happy life; it is all within yourself, in your way of thinking.",
                    "encouragement_lines": [
                        "This difficult moment will pass, and you will find light again."
                    ]
                }
            ]
        }
    
    def test_init(self):
        """Test ConfigManager initialization."""
        manager = ConfigManager()
        self.assertEqual(manager.config_path, "config/responses.json")
        self.assertIsNone(manager._config_data)
        self.assertFalse(manager.is_config_loaded())
        
        # Test custom path
        custom_manager = ConfigManager("custom/path.json")
        self.assertEqual(custom_manager.config_path, "custom/path.json")
    
    def test_load_config_success(self):
        """Test successful configuration loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            result = manager.load_config()
            
            self.assertEqual(result, self.valid_config)
            self.assertEqual(manager._config_data, self.valid_config)
            self.assertTrue(manager.is_config_loaded())
            self.assertIsNotNone(manager.get_config_file_mtime())
        finally:
            os.unlink(temp_path)
    
    def test_load_config_caching(self):
        """Test configuration caching mechanism."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            
            # First load
            result1 = manager.load_config()
            first_mtime = manager.get_config_file_mtime()
            
            # Second load should use cache
            result2 = manager.load_config()
            second_mtime = manager.get_config_file_mtime()
            
            self.assertEqual(result1, result2)
            self.assertEqual(first_mtime, second_mtime)
            
            # Force reload should reload
            result3 = manager.load_config(force_reload=True)
            self.assertEqual(result2, result3)
            
        finally:
            os.unlink(temp_path)
    
    def test_reload_config(self):
        """Test configuration reload functionality."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            
            # Initial load
            result1 = manager.load_config()
            
            # Modify file
            modified_config = self.valid_config.copy()
            modified_config["joy"] = [{
                "figure": "Buddha",
                "context_lines": ["who found enlightenment"],
                "quote": "Happiness comes from within.",
                "encouragement_lines": ["Find joy in simple moments."]
            }]
            
            # Wait a bit to ensure mtime difference
            time.sleep(0.1)
            with open(temp_path, 'w') as f:
                json.dump(modified_config, f)
            
            # Reload
            result2 = manager.reload_config()
            
            self.assertNotEqual(result1, result2)
            self.assertIn("joy", result2)
            
        finally:
            os.unlink(temp_path)
    
    def test_load_config_file_not_found(self):
        """Test loading non-existent configuration file."""
        manager = ConfigManager("nonexistent/path.json")
        
        with self.assertRaises(ConfigurationError) as context:
            manager.load_config()
        
        self.assertIn("Configuration file not found", str(context.exception))
    
    def test_load_config_invalid_json(self):
        """Test loading invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            
            with self.assertRaises(ConfigurationError) as context:
                manager.load_config()
            
            self.assertIn("Invalid JSON", str(context.exception))
        finally:
            os.unlink(temp_path)
    
    def test_schema_validation_not_dict(self):
        """Test schema validation with non-dictionary configuration."""
        invalid_config = ["not", "a", "dict"]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            
            with self.assertRaises(ConfigurationError) as context:
                manager.load_config()
            
            self.assertIn("validation failed", str(context.exception))
        finally:
            os.unlink(temp_path)
    
    def test_schema_validation_empty_config(self):
        """Test schema validation with empty configuration."""
        empty_config = {}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(empty_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            
            with self.assertRaises(ConfigurationError) as context:
                manager.load_config()
            
            self.assertIn("does not have enough properties", str(context.exception))
        finally:
            os.unlink(temp_path)
    
    def test_schema_validation_missing_required_fields(self):
        """Test schema validation with missing required fields."""
        invalid_config = {
            "anxiety": [
                {
                    "figure": "Seneca",
                    "context_lines": ["some context"],
                    # Missing quote and encouragement_lines
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            
            with self.assertRaises(ConfigurationError) as context:
                manager.load_config()
            
            self.assertIn("validation failed", str(context.exception))
        finally:
            os.unlink(temp_path)
    
    def test_schema_validation_empty_strings(self):
        """Test schema validation with empty strings."""
        invalid_config = {
            "anxiety": [
                {
                    "figure": "",  # Empty string
                    "context_lines": ["context"],
                    "quote": "Quote",
                    "encouragement_lines": ["encouragement"]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            
            with self.assertRaises(ConfigurationError) as context:
                manager.load_config()
            
            self.assertIn("validation failed", str(context.exception))
        finally:
            os.unlink(temp_path)
    
    def test_schema_validation_empty_arrays(self):
        """Test schema validation with empty arrays."""
        invalid_config = {
            "anxiety": [
                {
                    "figure": "Seneca",
                    "context_lines": [],  # Empty array
                    "quote": "Quote",
                    "encouragement_lines": ["encouragement"]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            
            with self.assertRaises(ConfigurationError) as context:
                manager.load_config()
            
            self.assertIn("validation failed", str(context.exception))
        finally:
            os.unlink(temp_path)
    
    def test_business_rules_validation_generic_figures(self):
        """Test business rules validation rejects generic figure names."""
        invalid_config = {
            "anxiety": [
                {
                    "figure": "Unknown",  # Generic name
                    "context_lines": ["context"],
                    "quote": "Quote",
                    "encouragement_lines": ["encouragement"]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            
            with self.assertRaises(ConfigurationError) as context:
                manager.load_config()
            
            self.assertIn("figure name 'Unknown' is not allowed", str(context.exception))
        finally:
            os.unlink(temp_path)
    
    def test_validate_config_file(self):
        """Test standalone config file validation."""
        # Test valid file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager()
            result = manager.validate_config_file(temp_path)
            self.assertTrue(result)
        finally:
            os.unlink(temp_path)
        
        # Test invalid file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"invalid": "config"}, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager()
            result = manager.validate_config_file(temp_path)
            self.assertFalse(result)
        finally:
            os.unlink(temp_path)
    
    def test_get_emotions_success(self):
        """Test getting list of emotions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            manager.load_config()
            
            emotions = manager.get_emotions()
            self.assertEqual(set(emotions), {"anxiety", "sadness"})
        finally:
            os.unlink(temp_path)
    
    def test_get_emotions_not_loaded(self):
        """Test getting emotions when config not loaded."""
        manager = ConfigManager("nonexistent.json")
        
        with self.assertRaises(ConfigurationError) as context:
            manager.get_emotions()
        
        self.assertIn("Configuration not loaded", str(context.exception))
    
    def test_get_response_success(self):
        """Test getting response for emotion."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            manager.load_config()
            
            response = manager.get_response("anxiety")
            self.assertIsNotNone(response)
            self.assertEqual(response["figure"], "Seneca")
            
            # Test unknown emotion
            response = manager.get_response("unknown")
            self.assertIsNone(response)
        finally:
            os.unlink(temp_path)
    
    def test_get_all_responses(self):
        """Test getting all responses for an emotion."""
        # Create config with multiple responses
        multi_config = {
            "anxiety": [
                {
                    "figure": "Seneca",
                    "context_lines": ["context1"],
                    "quote": "Quote1",
                    "encouragement_lines": ["encouragement1"]
                },
                {
                    "figure": "Marcus Aurelius",
                    "context_lines": ["context2"],
                    "quote": "Quote2",
                    "encouragement_lines": ["encouragement2"]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(multi_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            manager.load_config()
            
            responses = manager.get_all_responses("anxiety")
            self.assertEqual(len(responses), 2)
            
            # Test unknown emotion
            responses = manager.get_all_responses("unknown")
            self.assertEqual(len(responses), 0)
        finally:
            os.unlink(temp_path)
    
    def test_is_emotion_supported_success(self):
        """Test checking if emotion is supported."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            manager.load_config()
            
            self.assertTrue(manager.is_emotion_supported("anxiety"))
            self.assertTrue(manager.is_emotion_supported("sadness"))
            self.assertFalse(manager.is_emotion_supported("joy"))
        finally:
            os.unlink(temp_path)
    
    def test_thread_safety(self):
        """Test thread safety of configuration operations."""
        import threading
        import time
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            temp_path = f.name
        
        try:
            manager = ConfigManager(temp_path)
            results = []
            exceptions = []
            
            def load_config():
                try:
                    result = manager.load_config()
                    results.append(result)
                except Exception as e:
                    exceptions.append(e)
            
            # Start multiple threads
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=load_config)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Verify results
            self.assertEqual(len(exceptions), 0)
            self.assertEqual(len(results), 5)
            for result in results:
                self.assertEqual(result, self.valid_config)
                
        finally:
            os.unlink(temp_path)


class TestDataModels(unittest.TestCase):
    """Test suite for data models."""
    
    def test_historical_figure_creation(self):
        """Test HistoricalFigure creation and validation."""
        # Valid figure
        figure = HistoricalFigure(name="Seneca", birth_year=4, death_year=65)
        self.assertEqual(figure.name, "Seneca")
        self.assertEqual(figure.display_name, "Seneca")
        self.assertEqual(figure.lifespan, "4 - 65")
        
        # Figure without years
        figure2 = HistoricalFigure(name="Marcus Aurelius")
        self.assertIsNone(figure2.lifespan)
    
    def test_historical_figure_validation(self):
        """Test HistoricalFigure validation errors."""
        # Empty name
        with self.assertRaises(ValueError):
            HistoricalFigure(name="")
        
        # Name too long
        with self.assertRaises(ValueError):
            HistoricalFigure(name="x" * 101)
        
        # Invalid years
        with self.assertRaises(ValueError):
            HistoricalFigure(name="Test", birth_year=-4000)
        
        # Death before birth
        with self.assertRaises(ValueError):
            HistoricalFigure(name="Test", birth_year=100, death_year=50)
    
    def test_emotion_response_creation(self):
        """Test EmotionResponse creation."""
        figure = HistoricalFigure(name="Seneca")
        response = EmotionResponse(
            emotion="anxiety",
            figure=figure,
            context_lines=["context line"],
            quote="Test quote",
            encouragement_lines=["encouragement line"]
        )
        
        self.assertEqual(response.emotion, "anxiety")
        self.assertEqual(response.figure.name, "Seneca")
        self.assertTrue(response.word_count > 0)
        self.assertTrue(response.estimated_speaking_time > 0)
    
    def test_emotion_response_from_config_dict(self):
        """Test EmotionResponse creation from config dictionary."""
        config_dict = {
            "figure": "Seneca",
            "context_lines": ["context"],
            "quote": "Test quote",
            "encouragement_lines": ["encouragement"]
        }
        
        response = EmotionResponse.from_config_dict("anxiety", config_dict)
        self.assertEqual(response.emotion, "anxiety")
        self.assertEqual(response.figure.name, "Seneca")
        
        # Test with missing fields
        invalid_dict = {"figure": "Seneca"}
        with self.assertRaises(ValueError):
            EmotionResponse.from_config_dict("anxiety", invalid_dict)
    
    def test_emotion_response_randomization(self):
        """Test randomization methods."""
        figure = HistoricalFigure(name="Seneca")
        response = EmotionResponse(
            emotion="anxiety",
            figure=figure,
            context_lines=["line1", "line2", "line3"],
            quote="Test quote",
            encouragement_lines=["enc1", "enc2", "enc3"]
        )
        
        # Test random selection
        context = response.get_random_context_line()
        self.assertIn(context, response.context_lines)
        
        encouragement = response.get_random_encouragement_line()
        self.assertIn(encouragement, response.encouragement_lines)
        
        # Test exclusion
        context_excluded = response.get_random_context_line(exclude=["line1", "line2"])
        self.assertEqual(context_excluded, "line3")
    
    def test_configuration_stats(self):
        """Test ConfigurationStats generation."""
        config_data = {
            "anxiety": [
                {
                    "figure": "Seneca",
                    "context_lines": ["context1", "context2"],
                    "quote": "Quote one two three",
                    "encouragement_lines": ["enc1"]
                }
            ],
            "sadness": [
                {
                    "figure": "Marcus Aurelius",
                    "context_lines": ["context3"],
                    "quote": "Quote four five",
                    "encouragement_lines": ["enc2", "enc3"]
                }
            ]
        }
        
        stats = ConfigurationStats.from_config_data(config_data)
        
        self.assertEqual(stats.total_emotions, 2)
        self.assertEqual(stats.total_responses, 2)
        self.assertEqual(stats.emotions_with_multiple_responses, 0)
        self.assertEqual(stats.unique_figures, 2)
        self.assertEqual(stats.average_responses_per_emotion, 1.0)
        self.assertTrue(stats.estimated_total_speaking_time > 0)


if __name__ == "__main__":
    unittest.main() 