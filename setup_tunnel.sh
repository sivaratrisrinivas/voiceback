#!/bin/bash

echo "🔗 WEBHOOK TUNNEL SETUP - Multiple Options"
echo "=========================================="

# Check if Flask server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Flask server not running. Start it first:"
    echo "   python src/main.py"
    exit 1
fi

echo "✅ Flask server detected on localhost:8000"
echo ""

echo "Choose a tunneling option:"
echo "1. ngrok (requires free signup)"
echo "2. localtunnel (no signup needed)"  
echo "3. bore (no signup needed)"
echo "4. cloudflared (Cloudflare tunnel)"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "Setting up ngrok..."
        if command -v ngrok &> /dev/null; then
            echo "Starting ngrok tunnel..."
            ngrok http 8000
        else
            echo "❌ ngrok not installed. Install with:"
            echo "   sudo apt install ngrok"
            echo "   Then sign up at: https://dashboard.ngrok.com/signup"
        fi
        ;;
    2)
        echo "Setting up localtunnel..."
        if command -v npx &> /dev/null; then
            echo "🔗 Starting localtunnel (no signup required)..."
            echo "⏳ This may take a moment..."
            npx localtunnel --port 8000 --subdomain voiceback-$(date +%s)
        else
            echo "❌ Node.js/npx not found. Install with:"
            echo "   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
            echo "   sudo apt-get install -y nodejs"
        fi
        ;;
    3)
        echo "Setting up bore tunnel..."
        if command -v bore &> /dev/null; then
            echo "🔗 Starting bore tunnel..."
            bore local 8000 --to bore.pub
        else
            echo "Installing bore..."
            curl -L https://github.com/ekzhang/bore/releases/latest/download/bore-linux-x86_64 -o bore
            chmod +x bore
            sudo mv bore /usr/local/bin/
            echo "🔗 Starting bore tunnel..."
            bore local 8000 --to bore.pub
        fi
        ;;
    4)
        echo "Setting up Cloudflare tunnel..."
        if command -v cloudflared &> /dev/null; then
            echo "🔗 Starting Cloudflare tunnel..."
            cloudflared tunnel --url http://localhost:8000
        else
            echo "Installing cloudflared..."
            wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
            sudo dpkg -i cloudflared-linux-amd64.deb
            rm cloudflared-linux-amd64.deb
            echo "🔗 Starting Cloudflare tunnel..."
            cloudflared tunnel --url http://localhost:8000
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac 