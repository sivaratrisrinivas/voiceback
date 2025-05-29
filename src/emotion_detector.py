"""
Text-based emotion detection for voice input.

This module processes user speech (converted to text) and maps it to 
predefined emotion categories suitable for historical quote responses.
"""

import re
import os
import json
import datetime
from typing import Optional, Dict, List
from loguru import logger
from pathlib import Path


class EmotionDetector:
    """Detects emotions from user text input (converted from speech)."""
    
    # Emotion keywords based on spec.md supported emotions
    EMOTION_KEYWORDS = {
        "anxiety": [
            "anxious", "anxiety", "worried", "worry", "nervous", "stressed", 
            "stress", "panic", "panicked", "tension", "tense",
            "fearful", "afraid", "scared", "apprehensive", "restless", 
            "jittery", "on edge"
        ],
        "sadness": [
            "sad", "sadness", "depressed", "depression", "down", "low", 
            "blue", "melancholy", "grief", "grieving", "heartbroken", 
            "disappointed", "hopeless", "despair", "lonely", "empty",
            "hurt", "pain", "anguish", "sorrow", "mourning"
        ],
        "frustration": [
            "frustrated", "frustration", "mad", "irritated",
            "annoyed", "pissed", "furious", "rage", "upset", "bothered",
            "aggravated", "exasperated", "fed up", "resentful", "bitter",
            "outraged", "livid", "heated", "steamed", "i'm angry", "feel angry",
            "so angry", "really angry", "very angry", "getting angry"
        ],
        "uncertainty": [
            "uncertain", "uncertainty", "confused", "confusion", "lost", 
            "unclear", "unsure", "doubt", "doubtful", "puzzled", "bewildered",
            "perplexed", "mixed up", "torn", "conflicted", "indecisive",
            "questioning", "wondering", "hesitant", "undecided"
        ],
        "overwhelm": [
            "overwhelmed", "overwhelm", "too much", "overloaded", "swamped",
            "drowning", "suffocated", "exhausted", "burnt out", "burnout",
            "overworked", "pressured", "burdened", "weighed down", "crushed",
            "stretched thin", "at capacity", "maxed out"
        ]
    }
    
    # Default crisis keywords - can be overridden by configuration
    DEFAULT_CRISIS_KEYWORDS = [
        "suicide", "kill myself", "end it all", "hurt myself", "no point",
        "give up", "can't go on", "want to die", "suicidal", "self harm"
    ]
    
    # Default fallback emotion when input is unclear or empty
    # "anxiety" is chosen as it's the most common emotional state that leads to seeking support,
    # and provides a safe, supportive response that doesn't assume severe crisis
    DEFAULT_EMOTION = "anxiety"
    
    def __init__(self, crisis_keywords_source: Optional[str] = None, default_emotion: str = "anxiety"):
        """
        Initialize the emotion detector.
        
        Args:
            crisis_keywords_source: Path to crisis keywords file or None to use defaults
            default_emotion: Emotion to use when input is unclear (default: "anxiety")
        """
        self.default_emotion = default_emotion
        
        # Load crisis keywords from configurable source
        self.crisis_keywords = self._load_crisis_keywords(crisis_keywords_source)
        
        # Compile regex patterns for better performance
        self._emotion_patterns = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            # Create pattern that matches whole words (case insensitive)
            pattern = r'\b(?:' + '|'.join(re.escape(keyword) for keyword in keywords) + r')\b'
            self._emotion_patterns[emotion] = re.compile(pattern, re.IGNORECASE)
        
        # Crisis detection pattern
        crisis_pattern = r'\b(?:' + '|'.join(re.escape(keyword) for keyword in self.crisis_keywords) + r')\b'
        self._crisis_pattern = re.compile(crisis_pattern, re.IGNORECASE)
        
        # Emotion priority order for tie-breaking (specific to general)
        self._emotion_priority = ["uncertainty", "overwhelm", "frustration", "sadness", "anxiety"]
        
        logger.info(f"EmotionDetector initialized with {len(self.crisis_keywords)} crisis keywords and default emotion '{self.default_emotion}'")
    
    def _load_crisis_keywords(self, source: Optional[str] = None) -> List[str]:
        """
        Load crisis keywords from configurable source.
        
        Args:
            source: Path to keywords file, environment variable name, or None for defaults
            
        Returns:
            List of crisis keywords
        """
        # Try environment variable first
        env_keywords = os.getenv('CRISIS_KEYWORDS')
        if env_keywords:
            try:
                # Support JSON array format in environment variable
                keywords = json.loads(env_keywords)
                logger.info(f"Loaded {len(keywords)} crisis keywords from environment variable CRISIS_KEYWORDS")
                return keywords
            except json.JSONDecodeError:
                # Support comma-separated format
                keywords = [kw.strip() for kw in env_keywords.split(',') if kw.strip()]
                logger.info(f"Loaded {len(keywords)} crisis keywords from environment variable CRISIS_KEYWORDS (comma-separated)")
                return keywords
        
        # Try loading from file if source provided
        if source:
            try:
                source_path = Path(source)
                if source_path.exists():
                    with open(source_path, 'r', encoding='utf-8') as f:
                        if source_path.suffix.lower() == '.json':
                            keywords = json.load(f)
                        else:
                            # Assume text file with one keyword per line
                            keywords = [line.strip() for line in f if line.strip()]
                    logger.info(f"Loaded {len(keywords)} crisis keywords from file: {source}")
                    return keywords
                else:
                    logger.warning(f"Crisis keywords file not found: {source}, using defaults")
            except Exception as e:
                logger.error(f"Failed to load crisis keywords from {source}: {e}, using defaults")
        
        # Fallback to default keywords
        logger.info(f"Using default crisis keywords ({len(self.DEFAULT_CRISIS_KEYWORDS)} keywords)")
        return self.DEFAULT_CRISIS_KEYWORDS.copy()
    
    def detect_emotion(self, user_input: str) -> str:
        """
        Detect the primary emotion from user input text.
        
        Args:
            user_input: The user's spoken input (converted to text)
            
        Returns:
            The detected emotion string, defaults to configured default emotion if unclear
        """
        if not user_input or not user_input.strip():
            logger.warning("Empty user input received, using default emotion")
            return self.default_emotion
        
        user_text = user_input.strip().lower()
        logger.debug(f"Analyzing user input: '{user_input}'")
        
        # Check for crisis keywords first with comprehensive monitoring
        if self._crisis_pattern.search(user_text):
            # CRITICAL: Crisis keywords detected - log for monitoring and alerting
            crisis_matches = self._crisis_pattern.findall(user_text)
            timestamp = datetime.datetime.now().isoformat()
            logger.critical(f"🚨 CRISIS DETECTED 🚨 Keywords: {crisis_matches} | Input: '{user_input}' | Timestamp: {timestamp}")
            
            # Additional monitoring log for external systems (structured format)
            logger.bind(
                event_type="crisis_detection",
                crisis_keywords=crisis_matches,
                user_input=user_input,
                severity="critical"
            ).critical("Crisis keywords detected in user input")
            
            return "crisis"  # Special handling needed
        
        # Score each emotion based on keyword matches
        emotion_scores = {}
        for emotion, pattern in self._emotion_patterns.items():
            matches = pattern.findall(user_text)
            emotion_scores[emotion] = len(matches)
        
        # Log detected matches for debugging
        for emotion, score in emotion_scores.items():
            if score > 0:
                logger.debug(f"Emotion '{emotion}' scored {score} matches")
        
        # Return emotion with highest score, default to configured default if no matches
        if any(score > 0 for score in emotion_scores.values()):
            # Find max score
            max_score = max(emotion_scores.values())
            
            # Get all emotions with max score
            top_emotions = [emotion for emotion, score in emotion_scores.items() if score == max_score]
            
            # Use priority order for tie-breaking (most specific wins)
            for emotion in self._emotion_priority:
                if emotion in top_emotions:
                    detected_emotion = emotion
                    break
            else:
                # Fallback to first emotion if none in priority list
                detected_emotion = top_emotions[0]
            
            logger.info(f"Detected emotion: '{detected_emotion}' from input: '{user_input}'")
            return detected_emotion
        else:
            # No emotion keywords found - use configured default
            # "anxiety" is chosen as default because it's the most common emotional state 
            # that leads people to seek support, and provides a safe, supportive response 
            # that doesn't assume severe crisis while still offering meaningful help
            logger.info(f"No emotion keywords found, using default emotion '{self.default_emotion}' for: '{user_input}'")
            return self.default_emotion
    
    def detect_with_confidence(self, user_input: str) -> Dict[str, any]:
        """
        Detect emotion with confidence scores for all emotions.
        
        Args:
            user_input: The user's spoken input (converted to text)
            
        Returns:
            Dict with 'emotion', 'confidence', 'all_scores', and 'is_crisis'
        """
        if not user_input or not user_input.strip():
            return {
                "emotion": self.default_emotion,
                "confidence": 0.0,
                "all_scores": {},
                "is_crisis": False
            }
        
        user_text = user_input.strip().lower()
        
        # Crisis detection
        is_crisis = bool(self._crisis_pattern.search(user_text))
        
        # Calculate scores for each emotion
        emotion_scores = {}
        total_words = len(user_text.split())
        
        for emotion, pattern in self._emotion_patterns.items():
            matches = pattern.findall(user_text)
            # Normalize score by text length for confidence calculation
            emotion_scores[emotion] = len(matches) / max(total_words, 1)
        
        # Find primary emotion
        if any(score > 0 for score in emotion_scores.values()):
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            confidence = emotion_scores[primary_emotion]
        else:
            primary_emotion = self.default_emotion
            confidence = 0.0
        
        return {
            "emotion": primary_emotion,
            "confidence": confidence,
            "all_scores": emotion_scores,
            "is_crisis": is_crisis
        }
    
    def get_supported_emotions(self) -> List[str]:
        """Get list of all supported emotion categories."""
        # Include "crisis" to maintain consistency with detect_emotion() return values
        return list(self.EMOTION_KEYWORDS.keys()) + ["crisis"]
    
    def is_crisis_input(self, user_input: str) -> bool:
        """
        Check if user input contains crisis-related keywords.
        
        Args:
            user_input: The user's input text
            
        Returns:
            True if crisis keywords detected, False otherwise
        """
        if not user_input:
            return False
        
        return bool(self._crisis_pattern.search(user_input.strip().lower())) 