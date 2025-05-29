"""
Tests for the EmotionDetector class.

This module tests text-based emotion detection functionality for voice input.
"""

import pytest
from src.emotion_detector import EmotionDetector


class TestEmotionDetector:
    """Test cases for the EmotionDetector class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.detector = EmotionDetector()
    
    def test_initialization(self):
        """Test that EmotionDetector initializes correctly."""
        assert self.detector is not None
        assert hasattr(self.detector, '_emotion_patterns')
        assert hasattr(self.detector, '_crisis_pattern')
        
        # Check that all expected emotions are present
        expected_emotions = ["anxiety", "sadness", "frustration", "uncertainty", "overwhelm"]
        assert all(emotion in self.detector.EMOTION_KEYWORDS for emotion in expected_emotions)
    
    def test_detect_anxiety(self):
        """Test detection of anxiety-related emotions."""
        test_cases = [
            "I'm really anxious about my job interview tomorrow",
            "I feel so worried about everything",
            "I'm stressed out and nervous",
            "This is making me panic",
            "I'm on edge and can't relax"
        ]
        
        for text in test_cases:
            emotion = self.detector.detect_emotion(text)
            assert emotion == "anxiety", f"Failed to detect anxiety in: '{text}'"
    
    def test_detect_sadness(self):
        """Test detection of sadness-related emotions."""
        test_cases = [
            "I feel so sad and empty inside",
            "I'm really depressed about this situation",
            "I'm grieving the loss of my friend",
            "I feel heartbroken and lonely",
            "Everything feels hopeless right now"
        ]
        
        for text in test_cases:
            emotion = self.detector.detect_emotion(text)
            assert emotion == "sadness", f"Failed to detect sadness in: '{text}'"
    
    def test_detect_frustration(self):
        """Test detection of frustration-related emotions."""
        test_cases = [
            "I'm so frustrated with this situation",
            "I'm angry about how this turned out",
            "This is making me furious",
            "I'm irritated and fed up",
            "I'm livid about this injustice"
        ]
        
        for text in test_cases:
            emotion = self.detector.detect_emotion(text)
            assert emotion == "frustration", f"Failed to detect frustration in: '{text}'"
    
    def test_detect_uncertainty(self):
        """Test detection of uncertainty-related emotions."""
        test_cases = [
            "I'm so uncertain about what to do",
            "I feel confused and lost",
            "I'm unsure about my next steps",
            "I'm torn between different choices",
            "I'm questioning everything right now"
        ]
        
        for text in test_cases:
            emotion = self.detector.detect_emotion(text)
            assert emotion == "uncertainty", f"Failed to detect uncertainty in: '{text}'"
    
    def test_detect_overwhelm(self):
        """Test detection of overwhelm-related emotions."""
        test_cases = [
            "I feel completely overwhelmed",
            "There's just too much to handle",
            "I'm drowning in responsibilities",
            "I'm burnt out and exhausted",
            "I feel crushed by all the pressure"
        ]
        
        for text in test_cases:
            emotion = self.detector.detect_emotion(text)
            assert emotion == "overwhelm", f"Failed to detect overwhelm in: '{text}'"
    
    def test_crisis_detection(self):
        """Test detection of crisis-related keywords."""
        crisis_inputs = [
            "I want to kill myself",
            "I'm thinking about suicide",
            "I want to hurt myself",
            "There's no point in going on",
            "I can't take it anymore and want to end it all"
        ]
        
        for text in crisis_inputs:
            emotion = self.detector.detect_emotion(text)
            assert emotion == "crisis", f"Failed to detect crisis in: '{text}'"
            
            # Also test the specific crisis detection method
            assert self.detector.is_crisis_input(text), f"is_crisis_input failed for: '{text}'"
    
    def test_default_fallback(self):
        """Test fallback to anxiety for unclear input."""
        unclear_inputs = [
            "Hello there",
            "What's the weather like?",
            "I like pizza",
            "Random words here",
            "Nothing emotional at all"
        ]
        
        for text in unclear_inputs:
            emotion = self.detector.detect_emotion(text)
            assert emotion == "anxiety", f"Should default to anxiety for: '{text}'"
    
    def test_empty_input(self):
        """Test handling of empty or whitespace input."""
        empty_inputs = ["", "   ", "\n\t", None]
        
        for text in empty_inputs:
            emotion = self.detector.detect_emotion(text)
            assert emotion == "anxiety", f"Should default to anxiety for empty input: '{text}'"
    
    def test_mixed_emotions(self):
        """Test input containing multiple emotion keywords."""
        # This should return the emotion with the most matches
        mixed_input = "I'm anxious and worried and stressed and nervous"
        emotion = self.detector.detect_emotion(mixed_input)
        assert emotion == "anxiety"  # All keywords are anxiety-related
        
        # Test with genuinely mixed emotions (first match wins in case of ties)
        mixed_input2 = "I'm sad but also angry"
        emotion2 = self.detector.detect_emotion(mixed_input2)
        # Either sadness or frustration is acceptable, depends on implementation
        assert emotion2 in ["sadness", "frustration"]
    
    def test_case_insensitive(self):
        """Test that detection is case insensitive."""
        test_cases = [
            ("I'M ANXIOUS", "anxiety"),
            ("i'm sad", "sadness"),
            ("FRUSTRATED", "frustration"),
            ("Uncertain", "uncertainty"),
            ("OVERWHELMED", "overwhelm")
        ]
        
        for text, expected_emotion in test_cases:
            emotion = self.detector.detect_emotion(text)
            assert emotion == expected_emotion, f"Case insensitive test failed for: '{text}'"
    
    def test_word_boundaries(self):
        """Test that partial word matches don't trigger false positives."""
        # These should NOT trigger emotion detection
        false_positives = [
            "I like saddle riding",  # 'sad' in 'saddle' 
            "I'm going to anger management",  # 'anger' as part of compound
            "The weather is nice today"  # completely neutral
        ]
        
        for text in false_positives:
            emotion = self.detector.detect_emotion(text)
            # Should default to anxiety since no clear emotion keywords
            assert emotion == "anxiety", f"False positive detected in: '{text}'"
    
    def test_detect_with_confidence(self):
        """Test the detailed emotion detection with confidence scores."""
        test_input = "I'm really anxious and worried"
        result = self.detector.detect_with_confidence(test_input)
        
        assert isinstance(result, dict)
        assert "emotion" in result
        assert "confidence" in result
        assert "all_scores" in result
        assert "is_crisis" in result
        
        assert result["emotion"] == "anxiety"
        assert result["confidence"] > 0
        assert not result["is_crisis"]
        assert isinstance(result["all_scores"], dict)
    
    def test_get_supported_emotions(self):
        """Test getting list of supported emotions."""
        emotions = self.detector.get_supported_emotions()
        
        assert isinstance(emotions, list)
        assert len(emotions) == 6  # 5 standard emotions + "crisis"
        expected_emotions = ["anxiety", "sadness", "frustration", "uncertainty", "overwhelm", "crisis"]
        assert all(emotion in emotions for emotion in expected_emotions)
    
    def test_is_crisis_input(self):
        """Test the crisis input detection method."""
        # Crisis inputs
        assert self.detector.is_crisis_input("I want to kill myself")
        assert self.detector.is_crisis_input("suicide thoughts")
        assert self.detector.is_crisis_input("I want to hurt myself")
        
        # Non-crisis inputs
        assert not self.detector.is_crisis_input("I'm sad")
        assert not self.detector.is_crisis_input("I'm anxious")
        assert not self.detector.is_crisis_input("Hello world")
        assert not self.detector.is_crisis_input("")
        assert not self.detector.is_crisis_input(None)
    
    def test_performance_with_long_text(self):
        """Test that detection works with longer text inputs."""
        long_text = (
            "I've been feeling really anxious lately about my job situation. "
            "The company has been going through layoffs and I'm worried that "
            "I might be next. I've been having trouble sleeping and I'm constantly "
            "stressed about what might happen. I feel nervous all the time and "
            "can't seem to relax."
        )
        
        emotion = self.detector.detect_emotion(long_text)
        assert emotion == "anxiety"
        
        # Test confidence detection with long text
        result = self.detector.detect_with_confidence(long_text)
        assert result["emotion"] == "anxiety"
        assert result["confidence"] > 0 