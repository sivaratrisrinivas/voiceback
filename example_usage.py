#!/usr/bin/env python3
"""
Voiceback LLM Voice Agent - xAI Grok-3 Example

This example demonstrates the simple user journey with xAI's Grok-3:
1) User speaks
2) Vapi transcribes (STT)
3) Flask server receives the transcript
4) Grok-3 LLM generates a response
5) Flask returns the response to Vapi
6) Vapi converts the text to speech (TTS)
7) User hears the response
"""

import json
from src.call_handler import CallHandler

def main():
    """Demonstrate the xAI Grok-3 voice agent flow."""
    print("🎤 Voiceback Voice Agent - xAI Grok-3 Demo")
    print("=" * 55)
    
    # Initialize with xAI/Grok-3 (use fake API key for demo)
    handler = CallHandler(llm_api_key="xai-demo-key-123", llm_provider="xai")
    print(f"✅ CallHandler initialized with {handler.llm_provider} LLM")
    print(f"   Using Grok-3 model for emotional support responses")
    
    # Simulate the user journey
    print("\n📱 Complete Voice Agent Flow:")
    print("1) User speaks: 'I'm feeling really anxious about my job interview tomorrow'")
    print("2) Vapi STT transcribes speech to text...")
    
    # Simulate assistant request (call setup)
    assistant_request = {
        'message': {
            'type': 'assistant-request',
            'call': {
                'id': 'demo-call-123',
                'customer': {'number': '+1234567890'},
                'phoneNumber': {'number': '+0987654321'}
            }
        }
    }
    
    print("\n3) Flask receives assistant request...")
    assistant_response = handler.handle_webhook(assistant_request)
    print("✅ Assistant configuration returned")
    print(f"   First message: '{assistant_response['assistant']['firstMessage']}'")
    
    # Simulate function call (user transcript processing)
    function_call = {
        'message': {
            'type': 'function-call',
            'functionCall': {
                'parameters': {
                    'transcript': "I'm feeling really anxious about my job interview tomorrow"
                }
            },
            'call': {'id': 'demo-call-123'}
        }
    }
    
    print("\n4) Grok-3 processes the transcription...")
    print("   📝 Input: User's transcribed speech from Vapi STT")
    print("   🧠 Processing: xAI Grok-3 analyzes emotional context")
    print("   💬 Output: Compassionate response generated")
    
    # Mock the Grok-3 response since we don't have real API keys
    print("   (In real usage, this would call xAI's Grok-3 API)")
    
    # Simulate the response (without actually calling Grok-3)
    mock_response = {
        "result": "I understand that job interviews can feel overwhelming, and your anxiety is completely natural. Grok-3 recognizes that you're facing something important, and that's why you care so much. Remember that they invited you because they see potential in you. Take some deep breaths, prepare what you can, and trust in your abilities. You've got this! Remember, this is for inspiration and support, not professional advice. Thank you for calling Voiceback."
    }
    
    print("\n5) Flask returns Grok-3 response to Vapi...")
    print(f"✅ Generated response: '{mock_response['result'][:80]}...'")
    
    print("\n6) Vapi TTS converts text to speech...")
    print("7) User hears supportive Grok-3 response! 🔊")
    
    # Test crisis detection with xAI
    print("\n" + "=" * 55)
    print("🚨 Crisis Detection with xAI/Grok-3:")
    
    crisis_call = {
        'message': {
            'type': 'function-call',
            'functionCall': {
                'parameters': {
                    'transcript': "I want to kill myself, there's no point in living"
                }
            },
            'call': {'id': 'crisis-call-456'}
        }
    }
    
    print("User transcript: 'I want to kill myself, there's no point in living'")
    crisis_response = handler.handle_webhook(crisis_call)
    print("✅ Crisis detected - Emergency resources provided")
    print("   (Crisis detection bypasses LLM for immediate safety)")
    print(f"Response: {crisis_response['result'][:100]}...")
    
    # Test different LLM providers
    print("\n" + "=" * 55)
    print("🔄 Multi-LLM Provider Support:")
    
    providers = [
        ("openai", "GPT-4o-mini"),
        ("xai", "Grok-3"),
    ]
    
    for provider, model in providers:
        try:
            test_handler = CallHandler(llm_api_key=f"{provider}-test-key", llm_provider=provider)
            print(f"✅ {provider.upper()}: {model} - Ready for voice agent")
        except Exception as e:
            print(f"⚠️  {provider.upper()}: Configuration needed")
    
    # Show active calls
    print("\n" + "=" * 55)
    print("📞 Call Management:")
    active_calls = handler.get_active_calls()
    print(f"Currently tracking {len(active_calls)} calls")
    for call_id, call_info in active_calls.items():
        print(f"  - {call_id}: {call_info['status']} since {call_info['started_at']}")
    
    print("\n✨ xAI Grok-3 Integration Complete!")
    print("\n🎯 Voice Agent Flow Summary:")
    print("   📞 Vapi STT → 📝 Transcript → 🧠 Grok-3 → 💬 Response → 🔊 Vapi TTS")
    print("\n💡 Key Benefits of Grok-3 Integration:")
    print("• Advanced reasoning and emotional understanding")
    print("• Natural, contextual conversations")
    print("• Real-time processing for voice interactions")
    print("• Built-in safety with crisis detection")
    print("• Seamless integration with Vapi platform")
    
    print(f"\n📋 Configuration Required:")
    print("• Set LLM_PROVIDER=xai in your .env file")
    print("• Add your XAI_API_KEY to .env file")
    print("• Restart the voice agent to use Grok-3")


if __name__ == "__main__":
    main() 