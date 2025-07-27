@echo off
echo ========================================
echo AMAN CYBERSECURITY - NO JWT SETUP
echo ========================================

echo.
echo Stopping any running servers...
taskkill /f /im uvicorn.exe 2>nul
taskkill /f /im node.exe 2>nul

echo.
echo Installing backend dependencies (NO JWT)...
cd backend

REM Remove ALL JWT packages
pip uninstall PyJWT jwt python-jose -y 2>nul

REM Install only required packages
pip install passlib[bcrypt]==1.7.4
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install motor==3.3.2
pip install python-multipart==0.0.6
pip install slowapi==0.1.9
pip install python-dotenv==1.0.0
pip install pydantic==2.5.0

echo.
echo Testing auth module...
python -c "from auth import create_access_token; print('✅ NO-JWT Auth works!')" || (
    echo ❌ Auth module failed
    pause
    exit /b 1
)

echo.
echo Starting backend server...
start "Backend Server" cmd /k "uvicorn server:app --host 0.0.0.0 --port 8001 --reload"

echo Waiting for backend to start...
timeout /t 5 /nobreak

echo.
echo Installing frontend dependencies...
cd ..\frontend
yarn install --legacy-peer-deps

echo.
echo Starting frontend server...
start "Frontend Server" cmd /k "yarn start"

echo.
echo ========================================
echo ✅ NO-JWT SETUP COMPLETE!
echo ========================================
echo.
echo Backend: http://localhost:8001
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8001/docs
echo Auth System: Simple Token (No JWT)
echo.
echo 1. Load browser extension from chrome://extensions/
echo 2. Register/Login on frontend
echo 3. Test email scanning
echo.
pause