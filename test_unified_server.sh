#!/bin/bash

echo "Testing AI Learning Lab Unified Server..."
echo "=========================================="

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s http://localhost:8000/health | jq .
echo ""

# Test classroom functionality
echo "2. Testing classroom functionality..."
echo "   Creating new session..."
SESSION_RESPONSE=$(curl -s -X POST "http://localhost:8000/classroom/start" -H "Content-Type: application/json" -d '{"topic": "physics"}')
SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.sessionId')
echo "   Session ID: $SESSION_ID"

echo "   Sending message to classroom..."
curl -s -X POST "http://localhost:8000/classroom/turn/$SESSION_ID" -H "Content-Type: application/json" -d '{"userMessage": "What is gravity?"}' | jq '.messages[0].author, .messages[0].text'
echo ""

# Test animation functionality
echo "3. Testing animation functionality..."
echo "   Listing available scenes..."
curl -s http://localhost:8000/animations/scenes | jq '.scenes[0:3]'

echo "   Generating animation..."
ANIMATION_RESPONSE=$(curl -s -X POST "http://localhost:8000/animations/generate" -H "Content-Type: application/json" -d '{"prompt": "Create a simple red square", "quality": "low"}')
TASK_ID=$(echo $ANIMATION_RESPONSE | jq -r '.task_id')
echo "   Task ID: $TASK_ID"

echo "   Waiting for animation to complete..."
sleep 8

echo "   Checking animation status..."
curl -s http://localhost:8000/animations/status/$TASK_ID | jq '.status, .result_url'

echo ""
echo "=========================================="
echo "All tests completed!" 