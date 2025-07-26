@echo off
echo ============================================
echo Starting Aman Cybersecurity Frontend Server
echo ============================================

:: Check if we're in the correct directory
if not exist "frontend" (
    echo ERROR: Please run this script from the main project directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

cd frontend

:: Check if node_modules exists
if not exist "node_modules" (
    echo ERROR: Dependencies not installed. Please run setup-windows.bat first.
    pause
    exit /b 1
)

:: Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found in frontend directory.
    echo Please create .env file with required configuration.
    echo See WINDOWS_SETUP_GUIDE.md for .env file contents.
    pause
    exit /b 1
)

echo.
echo Starting React development server on http://localhost:3000
echo The browser should open automatically
echo Press Ctrl+C to stop the server
echo.

:: Start the frontend server
yarn start

echo.
echo Frontend server stopped.
pause