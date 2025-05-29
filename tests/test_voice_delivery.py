"""
Tests for voice delivery functionality in CallHandler.

Tests the voice message delivery system that handles greeting delivery
through Vapi assistant configurations.
"""

import pytest
from unittest.mock import Mock, patch
import datetime
import sys
from pathlib import Path

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from call_handler import CallHandler


class TestVoiceDelivery:
    """Test suite for voice delivery functionality."""

    @pytest.fixture
    def call_handler(self):
        """Create a CallHandler instance for testing."""
        return CallHandler()

    @pytest.fixture
    def sample_call_id(self):
        """Sample call ID for testing."""
        return "call_12345"

    @pytest.fixture
    def sample_assistant_request_webhook(self):
        """Sample assistant request webhook data."""
        return {
            "message": {
                "type": "assistant-request",
                "call": {
                    "id": "call_12345",
                    "customer": {"number": "+1234567890"},
                    "phoneNumber": {"number": "+0987654321"}
                }
            }
        }

    @pytest.fixture
    def sample_legacy_call_started_webhook(self):
        """Sample legacy call started webhook data."""
        return {
            "type": "call.started",
            "call": {
                "id": "call_12345",
                "customer": {"number": "+1234567890"},
                "phoneNumber": {"number": "+0987654321"}
            }
        }

    def test_send_voice_message_success(self, call_handler, sample_call_id):
        """Test successful voice message sending."""
        # Test voice message sending
        message = "Welcome to Voiceback. Thank you for calling. Goodbye."
        response = call_handler.send_voice_message(sample_call_id, message)

        # Verify response structure
        assert "assistant" in response
        assistant = response["assistant"]
        
        # Check first message
        assert assistant["firstMessage"] == message
        
        # Check model configuration
        assert assistant["model"]["provider"] == "openai"
        assert assistant["model"]["model"] == "gpt-4o-mini"
        assert len(assistant["model"]["messages"]) == 1
        assert assistant["model"]["messages"][0]["role"] == "system"
        assert "Voiceback" in assistant["model"]["messages"][0]["content"]
        
        # Check voice configuration
        assert assistant["voice"]["provider"] == "openai"
        assert assistant["voice"]["voiceId"] == "alloy"
        
        # Check call ending configuration
        assert assistant["silenceTimeoutSeconds"] == 10
        assert assistant["maxDurationSeconds"] == 30
        
        # Check call termination messages
        assert assistant["endCallMessage"] == "Thank you for calling Voiceback. Goodbye."
        assert "goodbye" in assistant["endCallPhrases"]

    def test_send_voice_message_unknown_call(self, call_handler, sample_call_id):
        """Test voice message sending for unknown call."""
        # Test sending message to unknown call - current implementation allows this
        response = call_handler.send_voice_message(sample_call_id, "Test message")
        
        # Verify assistant configuration is still returned (new behavior)
        assert "assistant" in response
        assert response["assistant"]["firstMessage"] == "Test message"

    def test_assistant_request_webhook_handling(self, call_handler, sample_assistant_request_webhook):
        """Test handling of assistant-request webhook."""
        response = call_handler.handle_webhook(sample_assistant_request_webhook)
        
        # Verify assistant configuration is returned
        assert "assistant" in response
        assert response["assistant"]["firstMessage"] == "Welcome to Voiceback. Thank you for calling. Goodbye."
        
        # Verify call is added to active calls
        call_id = sample_assistant_request_webhook["message"]["call"]["id"]
        assert call_id in call_handler.active_calls
        
        call_info = call_handler.active_calls[call_id]
        assert call_info["id"] == call_id
        assert call_info["status"] == "active"
        assert call_info["from_number"] == "+1234567890"
        assert call_info["to_number"] == "+0987654321"

    def test_legacy_call_started_webhook_handling(self, call_handler, sample_legacy_call_started_webhook):
        """Test handling of legacy call.started webhook format."""
        response = call_handler.handle_webhook(sample_legacy_call_started_webhook)
        
        # Verify assistant configuration is returned
        assert "assistant" in response
        assert response["assistant"]["firstMessage"] == "Welcome to Voiceback. Thank you for calling. Goodbye."
        
        # Verify call is added to active calls
        call_id = sample_legacy_call_started_webhook["call"]["id"]
        assert call_id in call_handler.active_calls

    def test_call_termination_settings(self, call_handler, sample_call_id):
        """Test that call termination is properly configured."""
        # Get voice message response
        response = call_handler.send_voice_message(sample_call_id, "Goodbye message")
        assistant = response["assistant"]
        
        # Test call ending configuration
        assert assistant["silenceTimeoutSeconds"] == 10
        assert assistant["maxDurationSeconds"] == 30
        
        # Test system message instructs to end call gracefully
        system_message = assistant["model"]["messages"][0]["content"]
        assert "end the call gracefully" in system_message.lower()
        assert "voiceback" in system_message.lower()

    def test_voice_configuration_parameters(self, call_handler, sample_call_id):
        """Test that voice configuration has correct parameters."""
        # Get voice message response
        response = call_handler.send_voice_message(sample_call_id, "Test message")
        assistant = response["assistant"]
        
        # Test voice settings for warm, neutral tone
        voice_config = assistant["voice"]
        assert voice_config["provider"] == "openai"
        assert voice_config["voiceId"] == "alloy"  # Neutral, warm voice
        
        # Test model settings
        model_config = assistant["model"]
        assert model_config["provider"] == "openai"
        assert model_config["model"] == "gpt-4o-mini"

    def test_greeting_text_delivery(self, call_handler, sample_assistant_request_webhook):
        """Test that the correct greeting text is delivered."""
        response = call_handler.handle_webhook(sample_assistant_request_webhook)
        
        expected_greeting = "Welcome to Voiceback. Thank you for calling. Goodbye."
        assert response["assistant"]["firstMessage"] == expected_greeting

    def test_call_flow_complete_cycle(self, call_handler):
        """Test complete call flow from start to voice delivery."""
        # Simulate assistant request
        webhook_data = {
            "message": {
                "type": "assistant-request",
                "call": {
                    "id": "call_flow_test",
                    "customer": {"number": "+1111111111"},
                    "phoneNumber": {"number": "+2222222222"}
                }
            }
        }
        
        # Process webhook
        response = call_handler.handle_webhook(webhook_data)
        
        # Verify complete flow
        assert "assistant" in response
        assert response["assistant"]["firstMessage"] == "Welcome to Voiceback. Thank you for calling. Goodbye."
        
        # Verify call tracking
        assert "call_flow_test" in call_handler.active_calls
        call_info = call_handler.active_calls["call_flow_test"]
        assert call_info["status"] == "active"
        assert "started_at" in call_info

    def test_webhook_without_call_id(self, call_handler):
        """Test webhook handling when call ID is missing."""
        webhook_data = {
            "message": {
                "type": "assistant-request",
                "call": {}  # Missing call ID
            }
        }
        
        response = call_handler.handle_webhook(webhook_data)
        
        assert response["status"] == "error"
        assert response["message"] == "Missing call ID"

    def test_malformed_webhook_data(self, call_handler):
        """Test handling of malformed webhook data."""
        webhook_data = {
            "invalid": "data"
        }
        
        response = call_handler.handle_webhook(webhook_data)
        
        assert response["status"] == "error"
        assert response["message"] == "Missing call ID"

    @patch('call_handler.logger')
    def test_logging_voice_delivery(self, mock_logger, call_handler, sample_call_id):
        """Test that voice delivery is properly logged."""
        # Send voice message
        message = "Test logging message"
        call_handler.send_voice_message(sample_call_id, message)
        
        # Verify logging calls
        mock_logger.info.assert_called()
        
        # Check if log message contains expected content
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        voice_log_found = any("Voice message configured" in log for log in log_calls)
        assert voice_log_found

    def test_multiple_calls_independence(self, call_handler):
        """Test that multiple calls are handled independently."""
        # Setup two calls
        call_id_1 = "call_001"
        call_id_2 = "call_002"
        
        call_handler.active_calls[call_id_1] = {'id': call_id_1, 'status': 'active'}
        call_handler.active_calls[call_id_2] = {'id': call_id_2, 'status': 'active'}
        
        # Send different messages to each call
        response_1 = call_handler.send_voice_message(call_id_1, "Message for call 1")
        response_2 = call_handler.send_voice_message(call_id_2, "Message for call 2")
        
        # Verify each call gets correct message
        assert response_1["assistant"]["firstMessage"] == "Message for call 1"
        assert response_2["assistant"]["firstMessage"] == "Message for call 2"
        
        # Verify both calls are still active
        assert call_id_1 in call_handler.active_calls
        assert call_id_2 in call_handler.active_calls

    def test_voice_delivery_timing_target(self, call_handler, sample_call_id):
        """Test that voice delivery is optimized for 30-second interaction target."""
        # Test with standard greeting
        message = "Welcome to Voiceback. Thank you for calling. Goodbye."
        response = call_handler.send_voice_message(sample_call_id, message)
        
        # Verify call ends quickly after message
        assert response["assistant"]["silenceTimeoutSeconds"] == 10  # 10 seconds
        assert response["assistant"]["maxDurationSeconds"] == 30  # Total 30 seconds max
        
        # Verify message is concise (under typical TTS limits)
        assert len(message) < 200  # Reasonable length for quick delivery 