@echo off
echo ============================================
echo Aman Cybersecurity Platform - Setup Verification
echo ============================================

set "errors=0"

echo.
echo Checking prerequisites...

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found
    set /a errors+=1
) else (
    echo ✅ Python installed
)

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found
    set /a errors+=1
) else (
    echo ✅ Node.js installed
)

:: Check MongoDB
net start | findstr "MongoDB" >nul 2>&1
if errorlevel 1 (
    echo ❌ MongoDB not running
    set /a errors+=1
) else (
    echo ✅ MongoDB running
)

:: Check Yarn
yarn --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Yarn not found
    set /a errors+=1
) else (
    echo ✅ Yarn installed
)

echo.
echo Checking project structure...

:: Check directories
if exist "backend" (
    echo ✅ Backend directory exists
) else (
    echo ❌ Backend directory missing
    set /a errors+=1
)

if exist "frontend" (
    echo ✅ Frontend directory exists
) else (
    echo ❌ Frontend directory missing
    set /a errors+=1
)

if exist "browser-extension" (
    echo ✅ Browser extension directory exists
) else (
    echo ❌ Browser extension directory missing
    set /a errors+=1
)

echo.
echo Checking configuration files...

:: Check backend files
if exist "backend\.env" (
    echo ✅ Backend .env file exists
) else (
    echo ❌ Backend .env file missing
    set /a errors+=1
)

if exist "backend\server.py" (
    echo ✅ Backend server.py exists
) else (
    echo ❌ Backend server.py missing
    set /a errors+=1
)

if exist "backend\requirements.txt" (
    echo ✅ Backend requirements.txt exists
) else (
    echo ❌ Backend requirements.txt missing
    set /a errors+=1
)

:: Check frontend files
if exist "frontend\.env" (
    echo ✅ Frontend .env file exists
) else (
    echo ❌ Frontend .env file missing
    set /a errors+=1
)

if exist "frontend\package.json" (
    echo ✅ Frontend package.json exists
) else (
    echo ❌ Frontend package.json missing
    set /a errors+=1
)

:: Check extension files
if exist "browser-extension\manifest.json" (
    echo ✅ Extension manifest.json exists
) else (
    echo ❌ Extension manifest.json missing
    set /a errors+=1
)

if exist "browser-extension\src\background.js" (
    echo ✅ Extension background.js exists
) else (
    echo ❌ Extension background.js missing
    set /a errors+=1
)

echo.
echo ============================================
echo Verification Results
echo ============================================

if %errors% equ 0 (
    echo ✅ All checks passed! Your setup looks good.
    echo.
    echo Next steps:
    echo 1. Run start-backend.bat to start the backend server
    echo 2. Run start-frontend.bat to start the frontend server
    echo 3. Open http://localhost:3000 in your browser
    echo 4. Load browser extension in Chrome
) else (
    echo ❌ Found %errors% issues that need to be resolved.
    echo.
    echo Please check the items marked with ❌ above.
    echo See WINDOWS_SETUP_GUIDE.md for detailed instructions.
)

echo.
pause