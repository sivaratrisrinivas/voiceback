"""
Vapi Client - HTTP API Integration

This module handles communication with the Vapi API for the Historical Echo voice agent.
Focuses on server-side telephony functionality rather than client-side web calls.
"""

import os
import requests
from typing import Optional, Dict, Any
from loguru import logger


class VapiConnectionError(Exception):
    """Raised when connection to Vapi API fails."""
    pass


class VapiAuthenticationError(Exception):
    """Raised when Vapi API authentication fails."""
    pass


class VapiClient:
    """
    Client for interacting with Vapi's HTTP API.
    
    Handles API connectivity, authentication, and basic operations
    for the Historical Echo telephony voice agent.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Vapi client.
        
        Args:
            api_key: Vapi API key. If not provided, reads from VAPI_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv('VAPI_API_KEY')
        if not self.api_key:
            raise ValueError("Vapi API key is required. Set VAPI_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = "https://api.vapi.ai"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        logger.info("VapiClient initialized")
    
    def health_check(self) -> bool:
        """
        Perform a health check to verify API connectivity and authentication.
        
        Only treats HTTP 200 as success. All other responses indicate issues:
        - 401/403: Authentication errors
        - 404: Endpoint not found but API is reachable  
        - 5xx: Server errors
        - Connection errors: Network/API failures
        
        Returns:
            bool: True if connection is successful (HTTP 200), False otherwise.
            
        Raises:
            VapiConnectionError: If connection fails or server errors occur
            VapiAuthenticationError: If authentication fails
        """
        try:
            logger.info("Performing Vapi API health check...")
            
            response = self.session.get(f"{self.base_url}/account", timeout=10)
            
            if response.status_code == 200:
                account_info = response.json()
                logger.info(f"Vapi API health check passed - connected to account: {account_info.get('name', 'Unknown')}")
                return True
            elif response.status_code == 401:
                logger.error("Vapi API authentication failed - invalid API key")
                raise VapiAuthenticationError("Invalid API key")
            elif response.status_code == 403:
                logger.error("Vapi API access forbidden - check API key permissions")
                raise VapiAuthenticationError("API key lacks required permissions")
            elif response.status_code == 404:
                logger.warning("Account endpoint not found - API is reachable but endpoint may not exist")
                return False
            elif response.status_code >= 500:
                logger.error(f"Vapi API server error: {response.status_code}")
                raise VapiConnectionError(f"Vapi API server error: {response.status_code}")
            else:
                logger.warning(f"Vapi API unexpected response: {response.status_code}")
                return False
            
        except requests.exceptions.Timeout:
            logger.error("Vapi API health check timed out")
            raise VapiConnectionError("API request timed out")
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Vapi API")
            raise VapiConnectionError("Failed to connect to Vapi API")
        except requests.exceptions.RequestException as e:
            logger.error(f"Vapi API request failed: {str(e)}")
            raise VapiConnectionError(f"API request failed: {str(e)}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information from Vapi API.
        
        Returns:
            Dict containing account information.
            
        Raises:
            VapiConnectionError: If the request fails
        """
        try:
            response = self.session.get(f"{self.base_url}/account", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get account info: {str(e)}")
            raise VapiConnectionError(f"Failed to get account info: {str(e)}")
    
    def get_phone_numbers(self) -> list:
        """
        Get list of phone numbers associated with the account.
        
        Returns:
            List of phone number configurations.
            
        Raises:
            VapiConnectionError: If the request fails
        """
        try:
            response = self.session.get(f"{self.base_url}/phone-number", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get phone numbers: {str(e)}")
            raise VapiConnectionError(f"Failed to get phone numbers: {str(e)}")
    
    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            logger.info("VapiClient session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 