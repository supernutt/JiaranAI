#!/bin/bash

echo "Starting AI Learning Lab Unified Server..."
echo "This server includes both classroom discussions and video generation capabilities."
echo ""

cd ai_learning_lab
python -m uvicorn server.main:app --reload --port 8000

echo ""
echo "Server stopped." 