# Voiceback - LLM-Powered Voice Agent

A compassionate voice agent that provides emotional support and encouragement through natural AI conversations.

## 🎯 Simple User Journey

1. **User speaks** → 2. **Vapi transcribes** → 3. **Flask receives transcript** → 4. **LLM generates response** → 5. **Flask returns response** → 6. **Vapi speaks** → 7. **User hears support**

## ✨ Key Features

- **Natural Conversations**: LLM-powered responses that understand context and provide genuine support
- **Crisis Detection**: Built-in safety with emergency hotline information for crisis situations
- **Multiple LLM Support**: Compatible with OpenAI, Anthropic Claude, and xAI
- **Simple Architecture**: Clean, maintainable codebase without complex emotion detection
- **Real-time Processing**: Instant responses through Vapi webhook integration

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│    User     │    │     Vapi     │    │   Flask     │    │     LLM     │
│   (Voice)   │◄──►│  (Speech)    │◄──►│  (Webhook)  │◄──►│ (Response)  │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
```

### Core Components

- **CallHandler**: Processes Vapi webhooks and manages LLM conversations
- **VapiClient**: Handles Vapi API integration and health checks  
- **Flask Server**: Webhook endpoint for real-time call processing
- **Crisis Detection**: Keyword-based safety system with emergency resources

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/yourusername/voiceback.git
cd voiceback

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.template` to `.env` and configure:

```env
# Required
VAPI_API_KEY=your_vapi_api_key
PHONE_NUMBER=your_vapi_phone_number
OPENAI_API_KEY=your_openai_api_key

# Optional
WEBHOOK_HOST=localhost
WEBHOOK_PORT=5000
LLM_PROVIDER=openai
LOG_LEVEL=INFO
```

### 3. Run the Agent

```bash
# Start the voice agent
python src/main.py
```

The server will start and display:
```
Voiceback Voice Agent is running!
Webhook endpoints:
  - Webhook: http://localhost:5000/webhook
  - Health Check: http://localhost:5000/health  
  - Active Calls: http://localhost:5000/calls
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_call_handler.py -v
pytest tests/test_main.py -v
pytest tests/test_vapi_client.py -v

# See the example in action
python example_usage.py
```

## 🔧 API Endpoints

### Webhook (`POST /webhook`)
Receives Vapi call events and processes user voice input through LLM.

### Health Check (`GET /health`)
```json
{
  "status": "healthy",
  "service": "Voiceback Voice Agent", 
  "checks": {
    "vapi": {"status": "connected"},
    "llm": {"provider": "openai", "status": "configured"},
    "calls": {"count": 0, "status": "active"}
  }
}
```

### Active Calls (`GET /calls`)
```json
{
  "status": "success",
  "calls": {"call-123": {"status": "active", "started_at": "2024-01-01T12:00:00"}},
  "count": 1
}
```

## 🛡️ Safety Features

**Crisis Detection**: Automatically detects keywords like "suicide", "kill myself", etc. and provides:
- US Suicide & Crisis Lifeline: **988**
- India AASRA: **9152987821**  
- Immediate emotional support and professional help guidance

**Disclaimer**: All responses include "Remember, this is for inspiration and support, not professional advice."

## 📁 Project Structure

```
voiceback/
├── src/
│   ├── main.py              # Flask server entry point
│   ├── call_handler.py      # LLM-powered webhook processing  
│   └── vapi_client.py       # Vapi API integration
├── tests/
│   ├── test_call_handler.py # CallHandler tests
│   ├── test_main.py         # Main server tests
│   └── test_vapi_client.py  # VapiClient tests
├── example_usage.py         # Demo script
├── requirements.txt         # Python dependencies
└── .env.template           # Environment configuration template
```

## 🔄 Development

### Adding New LLM Providers

1. Update `CallHandler.__init__()` to handle new provider
2. Add API key validation in `main.py`
3. Implement provider-specific response generation in `_generate_llm_response()`

### Customizing Responses

Modify the `system_prompt` in `CallHandler` to adjust the agent's personality and response style.

### Extending Crisis Detection

Add keywords to `CRISIS_KEYWORDS` list or implement more sophisticated detection logic.

## 📊 Benefits vs Previous Architecture

| Aspect | Old Complex System | New LLM System |
|--------|-------------------|----------------|
| **Responses** | Hardcoded quotes | Natural AI conversations |
| **Input Handling** | Complex text processing | Direct LLM understanding |
| **Maintenance** | Multiple config files | Simple system prompt |
| **Flexibility** | Fixed emotion categories | Handles any user input |
| **Codebase** | ~150KB+ components | ~30KB clean code |

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 Email: support@voiceback.ai
- 📱 Phone: Available through Vapi integration
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/voiceback/issues)

---

**Voiceback** - Providing compassionate support through the power of voice and AI 💙

