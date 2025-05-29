#!/usr/bin/env python3
"""
Voiceback - Main Entry Point

Flask webhook server that handles Vapi voice agent calls and delivers
historical wisdom based on user emotions.
"""

import os
import signal
import sys
import threading
import time
from typing import Optional
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Core imports
from dotenv import load_dotenv
from loguru import logger
from flask import Flask, request, jsonify
from werkzeug.serving import make_server

# Application imports
from vapi_client import VapiClient, VapiConnectionError, VapiAuthenticationError
from call_handler import CallHandler

# Application configuration
load_dotenv()

# Global variables for app components
app = Flask(__name__)
call_handler: Optional[CallHandler] = None
vapi_client: Optional[VapiClient] = None
server_thread: Optional[threading.Thread] = None
flask_server = None  # Reference to the Werkzeug server
shutdown_event = threading.Event()  # Event to signal shutdown


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
    optional_vars = ["WEBHOOK_HOST", "WEBHOOK_PORT"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file and ensure all required variables are set")
        return False
    
    # Log optional variables with defaults
    webhook_host = os.getenv("WEBHOOK_HOST", "localhost")
    webhook_port = os.getenv("WEBHOOK_PORT", "5000")
    logger.info(f"Webhook server will run on {webhook_host}:{webhook_port}")
    
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


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Vapi webhook calls."""
    try:
        data = request.get_json()
        
        if not data:
            logger.error("No JSON data received in webhook")
            return jsonify({"error": "No JSON data provided"}), 400
        
        logger.info(f"Received webhook: {data.get('type', 'unknown')}")
        
        # Process the webhook through call handler
        response = call_handler.handle_webhook(data)
        
        if response:
            return jsonify(response)
        else:
            return jsonify({"message": "Webhook processed successfully"}), 200
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Perform basic health checks
        health_status = {
            "status": "healthy",
            "service": "Voiceback Webhook Server",
            "version": "1.0.0",
            "timestamp": time.time()
        }
        
        # Check Vapi client health if available
        if vapi_client:
            try:
                vapi_health = vapi_client.health_check()
                health_status["vapi_status"] = "connected" if vapi_health else "disconnected"
            except Exception as e:
                health_status["vapi_status"] = f"error: {str(e)}"
        
        health_status["service"] = "Voiceback Voice Agent"
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }), 500


def setup_webhook_server():
    """Setup and configure the Flask webhook server."""
    global call_handler, vapi_client
    
    # Initialize call handler
    call_handler = CallHandler()
    logger.info("CallHandler initialized")
    
    # Initialize Vapi client for call control
    vapi_client = VapiClient()
    logger.info("VapiClient initialized for call control")
    
    # Configure Flask app
    app.config['ENV'] = os.getenv('ENVIRONMENT', 'development')
    app.config['DEBUG'] = app.config['ENV'] == 'development'
    
    logger.info("Webhook server setup complete")


def start_webhook_server():
    """Start the Flask webhook server in a separate thread."""
    global server_thread, flask_server
    
    def run_server():
        host = os.getenv("WEBHOOK_HOST", "localhost")
        port = int(os.getenv("WEBHOOK_PORT", "5000"))
        
        logger.info(f"Starting webhook server on {host}:{port}")
        flask_server = make_server(host, port, app)
        flask_server.timeout = 1  # Set timeout to allow checking for shutdown
        
        logger.info("Flask server created, starting to serve...")
        try:
            while not shutdown_event.is_set():
                flask_server.handle_request()
        except Exception as e:
            if not shutdown_event.is_set():
                logger.error(f"Server error: {e}")
        finally:
            logger.info("Server thread finishing...")
    
    server_thread = threading.Thread(target=run_server, daemon=False)
    server_thread.start()
    logger.info("Webhook server started in background thread")


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


def handle_shutdown(signum, frame):
    """Handle graceful shutdown on SIGINT or SIGTERM."""
    logger.info("Shutdown signal received, cleaning up...")
    
    # Signal shutdown to server thread
    shutdown_event.set()
    logger.info("Shutdown event set")
    
    # Stop Flask server if it exists
    if flask_server:
        logger.info("Shutting down Flask server...")
        flask_server.server_close()
    
    # Wait for server thread to finish (with timeout)
    if server_thread and server_thread.is_alive():
        logger.info("Waiting for server thread to finish...")
        server_thread.join(timeout=5.0)
        if server_thread.is_alive():
            logger.warning("Server thread did not finish gracefully within timeout")
    
    # Close Vapi client
    if vapi_client:
        vapi_client.close()
    
    logger.info("Cleanup complete, exiting")
    sys.exit(0)


def main():
    """Main application entry point."""
    # Setup
    setup_logging()
    
    logger.info("Starting Voiceback Voice Agent")
    
    # Health check
    if not health_check():
        logger.error("Health check failed - exiting")
        sys.exit(1)
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Setup webhook server
    setup_webhook_server()
    start_webhook_server()
    
    logger.info("Voiceback initialized successfully")
    logger.info("Webhook server ready to receive calls")
    logger.info("Press Ctrl+C to stop the service")
    
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        handle_shutdown(signal.SIGINT, None)


if __name__ == "__main__":
    # Support CLI arguments for health check
    if len(sys.argv) > 1 and sys.argv[1] == "--health-check":
        setup_logging()
        success = health_check()
        sys.exit(0 if success else 1)
    
    main() 