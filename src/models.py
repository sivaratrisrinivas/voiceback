"""
Data models for Voiceback emotion response system.

Defines the structure and validation for emotion responses and historical figures.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import datetime


@dataclass(frozen=True)
class HistoricalFigure:
    """Represents a historical figure with their wisdom."""
    
    name: str
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    description: Optional[str] = None
    cultural_background: Optional[str] = None
    
    def __post_init__(self):
        """Validate historical figure data."""
        if not self.name or not self.name.strip():
            raise ValueError("Historical figure name cannot be empty")
        
        if len(self.name) > 100:
            raise ValueError("Historical figure name too long (max 100 characters)")
        
        # Validate year ranges if provided
        if self.birth_year is not None:
            if self.birth_year < -3000 or self.birth_year > datetime.datetime.now().year:
                raise ValueError("Birth year must be between 3000 BCE and current year")
        
        if self.death_year is not None:
            if self.death_year < -3000 or self.death_year > datetime.datetime.now().year:
                raise ValueError("Death year must be between 3000 BCE and current year")
            
            if self.birth_year is not None and self.death_year <= self.birth_year:
                raise ValueError("Death year must be after birth year")
    
    @property
    def display_name(self) -> str:
        """Get the display name for this figure."""
        return self.name
    
    @property
    def lifespan(self) -> Optional[str]:
        """Get a formatted lifespan string."""
        if self.birth_year is None and self.death_year is None:
            return None
        
        birth_str = str(self.birth_year) if self.birth_year is not None else "?"
        death_str = str(self.death_year) if self.death_year is not None else "?"
        
        return f"{birth_str} - {death_str}"


@dataclass(frozen=True)
class EmotionResponse:
    """Represents a complete emotion response with all components."""
    
    emotion: str
    figure: HistoricalFigure
    context_lines: List[str]
    quote: str
    encouragement_lines: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate emotion response data."""
        # Validate emotion
        if not self.emotion or not self.emotion.strip():
            raise ValueError("Emotion cannot be empty")
        
        if len(self.emotion) > 50:
            raise ValueError("Emotion name too long (max 50 characters)")
        
        # Validate quote
        if not self.quote or not self.quote.strip():
            raise ValueError("Quote cannot be empty")
        
        if len(self.quote) > 1000:
            raise ValueError("Quote too long (max 1000 characters)")
        
        # Validate context lines
        if not self.context_lines:
            raise ValueError("Must have at least one context line")
        
        if len(self.context_lines) > 10:
            raise ValueError("Too many context lines (max 10)")
        
        for i, line in enumerate(self.context_lines):
            if not line or not line.strip():
                raise ValueError(f"Context line {i} cannot be empty")
            if len(line) > 500:
                raise ValueError(f"Context line {i} too long (max 500 characters)")
        
        # Validate encouragement lines
        if not self.encouragement_lines:
            raise ValueError("Must have at least one encouragement line")
        
        if len(self.encouragement_lines) > 10:
            raise ValueError("Too many encouragement lines (max 10)")
        
        for i, line in enumerate(self.encouragement_lines):
            if not line or not line.strip():
                raise ValueError(f"Encouragement line {i} cannot be empty")
            if len(line) > 500:
                raise ValueError(f"Encouragement line {i} too long (max 500 characters)")
    
    @classmethod
    def from_config_dict(cls, emotion: str, config_dict: Dict[str, Any]) -> "EmotionResponse":
        """
        Create EmotionResponse from configuration dictionary.
        
        Args:
            emotion: The emotion name
            config_dict: Dictionary from responses.json
            
        Returns:
            EmotionResponse instance
            
        Raises:
            ValueError: If config_dict is invalid
        """
        try:
            # Extract figure info
            figure_name = config_dict["figure"]
            figure = HistoricalFigure(name=figure_name)
            
            # Create emotion response
            return cls(
                emotion=emotion,
                figure=figure,
                context_lines=config_dict["context_lines"].copy(),
                quote=config_dict["quote"],
                encouragement_lines=config_dict["encouragement_lines"].copy(),
                metadata=config_dict.get("metadata", {})
            )
        except KeyError as e:
            raise ValueError(f"Missing required field in config: {e}")
        except Exception as e:
            raise ValueError(f"Invalid config data: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "emotion": self.emotion,
            "figure": self.figure.name,
            "context_lines": list(self.context_lines),
            "quote": self.quote,
            "encouragement_lines": list(self.encouragement_lines),
            "metadata": dict(self.metadata)
        }
    
    def get_random_context_line(self, exclude: Optional[List[str]] = None) -> str:
        """
        Get a random context line, optionally excluding specified ones.
        
        Args:
            exclude: List of context lines to exclude
            
        Returns:
            A random context line
        """
        import random
        
        available_lines = self.context_lines
        if exclude:
            available_lines = [line for line in self.context_lines if line not in exclude]
        
        if not available_lines:
            # Fallback to original list if all excluded
            available_lines = self.context_lines
        
        return random.choice(available_lines)
    
    def get_random_encouragement_line(self, exclude: Optional[List[str]] = None) -> str:
        """
        Get a random encouragement line, optionally excluding specified ones.
        
        Args:
            exclude: List of encouragement lines to exclude
            
        Returns:
            A random encouragement line
        """
        import random
        
        available_lines = self.encouragement_lines
        if exclude:
            available_lines = [line for line in self.encouragement_lines if line not in exclude]
        
        if not available_lines:
            # Fallback to original list if all excluded
            available_lines = self.encouragement_lines
        
        return random.choice(available_lines)
    
    @property
    def word_count(self) -> int:
        """Get approximate word count for the full response."""
        all_text = " ".join([
            self.quote,
            *self.context_lines,
            *self.encouragement_lines
        ])
        return len(all_text.split())
    
    @property
    def estimated_speaking_time(self) -> float:
        """
        Estimate speaking time in seconds (assuming ~150 words per minute).
        
        Returns:
            Estimated time in seconds
        """
        words_per_minute = 150
        return (self.word_count / words_per_minute) * 60


@dataclass
class ConfigurationStats:
    """Statistics about the loaded configuration."""
    
    total_emotions: int
    total_responses: int
    emotions_with_multiple_responses: int
    unique_figures: int
    average_responses_per_emotion: float
    total_context_lines: int
    total_encouragement_lines: int
    estimated_total_speaking_time: float
    
    @classmethod
    def from_config_data(cls, config_data: Dict[str, Any]) -> "ConfigurationStats":
        """
        Generate statistics from configuration data.
        
        Args:
            config_data: Loaded configuration dictionary
            
        Returns:
            ConfigurationStats instance
        """
        total_emotions = len(config_data)
        total_responses = sum(len(responses) for responses in config_data.values())
        emotions_with_multiple = sum(1 for responses in config_data.values() if len(responses) > 1)
        
        # Count unique figures
        figures = set()
        context_lines = 0
        encouragement_lines = 0
        total_words = 0
        
        for emotion, responses in config_data.items():
            for response in responses:
                figures.add(response["figure"])
                context_lines += len(response["context_lines"])
                encouragement_lines += len(response["encouragement_lines"])
                
                # Count words for speaking time estimate
                all_text = " ".join([
                    response["quote"],
                    *response["context_lines"],
                    *response["encouragement_lines"]
                ])
                total_words += len(all_text.split())
        
        avg_responses = total_responses / total_emotions if total_emotions > 0 else 0
        speaking_time = (total_words / 150) * 60 if total_words > 0 else 0  # 150 words/min
        
        return cls(
            total_emotions=total_emotions,
            total_responses=total_responses,
            emotions_with_multiple_responses=emotions_with_multiple,
            unique_figures=len(figures),
            average_responses_per_emotion=avg_responses,
            total_context_lines=context_lines,
            total_encouragement_lines=encouragement_lines,
            estimated_total_speaking_time=speaking_time
        )
    
    def __str__(self) -> str:
        """String representation of stats."""
        return (
            f"Configuration Stats:\n"
            f"  Emotions: {self.total_emotions}\n"
            f"  Total Responses: {self.total_responses}\n"
            f"  Unique Figures: {self.unique_figures}\n"
            f"  Avg Responses/Emotion: {self.average_responses_per_emotion:.1f}\n"
            f"  Estimated Speaking Time: {self.estimated_total_speaking_time:.1f}s"
        ) 