#!/bin/bash

# Start El Pais Vocabulary Builder
# Runs both the API server and frontend dev server

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Start API server in background
echo "Starting API server on http://localhost:8020..."
uvicorn api.app:app --reload --port 8020 &
API_PID=$!

# Start frontend dev server
echo "Starting frontend on http://localhost:3002..."
cd frontend && PORT=3002 npm run dev &
FRONTEND_PID=$!

# Handle cleanup on exit
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $API_PID 2>/dev/null
  kill $FRONTEND_PID 2>/dev/null
  exit 0
}

trap cleanup SIGINT SIGTERM

echo ""
echo "Both servers running. Press Ctrl+C to stop."
echo ""

# Wait for either process to exit
wait
