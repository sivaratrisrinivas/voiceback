"""
Configuration manager for Voiceback emotion responses.

This module handles loading and validating the emotion-to-quote configuration
from config/responses.json.
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional


class ConfigManager:
    """Manages loading and validation of emotion response configurations."""
    
    def __init__(self, config_path: str = "config/responses.json"):
        """Initialize ConfigManager with path to configuration file."""
        self.config_path = config_path
        self.config_data = None
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load and validate the emotion responses configuration.
        
        Returns:
            Dict containing the loaded configuration data
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config data is invalid
            json.JSONDecodeError: If config file is not valid JSON
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config_data = json.load(file)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in config file: {e}", e.doc, e.pos)
        
        # Validate the loaded configuration
        self._validate_config()
        
        self.logger.info(f"Successfully loaded configuration from {self.config_path}")
        return self.config_data
    
    def _validate_config(self) -> None:
        """
        Validate the structure and content of the configuration data.
        
        Raises:
            ValueError: If configuration structure is invalid
        """
        if not isinstance(self.config_data, dict):
            raise ValueError("Configuration must be a dictionary")
        
        if not self.config_data:
            raise ValueError("Configuration cannot be empty")
        
        for emotion, responses in self.config_data.items():
            if not isinstance(emotion, str):
                raise ValueError(f"Emotion key must be string, got {type(emotion)}")
            
            if not isinstance(responses, list):
                raise ValueError(f"Emotion '{emotion}' must have a list of responses")
            
            if not responses:
                raise ValueError(f"Emotion '{emotion}' must have at least one response")
            
            for i, response in enumerate(responses):
                self._validate_response(emotion, i, response)
    
    def _validate_response(self, emotion: str, index: int, response: Dict[str, Any]) -> None:
        """
        Validate a single emotion response entry.
        
        Args:
            emotion: The emotion name
            index: Index of the response in the list
            response: The response dictionary to validate
            
        Raises:
            ValueError: If response structure is invalid
        """
        if not isinstance(response, dict):
            raise ValueError(f"Response {index} for emotion '{emotion}' must be a dictionary")
        
        required_fields = ['figure', 'context_lines', 'quote', 'encouragement_lines']
        for field in required_fields:
            if field not in response:
                raise ValueError(f"Response {index} for emotion '{emotion}' missing required field: {field}")
        
        # Validate figure
        if not isinstance(response['figure'], str) or not response['figure'].strip():
            raise ValueError(f"Response {index} for emotion '{emotion}': 'figure' must be a non-empty string")
        
        # Validate quote
        if not isinstance(response['quote'], str) or not response['quote'].strip():
            raise ValueError(f"Response {index} for emotion '{emotion}': 'quote' must be a non-empty string")
        
        # Validate context_lines
        if not isinstance(response['context_lines'], list) or not response['context_lines']:
            raise ValueError(f"Response {index} for emotion '{emotion}': 'context_lines' must be a non-empty list")
        
        for line in response['context_lines']:
            if not isinstance(line, str) or not line.strip():
                raise ValueError(f"Response {index} for emotion '{emotion}': all context lines must be non-empty strings")
        
        # Validate encouragement_lines
        if not isinstance(response['encouragement_lines'], list) or not response['encouragement_lines']:
            raise ValueError(f"Response {index} for emotion '{emotion}': 'encouragement_lines' must be a non-empty list")
        
        for line in response['encouragement_lines']:
            if not isinstance(line, str) or not line.strip():
                raise ValueError(f"Response {index} for emotion '{emotion}': all encouragement lines must be non-empty strings")
    
    def get_emotions(self) -> List[str]:
        """
        Get list of all available emotions.
        
        Returns:
            List of emotion names
            
        Raises:
            RuntimeError: If configuration not loaded
        """
        if self.config_data is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        
        return list(self.config_data.keys())
    
    def get_response(self, emotion: str) -> Optional[Dict[str, Any]]:
        """
        Get a response configuration for the specified emotion.
        
        Args:
            emotion: The emotion to get response for
            
        Returns:
            Dictionary containing response data, or None if emotion not found
            
        Raises:
            RuntimeError: If configuration not loaded
        """
        if self.config_data is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        
        if emotion not in self.config_data:
            return None
        
        # For now, return the first response. Later steps will add randomization.
        responses = self.config_data[emotion]
        return responses[0] if responses else None
    
    def is_emotion_supported(self, emotion: str) -> bool:
        """
        Check if an emotion is supported in the configuration.
        
        Args:
            emotion: The emotion to check
            
        Returns:
            True if emotion is supported, False otherwise
            
        Raises:
            RuntimeError: If configuration not loaded
        """
        if self.config_data is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        
        return emotion in self.config_data 