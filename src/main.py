#!/usr/bin/env python3
"""
Historical Echo - Main Entry Point

A voice agent that delivers timeless wisdom from historical figures
based on user emotions. Built for Vapi platform integration.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Core imports
from dotenv import load_dotenv
from loguru import logger

# Application imports
from vapi_client import VapiClient, VapiConnectionError, VapiAuthenticationError

# Application configuration
load_dotenv()

def setup_logging():
    """Configure logging for the application."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Remove default logger and configure custom format
    logger.remove()
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    logger.info(f"Logging configured at {log_level} level")

def validate_environment():
    """Validate that required environment variables are set."""
    required_vars = ["VAPI_API_KEY", "PHONE_NUMBER"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file and ensure all required variables are set")
        return False
    
    logger.info("Environment validation passed")
    return True

def check_vapi_connectivity():
    """Check Vapi API connectivity and authentication."""
    try:
        with VapiClient() as vapi_client:
            success = vapi_client.health_check()
            if success:
                logger.info("Vapi API connectivity check passed")
                return True
            else:
                logger.error("Vapi API connectivity check failed")
                return False
    except VapiAuthenticationError as e:
        logger.error(f"Vapi authentication failed: {str(e)}")
        return False
    except VapiConnectionError as e:
        logger.error(f"Vapi connection failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Vapi connectivity check: {str(e)}")
        return False

def health_check():
    """Perform basic health check of the application."""
    logger.info("Performing health check...")
    
    # Check environment
    if not validate_environment():
        return False
    
    # Check Vapi connectivity
    if not check_vapi_connectivity():
        return False
    
    # TODO: Add configuration validation in Step 5
    
    logger.info("Health check passed - system ready")
    return True

def main():
    """Main application entry point."""
    # Setup
    setup_logging()
    
    logger.info("Starting Historical Echo Voice Agent")
    
    # Health check
    if not health_check():
        logger.error("Health check failed - exiting")
        sys.exit(1)
    
    # TODO: Start webhook server in Step 3
    # TODO: Initialize call handler in Step 3
    # TODO: Add graceful shutdown handling
    
    logger.info("Historical Echo initialized successfully")

if __name__ == "__main__":
    # Support CLI arguments for health check
    if len(sys.argv) > 1 and sys.argv[1] == "--health-check":
        setup_logging()
        success = health_check()
        sys.exit(0 if success else 1)
    
    main() 