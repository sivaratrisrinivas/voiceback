# Historical Echo - Developer Specification

## Project Summary
Historical Echo is a voice-powered agent that delivers timeless wisdom in under 30 seconds. Users call in, share how they feel, and receive comfort or perspective from the great thinkers of history—instantly. Built for a 2-day public competition using Vapi's voice agent platform.

## Core Requirements

### **Functional Requirements**
- **Platform**: Vapi voice agent with telephony integration
- **Access**: Inbound calls only from US/Canada phone numbers
- **Duration**: Target 30-second interactions maximum
- **Language**: English only for MVP
- **Concurrency**: Support multiple simultaneous calls
- **Availability**: Public phone number for competition demonstration

### **User Experience Flow**
1. **Greeting**: "Welcome to Historical Echo, where voices from the past bring comfort to the present. In a few words, please share how you're feeling right now."
2. **Input Processing**: Accept both single words and full sentences
3. **Emotion Detection**: Map user input to predefined emotions
4. **Response Delivery**: Acknowledge emotion → introduce historical figure → brief pause → deliver quote → emotion-specific encouragement
5. **Call Termination**: Disclaimer + goodbye

### **Supported Emotions & Response Structure**
- **Primary Emotions**: anxiety, sadness, frustration, uncertainty, overwhelm
- **Fallback**: Default to Seneca for unclear responses after one clarification attempt

**Response Template**:
```
"It sounds like you're feeling [emotion]. [Acknowledgment]. You remind me of [Historical Figure], [context line].
[1-second pause]
'[Authentic Historical Quote]'
[Emotion-specific encouragement line]"
```

## Technical Architecture

### **System Design**
```
User Call → Vapi Platform → Input Processing → Emotion Detection → Response Selection → Voice Output
                              ↓
                         Logging System
                              ↓
                      Anonymous Transcripts
```

### **Core Components**
1. **Input Processor**: Handles speech-to-text and normalizes user input
2. **Emotion Detector**: Maps user expressions to predefined emotion categories
3. **Response Selector**: Chooses appropriate historical figure, context, and quote
4. **Output Generator**: Formats and delivers voice response with proper timing
5. **Error Handler**: Manages failures gracefully
6. **Logger**: Tracks key events and user interactions

### **Data Structure**
```python
# Configuration structure (separate config file)
EMOTION_RESPONSES = {
    "anxiety": [
        {
            "figure": "Seneca",
            "context_lines": [
                "the Stoic philosopher who wrote about facing anxiety with courage",
                "who often wrote about finding peace in uncertain times",
                "who believed anxiety could be eased by focusing on the present"
            ],
            "quote": "We suffer more often in imagination than in reality.",
            "encouragement_lines": [
                "You have the strength to face what lies ahead.",
                "Trust in your ability to handle whatever comes."
            ]
        },
        # Additional figures for variety...
    ],
    # Other emotions...
}
```

## Implementation Details

### **Voice Configuration**
- **Voice**: Neutral, warm, calm tone (ElevenLabs or PlayHT via Vapi)
- **Speed**: Natural conversational pace
- **Pauses**: 1-second pause before quotes, natural pauses between sections
- **Error Messages**: Friendly, brief recovery prompts

### **Input Handling**
- **Timeout**: 7 seconds silence → gentle re-prompt → 7 seconds → end call
- **Emotion Detection**: Keyword matching with fallback patterns
- **Crisis Detection**: Monitor for self-harm keywords → provide supportive message + helpline numbers

### **Response Variations**
- **Context Lines**: 2-3 variations per figure/emotion, randomly selected
- **Encouragement**: Emotion-specific closing lines, randomly selected
- **Historical Figures**: 2-3 figures per emotion for variety

### **Error Handling Strategy**
```python
def handle_error(error_type):
    if error_type == "transcription_failure":
        return "I didn't catch that. Could you share how you're feeling in a word or two?"
    elif error_type == "system_error":
        return "Sorry, something went wrong on our end. Please try calling Historical Echo again in a few minutes. Goodbye."
    elif error_type == "timeout":
        return "It seems now may not be the right moment. Thank you for calling Historical Echo. Goodbye."
```

### **Crisis Response Protocol**
```python
CRISIS_KEYWORDS = ["suicide", "kill myself", "end it all", "hurt myself", "no point"]
CRISIS_RESPONSE = "I'm truly sorry you're feeling this way. Historical Echo is not equipped to help with urgent emotional crises, but you're not alone. Please consider reaching out to a professional or calling a helpline such as 988 in the US or 9152987821 in India."
```

## Data Handling

### **Privacy & Storage**
- **Anonymous Logging**: Store transcripts without phone numbers or personal identifiers
- **Data Retention**: Log format: `{timestamp, detected_emotion, selected_figure, response_delivered, call_duration}`
- **No Recording Announcements**: Keep experience seamless
- **Usage**: Analytics for improvement, not user tracking

### **Logging Schema**
```json
{
    "timestamp": "2025-05-28T23:29:00Z",
    "session_id": "uuid",
    "detected_emotion": "anxiety",
    "selected_figure": "seneca",
    "quote_delivered": true,
    "call_duration_seconds": 28,
    "error_occurred": false
}
```

## Testing Plan

### **Automated Tests**
1. **Unit Tests**
   - Emotion detection accuracy with sample inputs
   - Response selection logic for each emotion
   - Configuration loading and validation
   - Error handling scenarios

2. **Integration Tests**
   - End-to-end call flow simulation
   - Vapi platform integration
   - Timeout and silence handling
   - Crisis keyword detection

3. **Sample Test Cases**
```python
def test_emotion_detection():
    assert detect_emotion("I'm really anxious about tomorrow") == "anxiety"
    assert detect_emotion("feeling lost and sad") == "sadness"
    assert detect_emotion("frustrated with everything") == "frustration"

def test_response_selection():
    response = select_response("anxiety")
    assert response["figure"] in ["Seneca", "Marcus Aurelius", "Epictetus"]
    assert len(response["quote"]) > 0
```

### **Manual Testing Checklist**
- [ ] Call connects successfully
- [ ] Greeting plays clearly
- [ ] Various emotion inputs processed correctly
- [ ] Historical quotes delivered with proper timing
- [ ] Crisis scenarios handled appropriately
- [ ] Call ends gracefully with disclaimer
- [ ] Concurrent calls work without interference
- [ ] Error scenarios provide helpful messages

## Development Setup

### **Environment Variables**
```bash
VAPI_API_KEY=your_vapi_key
PHONE_NUMBER=your_assigned_number
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### **Dependencies**
- Vapi SDK/API integration
- Speech processing libraries
- Logging framework
- Configuration management
- Testing framework (pytest recommended)

### **File Structure**
```
historical-echo/
├── src/
│   ├── main.py              # Entry point and call handler
│   ├── emotion_detector.py  # Input processing and emotion mapping
│   ├── response_selector.py # Quote and figure selection
│   ├── voice_handler.py     # Vapi integration and output
│   └── utils/
│       ├── logger.py        # Logging utilities
│       └── error_handler.py # Error management
├── config/
│   └── responses.json       # Emotion-to-quote mappings
├── tests/
│   ├── test_emotion_detection.py
│   ├── test_response_selection.py
│   └── test_integration.py
├── docs/
│   ├── architecture_diagram.png
│   └── sample_dialogues.md
└── README.md               # Setup guide and documentation
```

## Documentation Requirements

### **README.md Structure**
1. **Project Summary** (2-3 sentences)
2. **Quick Start Guide** (setup instructions)
3. **Sample Dialogues** (3-4 realistic examples)
4. **Architecture Overview** (with diagram)
5. **Design Decisions** (key trade-offs explained)
6. **Future Improvements** (roadmap ideas)
7. **Technical Details** (API endpoints, configuration)

### **Sample Dialogue Examples**
```
User: "I'm anxious about my job interview tomorrow"
Historical Echo: "It sounds like you're feeling anxious. Many have walked this path before you. You remind me of Seneca, the Stoic philosopher who wrote about facing anxiety with courage. 'We suffer more often in imagination than in reality.' You have the strength to face what lies ahead. Thank you for calling Historical Echo. Please remember, this service offers inspiration, not professional advice. Goodbye."
```

## Success Metrics
- **Call Completion Rate**: >90% of calls reach quote delivery
- **Response Time**: <5 seconds from emotion detection to quote start
- **Error Rate**: <5% of calls encounter technical issues
- **User Experience**: Smooth, under 30-second interactions

## Future Expansion Ideas
- Multilingual support (Spanish, Hindi, French)
- Web and SMS interfaces
- User-submitted historical quotes
- Personalized figure preferences
- Daily wisdom callbacks
- Expanded emotion categories
- Advanced analytics dashboard

This specification provides everything needed for immediate development while maintaining flexibility for post-competition improvements and scaling.

---
