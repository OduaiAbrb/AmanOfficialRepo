@echo off
echo ============================================
echo Starting Aman Cybersecurity Backend Server
echo ============================================

:: Check if we're in the correct directory
if not exist "backend" (
    echo ERROR: Please run this script from the main project directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

cd backend

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found. Please run setup-windows.bat first.
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating Python virtual environment...
call venv\Scripts\activate.bat

:: Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found in backend directory.
    echo Please create .env file with required configuration.
    echo See WINDOWS_SETUP_GUIDE.md for .env file contents.
    pause
    exit /b 1
)

:: Start MongoDB if not running
net start | findstr "MongoDB" >nul 2>&1
if errorlevel 1 (
    echo Starting MongoDB...
    net start MongoDB >nul 2>&1
)

echo.
echo Starting FastAPI server on http://localhost:8001
echo Press Ctrl+C to stop the server
echo.

:: Start the server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

echo.
echo Backend server stopped.
pause