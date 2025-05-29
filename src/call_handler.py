"""
Call Handler - Vapi Webhook Processing

This module handles incoming call webhooks from Vapi and manages call lifecycle
for the Historical Echo voice agent.
"""

from typing import Dict, Any, Optional
from loguru import logger
import datetime
import threading


class CallHandler:
    """
    Handles incoming call webhooks from Vapi and manages call lifecycle.

    Manages call events like incoming calls, call answered, call ended,
    and provides basic call control functionality.
    """

    def __init__(self):
        """Initialize the CallHandler."""
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        logger.info("CallHandler initialized")

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

            # Return assistant configuration that will speak the greeting and
            # then end the call
            greeting = ("Welcome to Historical Echo. Thank you for calling. "
                        "Goodbye.")
            return self.send_voice_message(call_id, greeting)

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

            # For Step 4: Deliver greeting instead of immediately hanging up
            greeting = ("Welcome to Historical Echo. Thank you for calling. "
                        "Goodbye.")
            return self.send_voice_message(call_id, greeting)

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

    def send_voice_message(self, call_id: str, message: str) -> Dict[str, Any]:
        """
        Send a voice message to the caller using Vapi assistant configuration.

        Args:
            call_id: The ID of the call
            message: The text message to speak

        Returns:
            Dict containing assistant configuration for Vapi
        """
        with self._lock:
            if call_id not in self.active_calls:
                logger.error(
                    f"Cannot send voice message to unknown call: {call_id}")
                return {"status": "error", "message": "Call not found"}

            logger.info(f"Sending voice message to call {call_id}: {message}")

            # Return assistant configuration that will speak the message and
            # then end the call
            system_content = (
                "You are a voice agent for Historical Echo. "
                "After delivering your first message, immediately "
                "end the call by saying nothing more.")

            return {
                "assistant": {
                    "firstMessage": message,
                    "model": {
                        "provider": "openai",
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": system_content
                            }
                        ]
                    },
                    "voice": {
                        "provider": "openai",
                        "voiceId": "alloy"
                    },
                    # End call after 1 second of silence
                    "endCallAfterSilenceMs": 1000,
                    "transcriber": {
                        "provider": "deepgram",
                        "model": "nova-2"
                    }
                }
            }

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
