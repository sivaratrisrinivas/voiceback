#!/usr/bin/env python3
"""
Voiceback - Main Entry Point

Flask webhook server that handles Vapi voice agent calls and delivers
LLM-powered emotional support and guidance.
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
    llm_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY"]  # Any LLM API key
    optional_vars = ["WEBHOOK_HOST", "WEBHOOK_PORT", "LLM_PROVIDER"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    # Check for at least one LLM API key
    has_llm_key = any(os.getenv(var) for var in llm_vars)
    if not has_llm_key:
        logger.error("At least one LLM API key is required (OPENAI_API_KEY, ANTHROPIC_API_KEY, or XAI_API_KEY)")
        missing_vars.extend(["One of: OPENAI_API_KEY, ANTHROPIC_API_KEY, XAI_API_KEY"])
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file and ensure all required variables are set")
        return False
    
    # Log configuration
    webhook_host = os.getenv("WEBHOOK_HOST", "localhost")
    webhook_port = os.getenv("WEBHOOK_PORT", "5000")
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    logger.info(f"Webhook server will run on {webhook_host}:{webhook_port}")
    logger.info(f"LLM provider: {llm_provider}")
    
    # Validate LLM provider has corresponding API key
    if llm_provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        logger.error("LLM_PROVIDER is set to 'openai' but OPENAI_API_KEY is missing")
        return False
    elif llm_provider == "xai" and not os.getenv("XAI_API_KEY"):
        logger.error("LLM_PROVIDER is set to 'xai' but XAI_API_KEY is missing")
        return False
    elif llm_provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("LLM_PROVIDER is set to 'anthropic' but ANTHROPIC_API_KEY is missing")
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
            "service": "Voiceback Voice Agent",
            "version": "1.0.0",
            "timestamp": time.time(),
            "checks": {}
        }
        
        # Check Vapi client health if available
        if vapi_client:
            try:
                vapi_health = vapi_client.health_check()
                health_status["checks"]["vapi"] = {
                    "status": "connected" if vapi_health else "disconnected",
                    "message": "Vapi API connectivity check"
                }
            except Exception as e:
                health_status["checks"]["vapi"] = {
                    "status": "error",
                    "message": f"Vapi connectivity error: {str(e)}"
                }
                health_status["status"] = "degraded"
        
        # Check LLM provider
        if call_handler:
            health_status["checks"]["llm"] = {
                "status": "configured",
                "provider": call_handler.llm_provider,
                "message": f"LLM provider: {call_handler.llm_provider}"
            }
        
        # Check active calls
        if call_handler:
            active_calls = call_handler.get_active_calls()
            health_status["checks"]["calls"] = {
                "status": "active",
                "count": len(active_calls),
                "message": f"{len(active_calls)} active calls"
            }
        
        # Set overall status code based on health status
        # 200: Service is operational (healthy or degraded but functional)
        # 503: Service is not operational (unhealthy)
        if health_status["status"] in ["healthy", "degraded"]:
            status_code = 200
        else:  # unhealthy
            status_code = 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }), 503


@app.route('/calls', methods=['GET'])
def get_active_calls():
    """Get active calls endpoint."""
    try:
        if not call_handler:
            return jsonify({"error": "CallHandler not initialized"}), 500
        
        active_calls = call_handler.get_active_calls()
        
        return jsonify({
            "status": "success",
            "calls": active_calls,
            "count": len(active_calls)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting active calls: {e}")
        return jsonify({"error": "Internal server error"}), 500


def setup_webhook_server():
    """Setup and configure the Flask webhook server."""
    global call_handler, vapi_client
    
    # Get LLM configuration
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    llm_api_key = None
    
    if llm_provider == "openai":
        llm_api_key = os.getenv("OPENAI_API_KEY")
    elif llm_provider == "anthropic":
        llm_api_key = os.getenv("ANTHROPIC_API_KEY")
    elif llm_provider == "xai":
        llm_api_key = os.getenv("XAI_API_KEY")
    
    # Initialize call handler with LLM configuration
    call_handler = CallHandler(llm_api_key=llm_api_key, llm_provider=llm_provider)
    logger.info(f"CallHandler initialized with {llm_provider} LLM")
    
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
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    logger.info("Webhook server started in background thread")


def handle_shutdown(signum, frame):
    """Handle graceful shutdown signal."""
    logger.info(f"Received shutdown signal ({signum}). Shutting down gracefully...")
    
    # Set shutdown event to stop server loop
    shutdown_event.set()
    
    # Shutdown flask server if running
    if flask_server:
        logger.info("Shutting down Flask server...")
        flask_server.shutdown()
    
    # Wait for server thread to finish
    if server_thread and server_thread.is_alive():
        logger.info("Waiting for server thread to finish...")
        server_thread.join(timeout=5)
        if server_thread.is_alive():
            logger.warning("Server thread did not finish within timeout")
        else:
            logger.info("Server thread finished successfully")
    
    logger.info("Shutdown complete")
    sys.exit(0)


def main():
    """Main entry point for the application."""
    try:
        logger.info("Starting Voiceback Voice Agent...")
        
        # Setup logging first
        setup_logging()
        logger.info("Voiceback startup initiated")
        
        # Validate environment
        logger.info("Validating environment configuration...")
        if not validate_environment():
            logger.error("Environment validation failed. Exiting.")
            sys.exit(1)
        
        # Check Vapi connectivity
        logger.info("Checking Vapi API connectivity...")
        if not check_vapi_connectivity():
            logger.error("Vapi connectivity check failed. Exiting.")
            sys.exit(1)
        
        # Setup webhook server
        logger.info("Setting up webhook server...")
        setup_webhook_server()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        # Start webhook server
        start_webhook_server()
        
        logger.info("Voiceback Voice Agent is running!")
        logger.info("Webhook endpoints:")
        host = os.getenv("WEBHOOK_HOST", "localhost")
        port = os.getenv("WEBHOOK_PORT", "5000")
        logger.info(f"  - Webhook: http://{host}:{port}/webhook")
        logger.info(f"  - Health Check: http://{host}:{port}/health")
        logger.info(f"  - Active Calls: http://{host}:{port}/calls")
        logger.info("Press Ctrl+C to stop the server")
        
        # Keep the main thread alive
        try:
            while not shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            handle_shutdown(signal.SIGINT, None)
            
    except Exception as e:
        logger.error(f"Fatal error during startup: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 