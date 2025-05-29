"""
Vapi API client for voice telephony integration.

This module handles communication with the Vapi API for the Voiceback voice agent.
It provides methods for making calls, managing assistants, and handling webhooks.
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
    Vapi API client for managing voice calls and assistants
    for the Voiceback telephony voice agent.
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
            
            # Use /phone-number endpoint since /account doesn't exist in Vapi API
            response = self.session.get(f"{self.base_url}/phone-number", timeout=10)
            
            if response.status_code == 200:
                phone_numbers = response.json()
                logger.info(f"Vapi API health check passed - found {len(phone_numbers)} phone numbers")
                return True
            elif response.status_code == 401:
                logger.error("Vapi API authentication failed - invalid API key")
                raise VapiAuthenticationError("Invalid API key")
            elif response.status_code == 403:
                logger.error("Vapi API access forbidden - check API key permissions")
                raise VapiAuthenticationError("API key lacks required permissions")
            elif response.status_code == 404:
                logger.warning("Phone number endpoint not found - API is reachable but endpoint may not exist")
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
        Since /account endpoint doesn't exist in Vapi API, this returns phone number info.
        
        Returns:
            Dict containing account information (phone numbers).
            
        Raises:
            VapiConnectionError: If the request fails
        """
        try:
            response = self.session.get(f"{self.base_url}/phone-number", timeout=10)
            response.raise_for_status()
            phone_numbers = response.json()
            return {"phone_numbers": phone_numbers, "count": len(phone_numbers)}
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
    
    def register_webhook_endpoint(self, phone_number_id: str, webhook_url: str) -> Dict[str, Any]:
        """
        Register a webhook endpoint for a phone number.
        
        Args:
            phone_number_id: The ID of the phone number to configure
            webhook_url: The URL to receive webhooks
            
        Returns:
            Dict containing the updated phone number configuration
            
        Raises:
            VapiConnectionError: If the request fails
        """
        try:
            payload = {
                "serverUrl": webhook_url
            }
            
            response = self.session.patch(
                f"{self.base_url}/phone-number/{phone_number_id}", 
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Webhook endpoint registered: {webhook_url} for phone number {phone_number_id}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to register webhook endpoint: {str(e)}")
            raise VapiConnectionError(f"Failed to register webhook endpoint: {str(e)}")
    
    def create_assistant(self, assistant_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new assistant configuration.
        
        Args:
            assistant_config: The assistant configuration
            
        Returns:
            Dict containing the created assistant
            
        Raises:
            VapiConnectionError: If the request fails
        """
        try:
            response = self.session.post(
                f"{self.base_url}/assistant",
                json=assistant_config,
                timeout=10
            )
            response.raise_for_status()
            
            assistant = response.json()
            logger.info(f"Assistant created: {assistant.get('id')}")
            return assistant
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create assistant: {str(e)}")
            raise VapiConnectionError(f"Failed to create assistant: {str(e)}")
    
    def end_call(self, call_id: str) -> Dict[str, Any]:
        """
        End an active call.
        
        Args:
            call_id: The ID of the call to end
            
        Returns:
            Dict containing the call status
            
        Raises:
            VapiConnectionError: If the request fails
        """
        try:
            response = self.session.patch(
                f"{self.base_url}/call/{call_id}",
                json={"status": "ended"},
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Call ended via API: {call_id}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to end call: {str(e)}")
            raise VapiConnectionError(f"Failed to end call: {str(e)}")
    
    def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific call.
        
        Args:
            call_id: The ID of the call to check
            
        Returns:
            Dict containing call status information
            
        Raises:
            VapiConnectionError: If the request fails
        """
        try:
            response = self.session.get(f"{self.base_url}/call/{call_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get call status: {str(e)}")
            raise VapiConnectionError(f"Failed to get call status: {str(e)}")

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