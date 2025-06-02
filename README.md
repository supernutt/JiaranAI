# AI Learning Lab

A unified platform for interactive AI-powered classroom discussions and educational video generation.

## Features

- **Interactive Classroom**: AI-powered classroom discussions with multiple student personas and a teacher
- **Video Generation**: Create educational animations using Manim engine with AI-generated content
- **Unified Server**: Both features run on a single FastAPI server

## Quick Start

1. Install dependencies:
```bash
cd ai_learning_lab
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Copy and edit the .env file with your OpenAI API key
cp .env.example .env
```

3. Start the server:
```bash
./start_server.sh
```

Or manually:
```bash
cd ai_learning_lab
python -m uvicorn server.main:app --reload --port 8000
```

## API Endpoints

### Classroom
- `POST /classroom/start` - Start a new classroom session
- `POST /classroom/turn/{session_id}` - Send a message to the classroom

### Video Generation
- `GET /animations/scenes` - List available animation scenes
- `POST /animations/generate` - Generate a new animation
- `GET /animations/status/{task_id}` - Check animation generation status
- `GET /animations/video/{path}` - Access generated videos

## Frontend

The React frontend is in the `frontend/` directory. Start it with:
```bash
cd frontend
npm start
```

Server runs on http://localhost:8000
Frontend runs on http://localhost:3000 