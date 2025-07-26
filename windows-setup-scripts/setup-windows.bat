@echo off
echo ============================================
echo Aman Cybersecurity Platform - Windows Setup
echo ============================================

echo.
echo Checking prerequisites...

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ first.
    echo Download from: https://python.org/downloads/
    pause
    exit /b 1
)

:: Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 16+ first.
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)

:: Check if MongoDB is installed and running
net start | findstr "MongoDB" >nul 2>&1
if errorlevel 1 (
    echo WARNING: MongoDB service not running. Attempting to start...
    net start MongoDB >nul 2>&1
    if errorlevel 1 (
        echo ERROR: MongoDB not found or failed to start.
        echo Please install MongoDB Community Server first.
        echo Download from: https://www.mongodb.com/try/download/community
        pause
        exit /b 1
    )
)

echo ✅ All prerequisites found!
echo.

:: Create project structure
echo Creating project directories...
mkdir backend >nul 2>&1
mkdir frontend >nul 2>&1
mkdir browser-extension >nul 2>&1
mkdir browser-extension\src >nul 2>&1
mkdir browser-extension\content >nul 2>&1
mkdir browser-extension\popup >nul 2>&1
mkdir browser-extension\icons >nul 2>&1

echo ✅ Project structure created!
echo.

echo Setting up Python backend...
cd backend

:: Create virtual environment
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install Python packages
echo Installing Python dependencies...
pip install fastapi uvicorn motor pymongo bcrypt python-jose[cryptography] python-multipart slowapi python-dotenv websockets pydantic email-validator

:: Install emergent integrations
echo Installing AI integration packages...
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

:: Create requirements.txt
pip freeze > requirements.txt

echo ✅ Backend setup complete!
cd ..
echo.

echo Setting up React frontend...
cd frontend

:: Install yarn globally if not present
npm list -g yarn >nul 2>&1
if errorlevel 1 (
    echo Installing Yarn package manager...
    npm install -g yarn
)

:: Install frontend dependencies
echo Installing React dependencies...
yarn install

echo ✅ Frontend setup complete!
cd ..
echo.

echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Copy all project files to their respective folders
echo 2. Create .env files in backend and frontend folders
echo 3. Run start-backend.bat to start the backend server
echo 4. Run start-frontend.bat to start the frontend server
echo 5. Load browser extension in Chrome
echo.
echo See WINDOWS_SETUP_GUIDE.md for detailed instructions.
echo.
pause