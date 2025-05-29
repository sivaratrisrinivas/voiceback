"""
Configuration manager for Voiceback emotion responses.

This module handles loading and validating the emotion-to-quote configuration
from config/responses.json with robust schema validation and caching.
"""

import json
import os
import threading
from typing import Dict, List, Any, Optional
from loguru import logger
import jsonschema
from jsonschema import Draft7Validator


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


class ConfigManager:
    """Manages loading and validation of emotion response configurations."""
    
    # JSON Schema for validating responses.json structure
    RESPONSE_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "patternProperties": {
            "^[a-zA-Z_][a-zA-Z0-9_]*$": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "figure": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 100
                        },
                        "context_lines": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 10,
                            "items": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 500
                            }
                        },
                        "quote": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 1000
                        },
                        "encouragement_lines": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 10,
                            "items": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 500
                            }
                        }
                    },
                    "required": ["figure", "context_lines", "quote", "encouragement_lines"],
                    "additionalProperties": False
                }
            }
        },
        "minProperties": 1,
        "additionalProperties": False
    }
    
    def __init__(self, config_path: str = "config/responses.json"):
        """Initialize ConfigManager with path to configuration file."""
        self.config_path = config_path
        self._config_data: Optional[Dict[str, Any]] = None
        self._lock = threading.RLock()
        self._file_mtime: Optional[float] = None
        
        # Pre-compile JSON schema validator for performance
        try:
            self._schema_validator = Draft7Validator(self.RESPONSE_SCHEMA)
        except Exception as e:
            raise ConfigurationError(f"Invalid schema definition: {e}")
    
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load and validate the emotion responses configuration.
        
        Args:
            force_reload: If True, reload even if already cached
            
        Returns:
            Dict containing the loaded configuration data
            
        Raises:
            ConfigurationError: If config file doesn't exist or is invalid
        """
        with self._lock:
            # Check if we need to reload
            if not force_reload and self._config_data is not None:
                try:
                    current_mtime = os.path.getmtime(self.config_path)
                    if self._file_mtime is not None and current_mtime <= self._file_mtime:
                        logger.debug("Using cached configuration")
                        return self._config_data
                except OSError:
                    # File might have been deleted, proceed with reload
                    pass
            
            # Load configuration
            try:
                self._load_and_validate()
                logger.info(f"Successfully loaded configuration from {self.config_path}")
                return self._config_data
            except Exception as e:
                if isinstance(e, ConfigurationError):
                    raise
                raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _load_and_validate(self) -> None:
        """Load and validate configuration file."""
        # Check file exists
        if not os.path.exists(self.config_path):
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        
        # Load JSON
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config_data = json.load(file)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {e}")
        except OSError as e:
            raise ConfigurationError(f"Error reading config file: {e}")
        
        # Validate against schema
        try:
            self._schema_validator.validate(config_data)
        except jsonschema.ValidationError as e:
            error_path = ".".join(str(x) for x in e.absolute_path) if e.absolute_path else "root"
            raise ConfigurationError(
                f"Configuration validation failed at '{error_path}': {e.message}"
            )
        except jsonschema.SchemaError as e:
            raise ConfigurationError(f"Schema error: {e.message}")
        
        # Additional business logic validation
        self._validate_business_rules(config_data)
        
        # Cache the validated data
        self._config_data = config_data
        self._file_mtime = os.path.getmtime(self.config_path)
    
    def _validate_business_rules(self, config_data: Dict[str, Any]) -> None:
        """Validate business-specific rules beyond JSON schema."""
        # Ensure we have at least one emotion
        if not config_data:
            raise ConfigurationError("Configuration must contain at least one emotion")
        
        # Validate emotion names are reasonable
        for emotion in config_data.keys():
            if not emotion.strip():
                raise ConfigurationError("Emotion names cannot be empty or whitespace")
            if len(emotion) > 50:
                raise ConfigurationError(f"Emotion name '{emotion}' is too long (max 50 characters)")
        
        # Validate each emotion has valid responses
        for emotion, responses in config_data.items():
            if not responses:
                raise ConfigurationError(f"Emotion '{emotion}' must have at least one response")
            
            for i, response in enumerate(responses):
                # Check figure names are not generic
                figure = response.get('figure', '').strip()
                if figure.lower() in ['unknown', 'anonymous', 'n/a', 'none']:
                    raise ConfigurationError(
                        f"Response {i} for emotion '{emotion}': figure name '{figure}' is not allowed"
                    )
    
    def reload_config(self) -> Dict[str, Any]:
        """
        Force reload configuration from disk.
        
        Returns:
            Dict containing the reloaded configuration data
            
        Raises:
            ConfigurationError: If reload fails
        """
        logger.info("Force reloading configuration")
        return self.load_config(force_reload=True)
    
    def is_config_loaded(self) -> bool:
        """Check if configuration is currently loaded."""
        with self._lock:
            return self._config_data is not None
    
    def get_config_file_mtime(self) -> Optional[float]:
        """Get the modification time of the loaded config file."""
        with self._lock:
            return self._file_mtime
    
    def get_emotions(self) -> List[str]:
        """
        Get list of all available emotions.
        
        Returns:
            List of emotion names
            
        Raises:
            ConfigurationError: If configuration not loaded
        """
        with self._lock:
            if self._config_data is None:
                raise ConfigurationError("Configuration not loaded. Call load_config() first.")
            
            return list(self._config_data.keys())
    
    def get_response(self, emotion: str) -> Optional[Dict[str, Any]]:
        """
        Get a response configuration for the specified emotion.
        
        Args:
            emotion: The emotion to get response for
            
        Returns:
            Dictionary containing response data, or None if emotion not found
            
        Raises:
            ConfigurationError: If configuration not loaded
        """
        with self._lock:
            if self._config_data is None:
                raise ConfigurationError("Configuration not loaded. Call load_config() first.")
            
            if emotion not in self._config_data:
                return None
            
            # For now, return the first response. Later steps will add randomization.
            responses = self._config_data[emotion]
            return responses[0] if responses else None
    
    def get_all_responses(self, emotion: str) -> List[Dict[str, Any]]:
        """
        Get all response configurations for the specified emotion.
        
        Args:
            emotion: The emotion to get responses for
            
        Returns:
            List of response dictionaries, empty list if emotion not found
            
        Raises:
            ConfigurationError: If configuration not loaded
        """
        with self._lock:
            if self._config_data is None:
                raise ConfigurationError("Configuration not loaded. Call load_config() first.")
            
            return self._config_data.get(emotion, [])
    
    def is_emotion_supported(self, emotion: str) -> bool:
        """
        Check if an emotion is supported in the configuration.
        
        Args:
            emotion: The emotion to check
            
        Returns:
            True if emotion is supported, False otherwise
            
        Raises:
            ConfigurationError: If configuration not loaded
        """
        with self._lock:
            if self._config_data is None:
                raise ConfigurationError("Configuration not loaded. Call load_config() first.")
            
            return emotion in self._config_data
    
    def validate_config_file(self, config_path: Optional[str] = None) -> bool:
        """
        Validate a configuration file without loading it into this manager.
        
        Args:
            config_path: Path to config file, uses self.config_path if None
            
        Returns:
            True if valid, False otherwise
        """
        path = config_path or self.config_path
        
        try:
            if not os.path.exists(path):
                logger.error(f"Config file not found: {path}")
                return False
            
            with open(path, 'r', encoding='utf-8') as file:
                config_data = json.load(file)
            
            self._schema_validator.validate(config_data)
            self._validate_business_rules(config_data)
            
            logger.info(f"Configuration file {path} is valid")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed for {path}: {e}")
            return False 