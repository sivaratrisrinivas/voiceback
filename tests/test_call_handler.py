"""
Tests for CallHandler - Simple LLM-based Voice Agent

Tests the simplified webhook handling and LLM integration for voice responses.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import datetime
from src.call_handler import CallHandler


class TestCallHandler:
    """Test the simple LLM-based CallHandler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = CallHandler(llm_api_key="test-key-123")

    def test_initialization(self):
        """Test CallHandler initialization."""
        assert self.handler.llm_provider == "openai"
        assert self.handler.llm_api_key == "test-key-123"
        assert isinstance(self.handler.active_calls, dict)
        assert len(self.handler.active_calls) == 0
        assert self.handler.llm_client is not None

    def test_initialization_with_xai(self):
        """Test CallHandler initialization with xAI provider."""
        handler = CallHandler(llm_api_key="xai-test-key", llm_provider="xai")
        assert handler.llm_provider == "xai"
        assert handler.llm_api_key == "xai-test-key"
        assert handler.llm_client is not None

    def test_initialization_with_env_key(self):
        """Test initialization uses environment variable if no key provided."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'env-key-456'}):
            handler = CallHandler()
            assert handler.llm_api_key == 'env-key-456'

    def test_initialization_with_xai_env_key(self):
        """Test initialization with xAI using environment variable."""
        with patch.dict('os.environ', {'XAI_API_KEY': 'xai-env-key-789'}):
            handler = CallHandler(llm_provider="xai")
            assert handler.llm_api_key == 'xai-env-key-789'
            assert handler.llm_provider == "xai"

    def test_handle_webhook_assistant_request(self):
        """Test handling assistant request webhook."""
        webhook_data = {
            'message': {
                'type': 'assistant-request',
                'call': {
                    'id': 'call-123',
                    'customer': {'number': '+1234567890'},
                    'phoneNumber': {'number': '+0987654321'}
                }
            }
        }

        result = self.handler.handle_webhook(webhook_data)

        # Check assistant config is returned
        assert 'assistant' in result
        assert result['assistant']['firstMessage']
        assert result['assistant']['model']['provider'] == 'openai'
        
        # Check call is tracked
        assert 'call-123' in self.handler.active_calls
        call_info = self.handler.active_calls['call-123']
        assert call_info['id'] == 'call-123'
        assert call_info['status'] == 'active'

    def test_handle_function_call_normal_response(self):
        """Test handling function call with normal user input."""
        # Mock the LLM client response for the new architecture
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "I understand you're feeling anxious. That's completely normal before an interview. Remember, this is for inspiration and support, not professional advice. Thank you for calling Voiceback."
        
        with patch.object(self.handler.llm_client, 'chat') as mock_chat:
            mock_chat.completions.create.return_value = mock_completion

            webhook_data = {
                'message': {
                    'type': 'function-call',
                    'functionCall': {
                        'parameters': {
                            'transcript': "I'm really nervous about my job interview tomorrow"
                        }
                    },
                    'call': {'id': 'call-123'}
                }
            }

            result = self.handler.handle_webhook(webhook_data)

            # Check response format
            assert 'result' in result
            assert 'anxious' in result['result'] or 'nervous' in result['result']
            assert 'Thank you for calling Voiceback' in result['result']

            # Check LLM client was called correctly
            mock_chat.completions.create.assert_called_once()
            call_args = mock_chat.completions.create.call_args
            assert call_args[1]['model'] == 'gpt-4o-mini'
            assert len(call_args[1]['messages']) == 2
            assert call_args[1]['messages'][0]['role'] == 'system'
            assert call_args[1]['messages'][1]['role'] == 'user'

    def test_handle_function_call_crisis_response(self):
        """Test handling function call with crisis keywords."""
        webhook_data = {
            'message': {
                'type': 'function-call',
                'functionCall': {
                    'parameters': {
                        'transcript': "I want to kill myself, there's no point"
                    }
                },
                'call': {'id': 'call-123'}
            }
        }

        result = self.handler.handle_webhook(webhook_data)

        # Check crisis response
        assert 'result' in result
        assert '988' in result['result']  # US suicide hotline
        assert 'AASRA' in result['result']  # Indian crisis line
        assert 'not alone' in result['result']

    def test_handle_call_started(self):
        """Test handling call started event."""
        webhook_data = {
            'type': 'call.started',
            'call': {
                'id': 'call-456',
                'customer': {'number': '+1234567890'}
            }
        }

        result = self.handler.handle_webhook(webhook_data)
        
        assert result == {"status": "received"}

    def test_handle_call_ended(self):
        """Test handling call ended event."""
        # First set up an active call
        call_id = 'call-789'
        self.handler.active_calls[call_id] = {
            'id': call_id,
            'started_at': datetime.datetime.now().isoformat(),
            'status': 'active'
        }

        webhook_data = {
            'type': 'call.ended',
            'call': {'id': call_id}
        }

        result = self.handler.handle_webhook(webhook_data)
        
        assert result == {"status": "received"}
        
        # Check call info was updated
        call_info = self.handler.active_calls[call_id]
        assert call_info['status'] == 'ended'
        assert 'ended_at' in call_info
        assert 'duration' in call_info

    def test_handle_webhook_missing_call_id(self):
        """Test handling webhook without call ID."""
        webhook_data = {
            'message': {
                'type': 'assistant-request',
                'call': {}  # No id field
            }
        }

        result = self.handler.handle_webhook(webhook_data)
        
        assert result['status'] == 'error'
        assert 'Missing call ID' in result['message']

    def test_handle_webhook_unknown_type(self):
        """Test handling webhook with unknown event type."""
        webhook_data = {
            'message': {
                'type': 'unknown-event',
                'call': {'id': 'call-999'}
            }
        }

        result = self.handler.handle_webhook(webhook_data)
        
        assert result == {"status": "received"}

    def test_is_crisis_detection(self):
        """Test crisis keyword detection."""
        # Test positive cases
        assert self.handler._is_crisis("I want to kill myself")
        assert self.handler._is_crisis("thinking about suicide")
        assert self.handler._is_crisis("I'm going to end it all")
        assert self.handler._is_crisis("no point living anymore")
        
        # Test negative cases
        assert not self.handler._is_crisis("I'm feeling sad today")
        assert not self.handler._is_crisis("having a bad day")
        assert not self.handler._is_crisis("need some support")

    def test_generate_crisis_response(self):
        """Test crisis response generation."""
        response = self.handler._generate_crisis_response()
        
        assert '988' in response  # US hotline
        assert 'AASRA' in response  # Indian hotline
        assert 'not alone' in response
        assert 'trained specifically to help' in response

    def test_generate_llm_response_success(self):
        """Test successful LLM response generation."""
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Great response from AI"
        
        with patch.object(self.handler.llm_client, 'chat') as mock_chat:
            mock_chat.completions.create.return_value = mock_completion
            
            result = self.handler._generate_llm_response("test input")
            
            assert result == "Great response from AI"
            mock_chat.completions.create.assert_called_once()

    @patch('openai.ChatCompletion.create')
    def test_generate_llm_response_failure(self, mock_openai):
        """Test LLM response generation with API failure."""
        mock_openai.side_effect = Exception("API Error")

        result = self.handler._generate_llm_response("test input")
        
        # Should return fallback response
        assert "I'm here to listen and support you" in result
        assert "Thank you for calling Voiceback" in result

    def test_get_active_calls(self):
        """Test getting active calls."""
        # Add some test calls
        self.handler.active_calls['call-1'] = {'id': 'call-1', 'status': 'active'}
        self.handler.active_calls['call-2'] = {'id': 'call-2', 'status': 'active'}

        active_calls = self.handler.get_active_calls()
        
        assert len(active_calls) == 2
        assert 'call-1' in active_calls
        assert 'call-2' in active_calls
        
        # Should be a copy, not reference
        active_calls['call-3'] = {'id': 'call-3'}
        assert 'call-3' not in self.handler.active_calls

    def test_get_call_info(self):
        """Test getting specific call info."""
        test_call = {'id': 'call-test', 'status': 'active'}
        self.handler.active_calls['call-test'] = test_call

        # Existing call
        result = self.handler.get_call_info('call-test')
        assert result == test_call

        # Non-existing call
        result = self.handler.get_call_info('call-nonexistent')
        assert result is None

    def test_create_assistant_config(self):
        """Test assistant configuration creation."""
        config = self.handler._create_assistant_config()
        
        assert 'assistant' in config
        assistant = config['assistant']
        
        # Check required fields
        assert 'firstMessage' in assistant
        assert 'model' in assistant
        assert 'voice' in assistant
        assert 'endCallMessage' in assistant
        
        # Check model configuration
        model = assistant['model']
        assert model['provider'] == 'openai'
        assert model['model'] == 'gpt-4o-mini'
        assert 'functions' in model
        assert len(model['functions']) == 1
        
        # Check function definition
        func = model['functions'][0]
        assert func['name'] == 'respond_to_user'
        assert 'transcript' in func['parameters']['properties']

    def test_legacy_webhook_format(self):
        """Test handling legacy webhook format."""
        webhook_data = {
            'type': 'call.started',  # Legacy format without 'message' wrapper
            'call': {
                'id': 'call-legacy',
                'customer': {'number': '+1234567890'}
            }
        }

        result = self.handler.handle_webhook(webhook_data)
        
        assert result == {"status": "received"}

    @patch('openai.ChatCompletion.create')
    def test_handle_function_call_error_handling(self, mock_openai):
        """Test function call error handling."""
        mock_openai.side_effect = Exception("API Error")

        webhook_data = {
            'message': {
                'type': 'function-call',
                'functionCall': {
                    'parameters': {
                        'transcript': "test input"
                    }
                },
                'call': {'id': 'call-error'}
            }
        }

        result = self.handler.handle_webhook(webhook_data)

        # Should handle error gracefully
        assert 'result' in result
        assert "I'm here to listen and support you" in result['result']

    def test_handle_function_call_missing_transcript(self):
        """Test function call with missing transcript."""
        webhook_data = {
            'message': {
                'type': 'function-call',
                'functionCall': {
                    'parameters': {}  # No transcript
                },
                'call': {'id': 'call-no-transcript'}
            }
        }

        result = self.handler.handle_webhook(webhook_data)

        # Should handle gracefully with empty transcript
        assert 'result' in result

    def test_generate_llm_response_with_xai(self):
        """Test LLM response generation with xAI/Grok-3."""
        # Create xAI handler
        xai_handler = CallHandler(llm_api_key="xai-test-key", llm_provider="xai")
        
        # Mock the xAI client response
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Grok-3 generated response with empathy and support. Remember, this is for inspiration and support, not professional advice. Thank you for calling Voiceback."
        
        with patch.object(xai_handler.llm_client, 'chat') as mock_chat:
            mock_chat.completions.create.return_value = mock_completion
            
            result = xai_handler._generate_llm_response("I'm feeling anxious about my presentation")
            
            # Verify the response
            assert "Grok-3 generated response" in result
            assert "Thank you for calling Voiceback" in result
            
            # Verify Grok-3 model was used
            mock_chat.completions.create.assert_called_once()
            call_args = mock_chat.completions.create.call_args
            assert call_args[1]['model'] == 'grok-3'
            assert len(call_args[1]['messages']) == 2
            assert call_args[1]['messages'][0]['role'] == 'system'
            assert call_args[1]['messages'][1]['role'] == 'user'


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"]) 