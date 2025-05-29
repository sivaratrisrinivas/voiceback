"""
Call Handler - Vapi Webhook Processing

This module handles incoming call webhooks from Vapi and manages call lifecycle
for the Voiceback voice agent with emotion-based historical quote responses.
"""

from typing import Dict, Any, Optional
from loguru import logger
import datetime
import threading

# Import emotion detection and response building components
try:
    # Try relative imports first (when run as part of package)
    from .emotion_detector import EmotionDetector
    from .response_builder import ResponseBuilder
    from .config_manager import ConfigManager, ConfigurationError
except ImportError:
    # Fall back to absolute imports (when run directly or from tests)
    from emotion_detector import EmotionDetector
    from response_builder import ResponseBuilder
    from config_manager import ConfigManager, ConfigurationError

# Default greeting for when emotion system is not available
DEFAULT_GREETING = "Welcome to Voiceback. Thank you for calling. Goodbye."

# Step 7: Hardcoded input for testing emotion-based responses
TEST_EMOTION_INPUT = "I'm really anxious about my job interview tomorrow"


class CallHandler:
    """
    Handles incoming call webhooks from Vapi and manages call lifecycle.

    Manages call events like incoming calls, call answered, call ended,
    and provides emotion-based historical quote responses.
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None, 
                 enable_emotion_responses: bool = True,
                 crisis_keywords_source: Optional[str] = None,
                 default_emotion: str = "anxiety"):
        """
        Initialize the CallHandler with emotion detection capabilities.
        
        Args:
            config_manager: Optional ConfigManager instance for emotion responses
            enable_emotion_responses: If True, use emotion-based responses. If False, use default greeting.
            crisis_keywords_source: Path to crisis keywords file or None for defaults  
            default_emotion: Default emotion when input is unclear (default: "anxiety")
        """
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
        # Initialize emotion processing components only if enabled
        self.enable_emotion_responses = enable_emotion_responses
        if enable_emotion_responses:
            self.emotion_detector = EmotionDetector(
                crisis_keywords_source=crisis_keywords_source,
                default_emotion=default_emotion
            )
            self.response_builder = ResponseBuilder()
            self.config_manager = config_manager
        else:
            self.emotion_detector = None
            self.response_builder = None
            self.config_manager = None
        
        logger.info(f"CallHandler initialized with emotion detection {'enabled' if enable_emotion_responses else 'disabled'}")
        if enable_emotion_responses:
            logger.info(f"Emotion system configured with default emotion: '{default_emotion}'")

    def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming webhook from Vapi.

        Args:
            webhook_data: The webhook payload from Vapi

        Returns:
            Dict containing response data for Vapi
        """
        try:
            # Handle different webhook formats
            if 'message' in webhook_data:
                # New format: {"message": {"type": "assistant-request", "call":
                # {...}}}
                message = webhook_data['message']
                event_type = message.get('type')
                call_data = message.get('call', {})
                call_id = call_data.get('id')
            else:
                # Legacy format: {"type": "call.started", "call": {...}}
                event_type = webhook_data.get('type')
                call_data = webhook_data.get('call', {})
                call_id = call_data.get('id')

            if not call_id:
                logger.warning("Webhook received without call ID")
                return {"status": "error", "message": "Missing call ID"}

            logger.info(f"Processing webhook: {event_type} for call {call_id}")

            # Route webhook to appropriate handler based on event type
            if event_type == 'assistant-request':
                return self._handle_assistant_request(call_id, webhook_data)
            elif event_type == 'call.started':
                return self._handle_call_started(call_id, webhook_data)
            elif event_type == 'call.ended':
                return self._handle_call_ended(call_id, webhook_data)
            elif event_type == 'speech.started':
                return self._handle_speech_started(call_id, webhook_data)
            elif event_type == 'speech.ended':
                return self._handle_speech_ended(call_id, webhook_data)
            else:
                logger.info(f"Unhandled webhook type: {event_type}")
                return {"status": "received"}

        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {"status": "error", "message": "Webhook processing failed"}

    def _handle_assistant_request(
            self, call_id: str, webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle assistant request event.

        This is when Vapi needs an assistant configuration for a call.
        """
        with self._lock:
            # Extract call information
            if 'message' in webhook_data:
                call_data = webhook_data['message'].get('call', {})
            else:
                call_data = webhook_data.get('call', {})

            call_info = {
                'id': call_id,
                'started_at': datetime.datetime.now().isoformat(),
                'status': 'active',
                'from_number': call_data.get('customer', {}).get('number'),
                'to_number': call_data.get('phoneNumber', {}).get('number')
            }

            self.active_calls[call_id] = call_info
            from_number = call_info.get('from_number')
            logger.info(
                f"Assistant requested for call: {call_id} from {from_number}")

            # Choose response type based on emotion detection setting
            if self.enable_emotion_responses:
                voice_response = self._generate_emotion_response(call_id)
            else:
                voice_response = DEFAULT_GREETING
                
            return self.send_voice_message(call_id, voice_response)

    def _handle_call_started(
            self, call_id: str, webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle call started event."""
        with self._lock:
            call_data = webhook_data.get('call', {})
            customer = call_data.get('customer', {})
            phone_number = call_data.get('phoneNumber', {})

            call_info = {
                'id': call_id,
                'started_at': datetime.datetime.now().isoformat(),
                'status': 'active',
                'from_number': customer.get('number'),
                'to_number': phone_number.get('number')
            }

            self.active_calls[call_id] = call_info
            from_number = call_info.get('from_number')
            logger.info(f"Call started: {call_id} from {from_number}")

            # Choose response type based on emotion detection setting
            if self.enable_emotion_responses:
                voice_response = self._generate_emotion_response(call_id)
            else:
                voice_response = DEFAULT_GREETING
                
            return self.send_voice_message(call_id, voice_response)

    def _handle_call_ended(
            self, call_id: str, webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle call ended event."""
        with self._lock:
            if call_id in self.active_calls:
                call_info = self.active_calls[call_id]
                call_info['ended_at'] = datetime.datetime.now().isoformat()
                call_info['status'] = 'ended'

                # Log call duration
                if 'started_at' in call_info:
                    start_time_str = call_info['started_at']
                    start_time = datetime.datetime.fromisoformat(
                        start_time_str)
                    end_time = datetime.datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    call_info['duration_seconds'] = duration
                    logger.info(
                        f"Call ended: {call_id}, duration: {duration:.1f}s")

                # Remove from active calls
                del self.active_calls[call_id]
            else:
                logger.warning(f"Call ended event for unknown call: {call_id}")

            return {"status": "received"}

    def _handle_speech_started(
            self, call_id: str, webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle speech started event."""
        logger.info(f"Speech started on call: {call_id}")
        return {"status": "received"}

    def _handle_speech_ended(
            self, call_id: str, webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle speech ended event."""
        logger.info(f"Speech ended on call: {call_id}")
        return {"status": "received"}

    def send_voice_message(self, call_id: str, message: str = None) -> Dict[str, Any]:
        """
        Send a voice message for the specified call using assistant configuration.
        
        Args:
            call_id: The call ID to send the message to
            message: Optional message override. If not provided, uses default greeting.
            
        Returns:
            Assistant configuration for voice delivery
        """
        if message is None:
            greeting = DEFAULT_GREETING
        else:
            greeting = message
        
        try:
            # Create assistant configuration for voice delivery
            assistant_config = self.create_assistant_config(greeting)
            
            # Log voice delivery
            logger.info(f"Voice message configured for call {call_id}: {greeting[:50]}...")
            
            return assistant_config
            
        except Exception as e:
            logger.error(f"Failed to send voice message for call {call_id}: {str(e)}")
            raise

    def create_assistant_config(self, message: str) -> Dict[str, Any]:
        """
        Create assistant configuration for voice delivery.
        
        Args:
            message: The message to be delivered by the assistant
            
        Returns:
            Assistant configuration dictionary
        """
        # Default greeting if no message provided
        if not message:
            message = DEFAULT_GREETING
        
        # Create assistant configuration
        assistant_config = {
            "assistant": {
                "firstMessage": message,
                "model": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a voice agent for Voiceback. "
                                "Deliver the greeting message and end the call gracefully. "
                                "Keep responses brief and professional."
                            )
                        }
                    ]
                },
                "voice": {
                    "provider": "openai",
                    "voiceId": "alloy"
                },
                "endCallMessage": "Thank you for calling Voiceback. Goodbye.",
                "endCallPhrases": ["goodbye", "thank you", "end call"],
                "recordingEnabled": False,
                "silenceTimeoutSeconds": 10,
                "maxDurationSeconds": 30
            }
        }
        
        return assistant_config

    def answer_call(self, call_id: str) -> Dict[str, Any]:
        """
        Answer an incoming call.

        Args:
            call_id: The ID of the call to answer

        Returns:
            Dict containing response for Vapi
        """
        with self._lock:
            if call_id not in self.active_calls:
                logger.error(f"Cannot answer unknown call: {call_id}")
                return {"status": "error", "message": "Call not found"}

            logger.info(f"Answering call: {call_id}")

            # Update call status and timestamp
            call_info = self.active_calls[call_id]
            call_info["status"] = "active"
            call_info["answered_at"] = datetime.datetime.now().isoformat()

            return {"status": "success"}

    def end_call(self, call_id: str) -> Dict[str, Any]:
        """
        End an active call.

        Args:
            call_id: The ID of the call to end

        Returns:
            Dict containing response for Vapi
        """
        with self._lock:
            if call_id not in self.active_calls:
                logger.warning(f"Cannot end unknown call: {call_id}")
                return {"status": "error", "message": "Call not found"}

            logger.info(f"Ending call: {call_id}")

            # Return instruction to end the call
            return {
                "status": "success",
                "instruction": {
                    "type": "end_call"
                }
            }

    def get_active_calls(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all currently active calls.

        Returns:
            Dict of active call information
        """
        with self._lock:
            return self.active_calls.copy()

    def get_call_info(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific call.

        Args:
            call_id: The ID of the call

        Returns:
            Call information dict or None if not found
        """
        with self._lock:
            return self.active_calls.get(call_id)

    def _generate_emotion_response(self, call_id: str) -> str:
        """
        Generate an emotion-based historical quote response.
        
        Args:
            call_id: The call ID for logging
            
        Returns:
            Formatted voice response with historical quote
        """
        try:
            # Check if emotion detection is enabled
            if not self.enable_emotion_responses or not self.emotion_detector or not self.response_builder:
                logger.warning(f"Emotion detection disabled for call {call_id}, using default greeting")
                return DEFAULT_GREETING
            
            # Step 7: Use hardcoded anxious input for testing
            user_input = TEST_EMOTION_INPUT
            logger.info(f"Processing emotion input for call {call_id}: '{user_input}'")
            
            # Detect emotion from user input
            emotion = self.emotion_detector.detect_emotion(user_input)
            logger.info(f"Detected emotion '{emotion}' for call {call_id}")
            
            # Handle crisis case
            if emotion == "crisis":
                logger.warning(f"Crisis detected in call {call_id}")
                response = self.response_builder.build_response(emotion, None, user_input)
                return self.response_builder.add_disclaimer(response)
            
            # Get response data from configuration
            if self.config_manager:
                try:
                    response_data = self.config_manager.get_random_response(emotion)
                    if response_data:
                        logger.info(f"Found response for emotion '{emotion}' using figure '{response_data.get('figure')}'")
                    else:
                        logger.warning(f"No response data found for emotion '{emotion}'")
                except ConfigurationError as e:
                    logger.error(f"Configuration error getting response for '{emotion}': {e}")
                    response_data = None
            else:
                logger.warning("No config manager available for emotion responses")
                response_data = None
            
            # Build the response
            response = self.response_builder.build_response(emotion, response_data, user_input)
            
            # Add disclaimer and return
            final_response = self.response_builder.add_disclaimer(response)
            
            logger.info(f"Generated emotion response for call {call_id}: {final_response[:100]}...")
            return final_response
            
        except Exception as e:
            logger.error(f"Error generating emotion response for call {call_id}: {e}")
            # Fallback to default greeting
            return DEFAULT_GREETING
