#!/bin/bash

echo "Testing Voiceback webhook endpoints..."

# Test health check
echo "1. Testing /health endpoint:"
curl -s http://localhost:8000/health | jq '.'

echo -e "\n2. Testing /calls endpoint:"
curl -s http://localhost:8000/calls | jq '.'

echo -e "\n3. Testing /webhook with sample Vapi payload:"
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "type": "function-call",
      "functionCall": {
        "name": "respond_to_user",
        "parameters": {
          "transcript": "I am feeling really anxious today"
        }
      },
      "call": {
        "id": "test-call-123"
      }
    }
  }' | jq '.'

echo -e "\n4. Testing crisis detection:"
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "type": "function-call", 
      "functionCall": {
        "name": "respond_to_user",
        "parameters": {
          "transcript": "I want to kill myself"
        }
      },
      "call": {
        "id": "test-call-456"
      }
    }
  }' | jq '.'

echo -e "\nDone testing!" 