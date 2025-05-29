"""
Response builder for formatting historical quotes into voice responses.

This module creates the final voice response following the template:
"It sounds like you're feeling [emotion]. [Acknowledgment]. You remind me of 
[Historical Figure], [context line]. [pause] '[quote]' [encouragement line]"
"""

import random
from typing import Dict, Optional
from loguru import logger


class ResponseBuilder:
    """Builds formatted voice responses from emotion data and historical quotes."""
    
    # Emotion-specific acknowledgments
    EMOTION_ACKNOWLEDGMENTS = {
        "anxiety": [
            "That's completely understandable.",
            "Many people experience this feeling.",
            "You're not alone in feeling this way.",
            "It's natural to feel anxious sometimes."
        ],
        "sadness": [
            "I can hear the heaviness in that.",
            "Sadness is a natural part of the human experience.", 
            "It's okay to feel this deeply.",
            "Your feelings are valid and important."
        ],
        "frustration": [
            "That frustration sounds really difficult.",
            "It's clear this has been weighing on you.",
            "Frustration can be so overwhelming.",
            "I can understand why you'd feel that way."
        ],
        "uncertainty": [
            "Uncertainty can feel unsettling.",
            "Not knowing what's ahead is challenging.",
            "It's hard when the path isn't clear.",
            "Feeling uncertain is part of being human."
        ],
        "overwhelm": [
            "That sounds like so much to handle.",
            "Being overwhelmed is exhausting.",
            "It's understandable to feel swamped.",
            "Sometimes life can feel like too much."
        ]
    }
    
    # Crisis response (special case)
    CRISIS_RESPONSE = (
        "I'm truly sorry you're feeling this way. Voiceback is not equipped to help "
        "with urgent emotional crises, but you're not alone. Please consider reaching "
        "out to a professional or calling a helpline such as 988 in the US or "
        "1-833-456-4566 in Canada. Take care of yourself."
    )
    
    # Default fallback if emotion not found
    DEFAULT_ACKNOWLEDGMENT = "I hear you."
    
    def __init__(self):
        """Initialize the response builder."""
        pass
    
    def build_response(self, emotion: str, response_data: Optional[Dict], 
                      user_input: str = "") -> str:
        """
        Build a complete voice response from emotion and quote data.
        
        Args:
            emotion: The detected emotion
            response_data: Dictionary containing figure, context_line, quote, encouragement_line
            user_input: Original user input (for logging)
            
        Returns:
            Formatted voice response string ready for text-to-speech
        """
        # Handle crisis case
        if emotion == "crisis":
            logger.warning(f"Building crisis response for input: '{user_input}'")
            return self.CRISIS_RESPONSE
        
        # Handle missing response data
        if not response_data:
            logger.error(f"No response data available for emotion '{emotion}'")
            return self._build_fallback_response(emotion)
        
        try:
            # Extract components
            figure = response_data.get("figure", "a wise person")
            context_line = response_data.get("context_line", "who understood life's challenges")
            quote = response_data.get("quote", "Every moment is a fresh beginning.")
            encouragement_line = response_data.get("encouragement_line", "You have strength within you.")
            
            # Get acknowledgment for this emotion
            acknowledgment = self._get_acknowledgment(emotion)
            
            # Build the response following the spec template
            response = (
                f"It sounds like you're feeling {emotion}. {acknowledgment} "
                f"You remind me of {figure}, {context_line}. "
                f"[pause] '{quote}' {encouragement_line}"
            )
            
            logger.info(f"Built response for emotion '{emotion}' using figure '{figure}'")
            logger.debug(f"Full response: {response}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error building response for emotion '{emotion}': {e}")
            return self._build_fallback_response(emotion)
    
    def build_voice_optimized_response(self, emotion: str, response_data: Optional[Dict],
                                     user_input: str = "") -> Dict[str, str]:
        """
        Build a voice-optimized response with separate components for better TTS control.
        
        Args:
            emotion: The detected emotion
            response_data: Dictionary containing figure, context_line, quote, encouragement_line
            user_input: Original user input (for logging)
            
        Returns:
            Dictionary with separate components: intro, quote, conclusion
        """
        # Handle crisis case
        if emotion == "crisis":
            return {
                "intro": "",
                "quote": "",
                "conclusion": self.CRISIS_RESPONSE
            }
        
        # Handle missing response data
        if not response_data:
            fallback = self._build_fallback_response(emotion)
            return {
                "intro": fallback,
                "quote": "",
                "conclusion": ""
            }
        
        try:
            # Extract components
            figure = response_data.get("figure", "a wise person")
            context_line = response_data.get("context_line", "who understood life's challenges")
            quote = response_data.get("quote", "Every moment is a fresh beginning.")
            encouragement_line = response_data.get("encouragement_line", "You have strength within you.")
            
            # Get acknowledgment for this emotion
            acknowledgment = self._get_acknowledgment(emotion)
            
            # Build response components
            intro = (
                f"It sounds like you're feeling {emotion}. {acknowledgment} "
                f"You remind me of {figure}, {context_line}."
            )
            
            conclusion = encouragement_line
            
            return {
                "intro": intro,
                "quote": quote,
                "conclusion": conclusion
            }
            
        except Exception as e:
            logger.error(f"Error building voice-optimized response for emotion '{emotion}': {e}")
            fallback = self._build_fallback_response(emotion)
            return {
                "intro": fallback,
                "quote": "",
                "conclusion": ""
            }
    
    def _get_acknowledgment(self, emotion: str) -> str:
        """Get an appropriate acknowledgment for the emotion."""
        acknowledgments = self.EMOTION_ACKNOWLEDGMENTS.get(emotion, [self.DEFAULT_ACKNOWLEDGMENT])
        return random.choice(acknowledgments)
    
    def _build_fallback_response(self, emotion: str) -> str:
        """Build a fallback response when quote data is unavailable."""
        acknowledgment = self._get_acknowledgment(emotion)
        
        fallback = (
            f"It sounds like you're feeling {emotion}. {acknowledgment} "
            f"You remind me of Seneca, who believed we have the strength to face any challenge. "
            f"[pause] 'We suffer more often in imagination than in reality.' "
            f"You have the power to overcome this moment."
        )
        
        logger.info(f"Using fallback response for emotion '{emotion}'")
        return fallback
    
    def add_disclaimer(self, response: str) -> str:
        """
        Add the required disclaimer to the end of the response.
        
        Args:
            response: The main response content
            
        Returns:
            Response with disclaimer appended
        """
        disclaimer = (
            " Thank you for calling Voiceback. Please remember, this service "
            "offers inspiration, not professional advice. Goodbye."
        )
        
        return response + disclaimer
    
    def get_supported_emotions(self) -> list:
        """Get list of emotions that have specific acknowledgments."""
        return list(self.EMOTION_ACKNOWLEDGMENTS.keys()) 