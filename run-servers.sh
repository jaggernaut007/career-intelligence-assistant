#!/bin/bash

# Career Intelligence Platform - Server Startup Script
# This script starts both the backend (FastAPI) and frontend (React) servers

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Store PIDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"

    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}Backend server stopped${NC}"
    fi

    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}Frontend server stopped${NC}"
    fi

    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Career Intelligence Platform${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Copying from .env.example...${NC}"
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        echo -e "${YELLOW}Please edit .env with your API keys before using the application.${NC}"
    else
        echo -e "${RED}Error: .env.example not found. Please create a .env file.${NC}"
    fi
fi

# Start Backend Server
echo -e "\n${GREEN}Starting Backend Server (FastAPI)...${NC}"
cd "$BACKEND_DIR"
uv run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}Backend running on http://localhost:8000${NC}"

# Give backend a moment to start
sleep 2

# Start Frontend Server
echo -e "\n${GREEN}Starting Frontend Server (React + Vite)...${NC}"
cd "$FRONTEND_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend running on http://localhost:5173${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Both servers are running!${NC}"
echo -e "${GREEN}  Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}  Frontend: http://localhost:5173${NC}"
echo -e "${GREEN}  Press Ctrl+C to stop both servers${NC}"
echo -e "${GREEN}========================================${NC}"

# Wait for both processes
wait
