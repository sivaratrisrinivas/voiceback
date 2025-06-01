#!/bin/bash

echo "🎤 VOICEBACK VOICE AGENT - QUICK SETUP FOR FULL VOICE TESTING"
echo "============================================================"

# Check if Flask server is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Flask server is running on localhost:8000"
else
    echo "❌ Flask server not running. Please start it first:"
    echo "   python src/main.py"
    exit 1
fi

# Start ngrok
echo ""
echo "🔗 Starting ngrok to expose your webhook..."
echo "⏳ This will create a public URL for Vapi to reach your server"

# Kill any existing ngrok processes
pkill -f ngrok 2>/dev/null

# Start ngrok in background
ngrok http 8000 > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get the public URL
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null)

if [ "$PUBLIC_URL" != "null" ] && [ ! -z "$PUBLIC_URL" ]; then
    echo "✅ ngrok tunnel created successfully!"
    echo ""
    echo "📞 YOUR WEBHOOK URLS:"
    echo "   Webhook: $PUBLIC_URL/webhook"
    echo "   Health:  $PUBLIC_URL/health" 
    echo "   Calls:   $PUBLIC_URL/calls"
    echo ""
    
    # Test the public URL
    echo "🧪 Testing public webhook..."
    if curl -s "$PUBLIC_URL/health" > /dev/null; then
        echo "✅ Public webhook is accessible!"
    else
        echo "⚠️  Public webhook test failed - but URL is ready"
    fi
    
    echo ""
    echo "🎯 NEXT STEPS FOR VOICE TESTING:"
    echo ""
    echo "1. **Copy this webhook URL**: $PUBLIC_URL/webhook"
    echo ""
    echo "2. **Go to Vapi Dashboard**: https://dashboard.vapi.ai"
    echo ""
    echo "3. **Create Assistant with these settings**:"
    echo "   - Model Provider: Custom"
    echo "   - Model URL: $PUBLIC_URL/webhook"
    echo "   - Voice Provider: PlayHT"
    echo "   - Voice: Jennifer"
    echo "   - Transcriber: Deepgram Nova-2"
    echo ""
    echo "4. **Test Scenarios** (call your Vapi number and say):"
    echo "   🔹 \"I'm feeling anxious about work lately\""
    echo "   🔹 \"My relationship is having problems\""
    echo "   🔹 \"I feel hopeless and want to end it all\" (crisis test)"
    echo "   🔹 \"I'm having a great day today!\""
    echo ""
    echo "5. **What to Expect**:"
    echo "   ✅ Empathetic, natural responses"
    echo "   ✅ Crisis detection with hotline numbers"
    echo "   ✅ Response time under 3 seconds"
    echo "   ✅ Professional disclaimer at end"
    echo ""
    echo "⚠️  IMPORTANT: Keep this terminal open - ngrok must stay running!"
    echo "   Press Ctrl+C to stop ngrok when done testing"
    echo ""
    echo "🎉 Your voice agent is ready for live testing!"
    
    # Wait for user to stop
    echo ""
    echo "Press Ctrl+C to stop ngrok and end voice testing..."
    trap "echo ''; echo '🛑 Stopping ngrok...'; kill $NGROK_PID 2>/dev/null; echo '✅ Voice testing session ended.'; exit 0" SIGINT
    
    # Keep script running
    while true; do
        sleep 1
    done
    
else
    echo "❌ Failed to get ngrok URL. Please check ngrok installation."
    echo "   Try: sudo apt install ngrok"
    exit 1
fi 