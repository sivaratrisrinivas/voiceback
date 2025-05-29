"""
Tests for the ResponseBuilder class.

This module tests response formatting functionality for historical quote responses.
"""

import pytest
from src.response_builder import ResponseBuilder


class TestResponseBuilder:
    """Test cases for the ResponseBuilder class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.builder = ResponseBuilder()
    
    def test_initialization(self):
        """Test that ResponseBuilder initializes correctly."""
        assert self.builder is not None
        assert hasattr(self.builder, 'EMOTION_ACKNOWLEDGMENTS')
        assert hasattr(self.builder, 'CRISIS_RESPONSE')
        
        # Check that all expected emotions have acknowledgments
        expected_emotions = ["anxiety", "sadness", "frustration", "uncertainty", "overwhelm"]
        assert all(emotion in self.builder.EMOTION_ACKNOWLEDGMENTS for emotion in expected_emotions)
    
    def test_build_response_with_valid_data(self):
        """Test building response with complete valid data."""
        response_data = {
            "figure": "Seneca",
            "context_line": "the Stoic philosopher who wrote about facing anxiety with courage",
            "quote": "We suffer more often in imagination than in reality.",
            "encouragement_line": "You have the strength to face what lies ahead."
        }
        
        response = self.builder.build_response("anxiety", response_data, "I'm anxious")
        
        assert "It sounds like you're feeling anxiety" in response
        assert "Seneca" in response
        assert "the Stoic philosopher who wrote about facing anxiety with courage" in response
        assert "We suffer more often in imagination than in reality." in response
        assert "You have the strength to face what lies ahead." in response
        assert "[pause]" in response
    
    def test_build_response_all_emotions(self):
        """Test building responses for all supported emotions."""
        emotions = ["anxiety", "sadness", "frustration", "uncertainty", "overwhelm"]
        
        response_data = {
            "figure": "Marcus Aurelius",
            "context_line": "who understood life's challenges",
            "quote": "Every moment is a fresh beginning.",
            "encouragement_line": "You have strength within you."
        }
        
        for emotion in emotions:
            response = self.builder.build_response(emotion, response_data, f"I feel {emotion}")
            
            assert f"It sounds like you're feeling {emotion}" in response
            assert "Marcus Aurelius" in response
            assert "Every moment is a fresh beginning." in response
            assert "[pause]" in response
    
    def test_build_response_missing_data(self):
        """Test building response when response_data is None or incomplete."""
        # Test with None data
        response = self.builder.build_response("anxiety", None, "I'm anxious")
        assert "Seneca" in response  # Should use fallback
        assert "We suffer more often in imagination than in reality." in response
        
        # Test with incomplete data
        incomplete_data = {"figure": "Aristotle"}  # Missing other fields
        response = self.builder.build_response("sadness", incomplete_data, "I'm sad")
        assert "Aristotle" in response
        assert "who understood life's challenges" in response  # Default context
    
    def test_crisis_response(self):
        """Test building response for crisis situations."""
        response = self.builder.build_response("crisis", None, "I want to hurt myself")
        
        assert response == self.builder.CRISIS_RESPONSE
        assert "I'm truly sorry you're feeling this way" in response
        assert "988" in response  # US helpline
        assert "1-833-456-4566" in response  # Canada helpline
        assert "not equipped to help with urgent emotional crises" in response
    
    def test_build_voice_optimized_response(self):
        """Test building voice-optimized response with separate components."""
        response_data = {
            "figure": "Seneca",
            "context_line": "the Stoic philosopher who wrote about courage",
            "quote": "We suffer more often in imagination than in reality.",
            "encouragement_line": "You have the strength to face what lies ahead."
        }
        
        result = self.builder.build_voice_optimized_response("anxiety", response_data, "I'm anxious")
        
        assert isinstance(result, dict)
        assert "intro" in result
        assert "quote" in result
        assert "conclusion" in result
        
        assert "It sounds like you're feeling anxiety" in result["intro"]
        assert "Seneca" in result["intro"]
        assert result["quote"] == "We suffer more often in imagination than in reality."
        assert result["conclusion"] == "You have the strength to face what lies ahead."
    
    def test_voice_optimized_crisis_response(self):
        """Test voice-optimized response for crisis situations."""
        result = self.builder.build_voice_optimized_response("crisis", None, "crisis input")
        
        assert result["intro"] == ""
        assert result["quote"] == ""
        assert result["conclusion"] == self.builder.CRISIS_RESPONSE
    
    def test_acknowledgment_randomization(self):
        """Test that acknowledgments are randomized."""
        # Run multiple times to check for variation
        acknowledgments = set()
        for _ in range(20):
            ack = self.builder._get_acknowledgment("anxiety")
            acknowledgments.add(ack)
        
        # Should get some variation (at least 2 different acknowledgments)
        assert len(acknowledgments) >= 2
        
        # All acknowledgments should be valid for anxiety
        valid_acks = self.builder.EMOTION_ACKNOWLEDGMENTS["anxiety"]
        assert all(ack in valid_acks for ack in acknowledgments)
    
    def test_fallback_response(self):
        """Test the fallback response generation."""
        fallback = self.builder._build_fallback_response("uncertainty")
        
        assert "It sounds like you're feeling uncertainty" in fallback
        assert "Seneca" in fallback
        assert "We suffer more often in imagination than in reality." in fallback
        assert "[pause]" in fallback
    
    def test_add_disclaimer(self):
        """Test adding disclaimer to responses."""
        original_response = "This is a test response."
        response_with_disclaimer = self.builder.add_disclaimer(original_response)
        
        assert original_response in response_with_disclaimer
        assert "Thank you for calling Voiceback" in response_with_disclaimer
        assert "offers inspiration, not professional advice" in response_with_disclaimer
        assert "Goodbye" in response_with_disclaimer
    
    def test_get_supported_emotions(self):
        """Test getting list of emotions with specific acknowledgments."""
        emotions = self.builder.get_supported_emotions()
        
        assert isinstance(emotions, list)
        expected_emotions = ["anxiety", "sadness", "frustration", "uncertainty", "overwhelm"]
        assert all(emotion in emotions for emotion in expected_emotions)
    
    def test_acknowledgment_for_unknown_emotion(self):
        """Test acknowledgment for emotions not in the predefined list."""
        ack = self.builder._get_acknowledgment("unknown_emotion")
        assert ack == self.builder.DEFAULT_ACKNOWLEDGMENT
    
    def test_error_handling_in_build_response(self):
        """Test error handling when building response fails."""
        # Force an error by passing invalid data types
        invalid_data = "not a dictionary"
        
        # Should not crash and return fallback
        response = self.builder.build_response("anxiety", invalid_data, "test input")
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_response_structure_consistency(self):
        """Test that all responses follow the expected structure."""
        emotions = ["anxiety", "sadness", "frustration", "uncertainty", "overwhelm"]
        
        response_data = {
            "figure": "Test Figure",
            "context_line": "test context",
            "quote": "Test quote here.",
            "encouragement_line": "Test encouragement."
        }
        
        for emotion in emotions:
            response = self.builder.build_response(emotion, response_data, f"I feel {emotion}")
            
            # Check structure: emotion mention -> acknowledgment -> figure -> context -> pause -> quote -> encouragement
            parts = response.split(' ')
            
            # Should start with "It sounds like you're feeling [emotion]"
            assert response.startswith(f"It sounds like you're feeling {emotion}")
            
            # Should contain figure name
            assert "Test Figure" in response
            
            # Should have pause marker
            assert "[pause]" in response
            
            # Should contain quote in single quotes
            assert "'Test quote here.'" in response
    
    def test_empty_quote_handling(self):
        """Test handling of empty or missing quotes."""
        response_data = {
            "figure": "Seneca",
            "context_line": "the philosopher",
            "quote": "",  # Empty quote
            "encouragement_line": "You are strong."
        }
        
        response = self.builder.build_response("anxiety", response_data, "I'm anxious")
        
        # Should still build a response, using default values
        assert "Seneca" in response
        assert len(response) > 50  # Should be substantial
    
    def test_special_characters_in_data(self):
        """Test handling of special characters in response data."""
        response_data = {
            "figure": "Søren Kierkegaard",
            "context_line": "the Danish philosopher who wrote about anxiety & despair",
            "quote": "Life can only be understood backwards; but it must be lived forwards.",
            "encouragement_line": "Trust in your ability to navigate life's challenges."
        }
        
        response = self.builder.build_response("anxiety", response_data, "I'm anxious")
        
        # Should handle special characters correctly
        assert "Søren Kierkegaard" in response
        assert "&" in response
        assert ";" in response
    
    def test_long_text_handling(self):
        """Test handling of very long text in response data."""
        long_quote = "This is a very long quote that goes on and on " * 20
        
        response_data = {
            "figure": "Seneca",
            "context_line": "the Stoic philosopher",
            "quote": long_quote,
            "encouragement_line": "You have strength."
        }
        
        response = self.builder.build_response("anxiety", response_data, "I'm anxious")
        
        # Should handle long text without issues
        assert long_quote in response
        assert len(response) > len(long_quote)  # Should have other components too 