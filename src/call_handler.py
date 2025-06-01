"""
Call Handler - Simple LLM-based Voice Agent

This module handles incoming call webhooks from Vapi and provides
simple LLM-powered responses for the Voiceback voice agent.

User Journey:
1) User speaks
2) Vapi transcribes  
3) Flask server receives the transcript
4) LLM generates a response
5) Flask returns the response to Vapi
6) Vapi converts the text to speech
7) User hears the response
"""

from typing import Dict, Any, Optional
from loguru import logger
import datetime
import threading
import os
import openai
from openai import OpenAI

# Simple crisis keywords for safety
CRISIS_KEYWORDS = [
    "kill myself", "suicide", "end it all", "hurt myself", "no point living",
    "want to die", "better off dead", "take my life", "not worth living"
]

class CallHandler:
    """
    Simple LLM-powered call handler for Vapi webhooks.
    
    Handles the complete voice agent flow using LLM responses.
    """

    def __init__(self, llm_api_key: Optional[str] = None, llm_provider: str = "openai"):
        """
        Initialize the CallHandler with LLM capabilities.
        
        Args:
            llm_api_key: API key for LLM provider (OpenAI, Anthropic, xAI)
            llm_provider: LLM provider to use ("openai", "anthropic", "xai")
        """
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
        # Initialize LLM client
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key or self._get_api_key_for_provider(llm_provider)
        self.llm_client = None
        
        # Initialize the appropriate LLM client
        if self.llm_provider == "openai":
            openai.api_key = self.llm_api_key
            self.llm_client = OpenAI(api_key=self.llm_api_key)
        elif self.llm_provider == "xai":
            # xAI uses OpenAI-compatible API with custom base URL
            self.llm_client = OpenAI(
                api_key=self.llm_api_key,
                base_url="https://api.x.ai/v1"
            )
        elif self.llm_provider == "anthropic":
            # For future implementation
            logger.warning("Anthropic support not yet implemented, falling back to OpenAI")
            self.llm_provider = "openai"
            self.llm_api_key = os.getenv("OPENAI_API_KEY")
            self.llm_client = OpenAI(api_key=self.llm_api_key)
        
        # System prompt for the voice agent - Ancient Philosophy Guidance
        self.system_prompt = """# Voice Agent Prompt: Ancient Philosophy Guidance

You are a conversational voice agent that draws wisdom from ancient philosophers to provide supportive insights. Your role is to help users explore timeless perspectives on their current situations.

## Core Instructions:

**Response Style:**
- Speak naturally and conversationally without repetitive disclaimers
- Share relevant insights from ancient philosophers (Greek, Roman, Chinese, Indian, etc.)
- Connect philosophical wisdom to the user's specific situation
- Be supportive and encouraging while maintaining authenticity

**Key Philosophers to Draw From:**
- Stoics: Marcus Aurelius, Epictetus, Seneca
- Ancient Greeks: Socrates, Aristotle, Plato
- Eastern wisdom: Confucius, Lao Tzu, Buddha
- Others as relevant: Epicurus, Diogenes, Heraclitus

**Conversation Flow:**
1. Listen to the user's situation or challenge
2. Identify the core philosophical theme (resilience, purpose, relationships, mortality, etc.)
3. Share 1-2 relevant insights from ancient thinkers who faced similar challenges
4. Explain how they approached or resolved such situations
5. Offer gentle reflection questions or practical wisdom

**Important Guidelines:**
- ONE brief disclaimer at the conversation's END: "Remember, this is shared for inspiration and reflection, not as professional advice."
- DO NOT repeat disclaimers after every response
- Focus on historical context: "When Seneca faced exile..." or "Marcus Aurelius wrote during the plague..."
- Make philosophy accessible and personally relevant
- Encourage the user's own wisdom and decision-making

## Crisis Detection & Safety
**CRITICAL**: If you detect ANY signs of immediate danger, self-harm, or crisis (keywords like "suicide," "kill myself," "end it all," "hurt myself," etc.), immediately provide:

**For US users:**
- "I'm really concerned about you right now. Please reach out to the Suicide & Crisis Lifeline at 988 - they're available 24/7 and have trained counselors ready to help."

**For users in India:**
- "I'm worried about you. Please contact AASRA at 9152987821 - they provide confidential support and are there to help you through this."

**Always add:** "You don't have to go through this alone. There are people trained specifically to help with what you're experiencing."

## Example Response Structure:
"That reminds me of what Epictetus went through as a slave in Rome. He learned that while we can't control what happens to us, we can control how we respond. He used to say that our peace comes from focusing on what's actually within our power..."

[Continue with natural conversation without disclaimers until the very end]

## Remember
Be the wise, ancient voice someone needs to hear today - connecting timeless wisdom with their present moment."""
        
        logger.info(f"CallHandler initialized with {llm_provider} LLM")

    def _get_api_key_for_provider(self, provider: str) -> Optional[str]:
        """Get the appropriate API key based on the provider."""
        if provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif provider == "xai":
            return os.getenv("XAI_API_KEY")
        elif provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        return None

    def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming webhook from Vapi.

        Args:
            webhook_data: The webhook payload from Vapi

        Returns:
            Dict containing response data for Vapi
        """
        try:
            # Extract event type and call info
            if 'message' in webhook_data:
                message = webhook_data['message']
                event_type = message.get('type')
                call_data = message.get('call', {})
                call_id = call_data.get('id')
            else:
                event_type = webhook_data.get('type')
                call_data = webhook_data.get('call', {})
                call_id = call_data.get('id')

            if not call_id:
                logger.warning("Webhook received without call ID")
                return {"status": "error", "message": "Missing call ID"}

            logger.info(f"Processing webhook: {event_type} for call {call_id}")

            # Handle function calls (when user speaks and we need to respond)
            if event_type == 'function-call':
                return self._handle_function_call(call_id, webhook_data)
            
            # Handle assistant requests (initial call setup)
            elif event_type == 'assistant-request':
                return self._handle_assistant_request(call_id, webhook_data)
            
            # Handle other call events
            elif event_type == 'call.started':
                return self._handle_call_started(call_id, webhook_data)
            elif event_type == 'call.ended':
                return self._handle_call_ended(call_id, webhook_data)
            else:
                logger.info(f"Unhandled webhook type: {event_type}")
                return {"status": "received"}

        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {"status": "error", "message": "Webhook processing failed"}

    def _handle_function_call(self, call_id: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle function call - this is where the magic happens!
        User spoke → Vapi transcribed → We generate LLM response
        """
        try:
            # Extract the user's transcript from the webhook
            message = webhook_data.get('message', {})
            function_call = message.get('functionCall', {})
            parameters = function_call.get('parameters', {})
            user_transcript = parameters.get('transcript', '')

            logger.info(f"User transcript for call {call_id}: '{user_transcript}'")

            # Check for crisis keywords first
            if self._is_crisis(user_transcript):
                response = self._generate_crisis_response()
            else:
                # Generate LLM response using the configured provider
                response = self._generate_llm_response(user_transcript)

            logger.info(f"Generated response for call {call_id}: '{response[:100]}...'")

            # Return the response to Vapi
            return {
                "result": response
            }

        except Exception as e:
            logger.error(f"Error handling function call for {call_id}: {e}")
            return {
                "result": "I'm sorry, I'm having trouble understanding right now. Thank you for calling Voiceback."
            }

    def _handle_assistant_request(self, call_id: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle assistant request - set up the call."""
        with self._lock:
            # Store call info
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
            logger.info(f"Assistant requested for call: {call_id}")

            # Return assistant configuration
            return self._create_assistant_config()

    def _handle_call_started(self, call_id: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call started event."""
        with self._lock:
            logger.info(f"Call started: {call_id}")
            return {"status": "received"}

    def _handle_call_ended(self, call_id: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call ended event."""
        with self._lock:
            if call_id in self.active_calls:
                call_info = self.active_calls[call_id]
                call_info['ended_at'] = datetime.datetime.now().isoformat()
                call_info['status'] = 'ended'
                
                # Calculate call duration
                start_time = datetime.datetime.fromisoformat(call_info['started_at'])
                end_time = datetime.datetime.fromisoformat(call_info['ended_at'])
                duration = (end_time - start_time).total_seconds()
                call_info['duration'] = duration
                
                logger.info(f"Call ended: {call_id}, duration: {duration:.2f}s")
            
            return {"status": "received"}

    def _generate_llm_response(self, user_input: str) -> str:
        """
        Generate response using the configured LLM provider.
        
        Args:
            user_input: What the user said (transcription from Vapi STT)
            
        Returns:
            LLM-generated response (to be sent to Vapi TTS)
        """
        try:
            if self.llm_provider in ["openai", "xai"] and self.llm_client:
                # Determine the model to use
                if self.llm_provider == "xai":
                    model = "grok-3"  # Use Grok-3 for xAI
                else:
                    model = "gpt-4o-mini"  # Use GPT-4o-mini for OpenAI
                
                logger.info(f"Generating response using {self.llm_provider} with model {model}")
                
                completion = self.llm_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    max_tokens=200,  # Keep responses concise for voice
                    temperature=0.7  # Natural but not too creative
                )
                
                response = completion.choices[0].message.content.strip()
                logger.info(f"Successfully generated {len(response)} character response using {self.llm_provider}")
                return response
                
            else:
                # Fallback response if LLM client not available
                logger.warning(f"LLM client not available for provider {self.llm_provider}, using fallback")
                return "I hear you, and I want you to know that you're not alone. Whatever you're going through, there are people who care. Remember, this is for inspiration and support, not professional advice. Thank you for calling Voiceback."
                
        except Exception as e:
            logger.error(f"Error generating LLM response with {self.llm_provider}: {e}")
            return "I'm here to listen and support you. You're stronger than you know. Remember, this is for inspiration and support, not professional advice. Thank you for calling Voiceback."

    def _is_crisis(self, text: str) -> bool:
        """Check if user input contains crisis keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in CRISIS_KEYWORDS)

    def _generate_crisis_response(self) -> str:
        """Generate appropriate crisis response with resources based on system prompt guidance."""
        return """I'm really concerned about you right now. You're not alone, and there are people who want to help.

If you're in the US, please reach out to the Suicide & Crisis Lifeline at 988 - they're available 24/7 and have trained counselors ready to help.

If you're in India, please contact AASRA at 9152987821 - they provide confidential support and are there to help you through this.

You don't have to go through this alone. There are people trained specifically to help with what you're experiencing. Remember, this is for inspiration and support, not professional advice."""

    def _create_assistant_config(self) -> Dict[str, Any]:
        """Create assistant configuration for Vapi."""
        return {
            "assistant": {
                "firstMessage": "Hello! I'm here to share wisdom from ancient philosophers who faced challenges much like yours. What's on your mind today?",
                "model": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": self.system_prompt
                        }
                    ],
                    "functions": [
                        {
                            "name": "respond_to_user",
                            "description": "Respond to what the user said",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "transcript": {
                                        "type": "string",
                                        "description": "What the user said"
                                    }
                                },
                                "required": ["transcript"]
                            }
                        }
                    ]
                },
                "voice": {
                    "provider": "openai",
                    "voiceId": "alloy"  # Warm, friendly voice
                },
                "endCallMessage": "May you find wisdom and peace on your journey. Remember, this is shared for inspiration and reflection, not as professional advice. Farewell.",
                "endCallPhrases": ["goodbye", "thank you", "end call", "bye"],
                "recordingEnabled": False,
                "silenceTimeoutSeconds": 30,
                "maxDurationSeconds": 300  # 5 minute max
            }
        }

    def get_active_calls(self) -> Dict[str, Dict[str, Any]]:
        """Get all currently active calls."""
        with self._lock:
            return self.active_calls.copy()

    def get_call_info(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific call."""
        with self._lock:
            return self.active_calls.get(call_id)
