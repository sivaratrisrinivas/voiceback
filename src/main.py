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
from config_manager import ConfigManager, ConfigurationError
from models import ConfigurationStats

# Application configuration
load_dotenv()

# Global variables for app components
app = Flask(__name__)
call_handler: Optional[CallHandler] = None
vapi_client: Optional[VapiClient] = None
config_manager: Optional[ConfigManager] = None
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


def load_and_validate_configuration():
    """Load and validate application configuration."""
    global config_manager
    
    try:
        # Initialize configuration manager
        config_path = os.getenv("CONFIG_PATH", "config/responses.json")
        config_manager = ConfigManager(config_path)
        
        logger.info(f"Loading configuration from {config_path}")
        
        # Load configuration
        config_data = config_manager.load_config()
        
        # Generate and log statistics
        stats = ConfigurationStats.from_config_data(config_data)
        logger.info(f"Configuration loaded successfully:")
        logger.info(f"  - {stats.total_emotions} emotions with {stats.total_responses} total responses")
        logger.info(f"  - {stats.unique_figures} unique historical figures")
        logger.info(f"  - Estimated total speaking time: {stats.estimated_total_speaking_time:.1f}s")
        
        # Log available emotions
        emotions = config_manager.get_emotions()
        logger.info(f"Available emotions: {', '.join(emotions)}")
        
        return True
        
    except ConfigurationError as e:
        logger.error(f"Configuration validation failed: {e}")
        logger.error("Please check your configuration file and fix any issues")
        return False
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        return False


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
        
        # Check configuration health
        if config_manager:
            try:
                # Check if config is loaded
                if config_manager.is_config_loaded():
                    emotions = config_manager.get_emotions()
                    health_status["checks"]["configuration"] = {
                        "status": "loaded",
                        "message": f"Configuration valid with {len(emotions)} emotions",
                        "emotions": emotions
                    }
                    
                    # Check if config file has been modified
                    current_mtime = config_manager.get_config_file_mtime()
                    if current_mtime:
                        import os
                        actual_mtime = os.path.getmtime(config_manager.config_path)
                        if actual_mtime > current_mtime:
                            health_status["checks"]["configuration"]["status"] = "outdated"
                            health_status["checks"]["configuration"]["message"] += " (file modified, reload recommended)"
                            health_status["status"] = "degraded"
                else:
                    health_status["checks"]["configuration"] = {
                        "status": "not_loaded",
                        "message": "Configuration not loaded"
                    }
                    health_status["status"] = "unhealthy"
            except Exception as e:
                health_status["checks"]["configuration"] = {
                    "status": "error",
                    "message": f"Configuration error: {str(e)}"
                }
                health_status["status"] = "unhealthy"
        
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


@app.route('/config/reload', methods=['POST'])
def reload_config():
    """Reload configuration endpoint."""
    try:
        if not config_manager:
            return jsonify({"error": "Configuration manager not initialized"}), 500
        
        logger.info("Reloading configuration via API request")
        config_data = config_manager.reload_config()
        
        # Generate updated statistics
        stats = ConfigurationStats.from_config_data(config_data)
        
        return jsonify({
            "status": "success",
            "message": "Configuration reloaded successfully",
            "stats": {
                "total_emotions": stats.total_emotions,
                "total_responses": stats.total_responses,
                "unique_figures": stats.unique_figures,
                "emotions": config_manager.get_emotions()
            }
        }), 200
        
    except ConfigurationError as e:
        logger.error(f"Configuration reload failed: {e}")
        return jsonify({"error": f"Configuration reload failed: {e}"}), 400
    except Exception as e:
        logger.error(f"Unexpected error during config reload: {e}")
        return jsonify({"error": "Internal server error"}), 500


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
        
        # Load and validate configuration
        logger.info("Loading and validating configuration...")
        if not load_and_validate_configuration():
            logger.error("Configuration validation failed. Exiting.")
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
        logger.info(f"  - Config Reload: http://{host}:{port}/config/reload")
        logger.info("Press Ctrl+C to stop the server")
        
        # Keep the main thread alive
        try:
            while not shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            handle_shutdown(signal.SIGINT, None)
            
    except Exception as e:
        logger.error(f"Failed to start Voiceback: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 