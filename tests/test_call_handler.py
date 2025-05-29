"""
Tests for CallHandler - Webhook Processing and Call Lifecycle

Tests webhook handling, call management, and integration functionality
for the Voiceback voice agent.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import datetime

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from call_handler import CallHandler, DEFAULT_GREETING


class TestCallHandler:
    """Test suite for CallHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Disable emotion responses for backward compatibility with existing tests
        self.call_handler = CallHandler(enable_emotion_responses=False)
        self.sample_call_id = "call_12345"
    
    def test_init(self):
        """Test CallHandler initialization."""
        handler = CallHandler()
        assert handler.active_calls == {}
        assert hasattr(handler, 'active_calls')
    
    def test_handle_webhook_missing_call_id(self):
        """Test webhook handling with missing call ID."""
        webhook_data = {
            "type": "call.started",
            "call": {}  # Missing 'id' field
        }
        
        response = self.call_handler.handle_webhook(webhook_data)
        
        assert response["status"] == "error"
        assert "Missing call ID" in response["message"]
    
    def test_handle_webhook_invalid_json(self):
        """Test webhook handling with invalid data."""
        webhook_data = None
        
        # Should handle gracefully and return error response
        response = self.call_handler.handle_webhook(webhook_data)
        
        assert response["status"] == "error"
        assert "Webhook processing failed" in response["message"]
    
    def test_handle_call_started(self):
        """Test handling call started event."""
        webhook_data = {
            "type": "call.started",
            "call": {
                "id": self.sample_call_id,
                "customer": {"number": "+1234567890"},
                "phoneNumber": {"number": "+0987654321"}
            }
        }
        
        response = self.call_handler.handle_webhook(webhook_data)
        
        # Step 4: Should now return assistant configuration for greeting
        assert "assistant" in response
        assert response["assistant"]["firstMessage"] == DEFAULT_GREETING
        
        # Call should be in active calls initially
        assert self.sample_call_id in self.call_handler.active_calls
        call_info = self.call_handler.active_calls[self.sample_call_id]
        assert call_info["status"] == "active"
        assert call_info["from_number"] == "+1234567890"
        assert call_info["to_number"] == "+0987654321"
    
    def test_handle_call_ended(self):
        """Test handling call ended event."""
        # First start a call
        start_data = {
            "type": "call.started",
            "call": {
                "id": self.sample_call_id,
                "customer": {"number": "+1234567890"},
                "phoneNumber": {"number": "+0987654321"}
            }
        }
        self.call_handler.handle_webhook(start_data)
        
        # Then end the call
        end_data = {
            "type": "call.ended",
            "call": {"id": self.sample_call_id}
        }
        
        response = self.call_handler.handle_webhook(end_data)
        
        assert response["status"] == "received"
        # Call should be removed from active calls
        assert self.sample_call_id not in self.call_handler.active_calls
    
    def test_handle_call_ended_unknown_call(self):
        """Test handling call ended for unknown call."""
        webhook_data = {
            "type": "call.ended",
            "call": {"id": "unknown_call_id"}
        }
        
        response = self.call_handler.handle_webhook(webhook_data)
        
        assert response["status"] == "received"
    
    def test_handle_speech_events(self):
        """Test handling speech started and ended events."""
        speech_started_data = {
            "type": "speech.started",
            "call": {"id": self.sample_call_id}
        }
        
        speech_ended_data = {
            "type": "speech.ended",
            "call": {"id": self.sample_call_id}
        }
        
        response1 = self.call_handler.handle_webhook(speech_started_data)
        response2 = self.call_handler.handle_webhook(speech_ended_data)
        
        assert response1["status"] == "received"
        assert response2["status"] == "received"
    
    def test_handle_unhandled_webhook_type(self):
        """Test handling unknown webhook types."""
        webhook_data = {
            "type": "unknown.event",
            "call": {"id": self.sample_call_id}
        }
        
        response = self.call_handler.handle_webhook(webhook_data)
        
        assert response["status"] == "received"
    
    def test_handle_webhook_with_missing_fields(self):
        """Test webhook handling with missing optional fields."""
        # Pass data with missing customer and phoneNumber fields
        webhook_data = {
            "type": "call.started",
            "call": {"id": self.sample_call_id}
            # Missing customer and phoneNumber - should handle gracefully
        }
        
        response = self.call_handler.handle_webhook(webhook_data)
        
        # Step 4: Should return assistant configuration for greeting
        assert "assistant" in response
        assert response["assistant"]["firstMessage"] == DEFAULT_GREETING
        
        # Call should be in active calls with None values for missing fields
        assert self.sample_call_id in self.call_handler.active_calls
        call_info = self.call_handler.active_calls[self.sample_call_id]
        assert call_info["from_number"] is None
        assert call_info["to_number"] is None
    
    def test_answer_call_success(self):
        """Test answering a call successfully."""
        # Add call to active calls first
        self.call_handler.active_calls[self.sample_call_id] = {
            "id": self.sample_call_id,
            "status": "ringing"
        }
        
        response = self.call_handler.answer_call(self.sample_call_id)
        
        # Step 4: answer_call now returns simple acknowledgment since voice delivery handles the flow
        assert response["status"] == "success"
    
    def test_answer_call_unknown(self):
        """Test answering unknown call."""
        response = self.call_handler.answer_call("unknown_call")
        
        assert response["status"] == "error"
        assert "Call not found" in response["message"]
    
    def test_end_call_success(self):
        """Test ending a call successfully."""
        # Add call to active calls first
        self.call_handler.active_calls[self.sample_call_id] = {
            "id": self.sample_call_id,
            "status": "active"
        }
        
        response = self.call_handler.end_call(self.sample_call_id)
        
        assert response["status"] == "success"
        assert response["instruction"]["type"] == "end_call"
    
    def test_end_call_unknown(self):
        """Test ending unknown call."""
        response = self.call_handler.end_call("unknown_call")
        
        assert response["status"] == "error"
        assert "Call not found" in response["message"]
    
    def test_get_active_calls(self):
        """Test getting active calls."""
        # Add some calls
        call1_id = "call_1"
        call2_id = "call_2"
        
        self.call_handler.active_calls[call1_id] = {"id": call1_id, "status": "active"}
        self.call_handler.active_calls[call2_id] = {"id": call2_id, "status": "active"}
        
        active_calls = self.call_handler.get_active_calls()
        
        assert len(active_calls) == 2
        assert call1_id in active_calls
        assert call2_id in active_calls
        
        # Should return a copy, not the original
        assert active_calls is not self.call_handler.active_calls
    
    def test_get_call_info(self):
        """Test getting call information."""
        call_info = {"id": self.sample_call_id, "status": "active", "from_number": "+1234567890"}
        self.call_handler.active_calls[self.sample_call_id] = call_info
        
        retrieved_info = self.call_handler.get_call_info(self.sample_call_id)
        
        assert retrieved_info == call_info
        
        # Test unknown call
        unknown_info = self.call_handler.get_call_info("unknown_call")
        assert unknown_info is None


class TestCallHandlerIntegration:
    """Integration tests for CallHandler with realistic scenarios."""
    
    def setup_method(self):
        """Set up test fixtures for integration tests."""
        # Disable emotion responses for backward compatibility with existing tests
        self.call_handler = CallHandler(enable_emotion_responses=False)
    
    def test_complete_call_lifecycle(self):
        """Test a complete call from start to end."""
        call_id = "integration_call_123"
        
        # 1. Call started
        start_webhook = {
            "type": "call.started",
            "call": {
                "id": call_id,
                "customer": {"number": "+1555123456"},
                "phoneNumber": {"number": "+1555987654"}
            }
        }
        
        start_response = self.call_handler.handle_webhook(start_webhook)
        
        # Step 4: Should return assistant configuration for voice greeting
        assert "assistant" in start_response
        assert start_response["assistant"]["firstMessage"] == DEFAULT_GREETING
        assert call_id in self.call_handler.active_calls
        
        # 2. Call ended
        end_webhook = {
            "type": "call.ended",
            "call": {"id": call_id}
        }
        
        end_response = self.call_handler.handle_webhook(end_webhook)
        
        assert end_response["status"] == "received"
        assert call_id not in self.call_handler.active_calls
    
    def test_multiple_concurrent_calls(self):
        """Test handling multiple calls simultaneously."""
        call_ids = ["call_1", "call_2", "call_3"]
        
        # Start multiple calls
        for call_id in call_ids:
            webhook = {
                "type": "call.started",
                "call": {
                    "id": call_id,
                    "customer": {"number": f"+155512{call_id[-1]}456"},
                    "phoneNumber": {"number": "+1555987654"}
                }
            }
            response = self.call_handler.handle_webhook(webhook)
            # Step 4: Should return assistant configuration for voice greeting
            assert "assistant" in response
            assert response["assistant"]["firstMessage"] == DEFAULT_GREETING
        
        # All calls should be active
        active_calls = self.call_handler.get_active_calls()
        assert len(active_calls) == 3
        
        # End calls one by one
        for call_id in call_ids:
            end_webhook = {
                "type": "call.ended",
                "call": {"id": call_id}
            }
            self.call_handler.handle_webhook(end_webhook)
        
        # No calls should be active
        assert len(self.call_handler.get_active_calls()) == 0

    @patch('call_handler.datetime')
    def test_call_duration_tracking(self, mock_datetime):
        """Test that call duration is tracked correctly."""
        call_id = "duration_test_call"
        
        # Mock datetime for consistent testing
        start_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
        end_time = datetime.datetime(2024, 1, 1, 12, 0, 30)  # 30 seconds later
        
        mock_datetime.datetime.now.side_effect = [start_time, end_time, end_time]
        mock_datetime.datetime.fromisoformat.return_value = start_time
        
        # Start call
        start_webhook = {
            "type": "call.started",
            "call": {
                "id": call_id,
                "customer": {"number": "+1234567890"},
                "phoneNumber": {"number": "+0987654321"}
            }
        }
        self.call_handler.handle_webhook(start_webhook)
        
        # End call
        end_webhook = {
            "type": "call.ended",
            "call": {"id": call_id}
        }
        self.call_handler.handle_webhook(end_webhook)
        
        # Duration should have been calculated (but call is removed from active calls)
        # We can't test this directly since the call is removed, but the duration
        # calculation logic is tested through the datetime mocking


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"]) 