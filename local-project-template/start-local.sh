#!/bin/bash

echo "🚀 Starting Aman Cybersecurity Platform Locally..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if MongoDB is running
echo -e "${BLUE}📊 Checking MongoDB...${NC}"
if ! pgrep -x "mongod" > /dev/null; then
    echo -e "${YELLOW}⚠️  MongoDB not running. Please start MongoDB first:${NC}"
    echo "   mongod --dbpath /your/data/path"
    echo "   OR on macOS with Homebrew: brew services start mongodb/brew/mongodb-community"
    exit 1
else
    echo -e "${GREEN}✅ MongoDB is running${NC}"
fi

# Function to start backend
start_backend() {
    echo -e "${BLUE}🐍 Starting Backend...${NC}"
    cd backend/
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Start backend in background
    uvicorn server:app --host 0.0.0.0 --port 8001 --reload &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    cd ..
}

# Function to start frontend
start_frontend() {
    echo -e "${BLUE}⚛️  Starting Frontend...${NC}"
    cd frontend/
    
    # Start frontend in background
    if command -v yarn &> /dev/null; then
        yarn start &
    else
        npm start &
    fi
    FRONTEND_PID=$!
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
    cd ..
}

# Start services
start_backend
sleep 3
start_frontend

echo -e "${GREEN}🎉 Aman Cybersecurity Platform is starting up!${NC}"
echo ""
echo -e "${BLUE}📱 Access URLs:${NC}"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8001" 
echo "   API Docs:  http://localhost:8001/docs"
echo "   Admin:     http://localhost:3000/admin"
echo ""
echo -e "${YELLOW}👤 Test Accounts:${NC}"
echo "   Regular: test@company.com / TestPass123!"
echo "   Admin:   admin@cybersec.com / AdminPass123!"
echo ""
echo -e "${RED}🛑 To stop services: Press Ctrl+C or run 'pkill -f uvicorn' and 'pkill -f react-scripts'${NC}"

# Wait for user input to stop
echo -e "${BLUE}Press any key to stop all services...${NC}"
read -n 1 -s

# Kill processes
echo -e "${YELLOW}🛑 Stopping services...${NC}"
pkill -f "uvicorn server:app" 2>/dev/null
pkill -f "react-scripts start" 2>/dev/null
pkill -f "node.*webpack" 2>/dev/null

echo -e "${GREEN}✅ All services stopped${NC}"