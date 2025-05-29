# Voiceback

> **Call in, share how you feel, and receive instant comfort from history's greatest thinkers in under 30 seconds.**

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-90%20passing-green)](#testing)
[![Development Status](https://img.shields.io/badge/status-Step%205%20Complete-brightgreen)](#development-progress)

Voiceback is a voice-powered agent that delivers timeless wisdom through phone calls. Users dial in, share their emotional state, and receive personalized quotes and encouragement from history's greatest philosophers and thinkers - all in under 30 seconds.

## 🎯 Project Overview

Voiceback bridges the gap between modern emotional needs and ancient wisdom. Built for a 2-day public competition using [Vapi's voice agent platform](https://vapi.ai), this system provides immediate emotional support through carefully curated historical quotes matched to the caller's feelings.

### Key Features

- **🎤 Voice-First Experience**: Natural phone-based interaction with speech-to-text processing
- **🧠 Emotion Detection**: Intelligent mapping of user expressions to emotional categories
- **📚 Historical Wisdom**: Curated quotes from Seneca, Marcus Aurelius, and other great thinkers
- **⚡ 30-Second Interactions**: Optimized for quick, meaningful exchanges
- **🔄 Dynamic Responses**: Randomized context and encouragement for variety
- **🚨 Crisis Support**: Built-in safety features with professional resource referrals

## 🚀 Current Status: Step 5 Complete

### ✅ Implemented Features

#### **Phase 1: Foundation (Steps 1-4)**
- **Vapi Integration**: Full telephony setup with webhook handling
- **Call Management**: Complete call lifecycle with proper state tracking
- **Voice Delivery**: Working greeting system with natural speech timing
- **Testing Infrastructure**: 90 comprehensive tests ensuring reliability

#### **Phase 2: Configuration System (Step 5)**
- **Emotion Mapping**: JSON-based configuration for anxiety and sadness responses
- **Quote Management**: Structured storage of historical figures, context, and encouragement
- **Validation System**: Robust configuration validation with error handling
- **Extensible Design**: Ready for additional emotions and historical figures

### 📋 Sample Interaction

```
Caller: "I'm really anxious about tomorrow"
Voiceback: "It sounds like you're feeling anxious. You remind me of 
Seneca, the Stoic philosopher who wrote about facing anxiety with courage. 
[pause] 'We suffer more often in imagination than in reality.' 
You have the strength to face what lies ahead. Thank you for calling 
Voiceback."
```

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.8 or higher
- [Vapi API account](https://vapi.ai) with API key
- Phone number configured for inbound calls

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/sivaratrisrinivas/voiceback.git
   cd voiceback
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp env.template .env
   # Edit .env with your Vapi API key and configuration
   ```

5. **Run the application**
   ```bash
   python src/main.py
   ```

### Environment Variables

```bash
VAPI_API_KEY=your_vapi_api_key_here
PHONE_NUMBER=your_vapi_phone_number
WEBHOOK_HOST=your_webhook_url
WEBHOOK_PORT=5000
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## 🏗️ Architecture

```
📞 User Call → 🌐 Vapi Platform → 🎯 Webhook Server → 🧠 Call Handler
                                                        ↓
🎭 Emotion Detection ← 📝 Text Processing ← 🗣️ Speech-to-Text
                    ↓
📚 Response Builder ← 🎲 Quote Selector ← ⚙️ Config Manager
                    ↓
🔊 Voice Delivery → 📞 User
```

### Core Components

- **`src/main.py`**: Flask webhook server and application entry point
- **`src/vapi_client.py`**: Vapi API integration and health checks
- **`src/call_handler.py`**: Call lifecycle management and state tracking
- **`src/config_manager.py`**: Configuration loading and validation
- **`config/responses.json`**: Emotion-to-quote mappings

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src

# Run specific test file
python -m pytest tests/test_config_manager.py -v
```

### Test Coverage

- **90 tests total** across all components
- **Unit Tests**: Individual component functionality
- **Integration Tests**: End-to-end call flow simulation
- **Configuration Tests**: Validation and error handling

## 🔧 Development Progress

### Completed Phases

- [x] **Step 1**: Project structure and environment setup
- [x] **Step 2**: Vapi connectivity and health checks  
- [x] **Step 3**: Basic call handling infrastructure
- [x] **Step 4**: Voice response and greeting delivery
- [x] **Step 5**: Configuration system foundation

### Next Steps

- [ ] **Step 6**: Enhanced configuration with caching and schema validation
- [ ] **Step 7**: Emotion detection and text processing
- [ ] **Step 8-11**: Advanced emotion detection with confidence scoring
- [ ] **Step 12-15**: Response generation and templating system
- [ ] **Step 16-19**: Call flow management and user input handling
- [ ] **Step 20-22**: Error handling and crisis detection
- [ ] **Step 23-24**: Logging and analytics infrastructure
- [ ] **Step 25-27**: Integration, testing, and performance optimization

## 📁 Project Structure

```
voiceback/
├── src/                    # Application source code
│   ├── main.py            # Entry point and webhook server
│   ├── vapi_client.py     # Vapi API integration
│   ├── call_handler.py    # Call lifecycle management
│   └── config_manager.py  # Configuration management
├── config/                # Configuration files
│   └── responses.json     # Emotion-to-quote mappings
├── tests/                 # Test suite
│   ├── test_main.py
│   ├── test_vapi_client.py
│   ├── test_call_handler.py
│   └── test_config_manager.py
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── env.template          # Environment configuration template
└── README.md             # Project documentation
```

## 🎭 Supported Emotions

### Currently Available
- **Anxiety**: Stoic wisdom from Seneca for facing uncertainty
- **Sadness**: Comfort from Marcus Aurelius on life's sorrows

### Coming Soon
- **Frustration**: Guidance on managing anger and irritation
- **Uncertainty**: Wisdom for navigating confusion and doubt  
- **Overwhelm**: Support for feeling stressed and exhausted

## 🔒 Privacy & Safety

- **Anonymous Interactions**: No personal data stored or tracked
- **Crisis Detection**: Built-in safety features for concerning language
- **Professional Resources**: Helpline information (988 US, 9152987821 India)
- **Secure Processing**: All voice data processed through Vapi's secure platform

## 🤝 Contributing

This project is built incrementally following a detailed [development blueprint](prompt_plan.md). Each step builds upon the previous while maintaining full functionality.

### Development Workflow

1. Follow the step-by-step implementation plan
2. Maintain test coverage for all new features
3. Ensure backward compatibility
4. Update documentation

### Running Development Server

```bash
# Start the webhook server
python src/main.py

# Run health check
python src/main.py --health-check

# Run tests in watch mode
python -m pytest --watch
```

## 📊 Performance Targets

- **Response Time**: <5 seconds from emotion detection to quote delivery
- **Call Completion**: >90% of calls reach successful quote delivery
- **Interaction Duration**: <30 seconds total per call
- **Error Rate**: <5% of calls encounter technical issues

## 📄 License

This project is released into the public domain. See the full license in [LICENSE.md](LICENSE.md).

**Voiceback** - *Where voices from the past bring comfort to the present.*

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/sivaratrisrinivas/voiceback).

