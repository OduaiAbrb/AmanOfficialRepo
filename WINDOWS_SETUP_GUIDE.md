# 🪟 Aman Cybersecurity Platform - Windows Setup Guide

This guide provides complete step-by-step instructions for setting up the Aman Cybersecurity Platform on Windows laptops.

## 📋 Prerequisites - Install These First

### 1. Download and Install Required Software

**MongoDB Community Server**
```
1. Go to: https://www.mongodb.com/try/download/community
2. Select: Windows, MSI Package, Latest Version
3. Download and run the installer
4. During installation:
   - Select "Complete" setup type
   - Check "Install MongoDB as a Service" 
   - Check "Run service as Network Service user"
   - Install MongoDB Compass (GUI tool)
5. MongoDB will start automatically as a Windows service
```

**Node.js (v16 or higher)**
```
1. Go to: https://nodejs.org/
2. Download the Windows installer (LTS version)
3. Run installer with default settings
4. Open Command Prompt and verify:
   node --version
   npm --version
```

**Python (v3.8 or higher)**
```
1. Go to: https://www.python.org/downloads/
2. Download Python for Windows
3. IMPORTANT: Check "Add Python to PATH" during installation
4. Open Command Prompt and verify:
   python --version
   pip --version
```

**Git for Windows**
```
1. Go to: https://git-scm.com/download/win
2. Download and install with default settings
```

**Yarn Package Manager**
```
1. Open Command Prompt as Administrator
2. Run: npm install -g yarn
3. Verify: yarn --version
```

## 📁 Step 1: Create Project Directory

```powershell
# Open Command Prompt or PowerShell
# Navigate to where you want to create the project (e.g., Desktop)
cd C:\Users\%USERNAME%\Desktop

# Create main project directory
mkdir aman-cybersecurity-platform
cd aman-cybersecurity-platform

# Create subdirectories
mkdir backend frontend browser-extension
```

## 📂 Step 2: Copy Project Files

Create the following files in your project directory:

### Backend Files

Create `backend\.env`:
```env
MONGO_URL=mongodb://localhost:27017
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-for-production
ENVIRONMENT=development
GEMINI_API_KEY=AIzaSyBUPx4B7pH-f-ECKgGrl-4zCihpRB2hglY
```

### Frontend Files

Create `frontend\.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_LOCAL_BASE_URL=http://localhost:8001
DANGEROUSLY_DISABLE_HOST_CHECK=true
```

### Copy All Code Files

You'll need to copy all the Python files, React components, and browser extension files from the original project. The main files include:

**Backend:**
- `server.py` (main FastAPI app)
- `database.py` (MongoDB connection)
- `auth.py` (authentication)
- `security.py` (security utilities)
- `models.py` (data models)
- `ai_scanner.py` (AI scanning)
- `requirements.txt` (Python dependencies)
- All other `.py` files

**Frontend:**
- `package.json` (dependencies)
- `src/` folder with all React components
- `public/` folder
- `tailwind.config.js`
- `postcss.config.js`

**Browser Extension:**
- `manifest.json`
- `src/background.js` (service worker)
- `content/` folder
- `popup/` folder
- `icons/` folder

## 🗄️ Step 3: Setup MongoDB

```powershell
# MongoDB should already be running as a Windows service
# Verify it's running:
net start MongoDB

# If not running, start it:
net start MongoDB

# To check MongoDB status, open MongoDB Compass
# Connect to: mongodb://localhost:27017
```

## 🐍 Step 4: Setup Python Backend

```powershell
# Navigate to backend folder
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# You should see (venv) in your command prompt

# Install Python dependencies
pip install fastapi uvicorn motor pymongo bcryptjs python-jose[cryptography] python-multipart slowapi

# Install emergent integrations (for AI)
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Install other required packages
pip install python-dotenv websockets pydantic email-validator

# Create requirements.txt with all installed packages
pip freeze > requirements.txt

# Start the backend server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
```

**Leave this Command Prompt window open!** The backend server needs to keep running.

## ⚛️ Step 5: Setup React Frontend

Open a NEW Command Prompt window:

```powershell
# Navigate to frontend folder
cd C:\Users\%USERNAME%\Desktop\aman-cybersecurity-platform\frontend

# Install dependencies
yarn install

# If you get errors, try:
yarn install --legacy-peer-deps

# Start the frontend development server
yarn start
```

You should see:
```
webpack compiled successfully
Local:            http://localhost:3000
On Your Network:  http://192.168.x.x:3000
```

Your browser should automatically open to http://localhost:3000

**Leave this Command Prompt window open too!**

## 🌐 Step 6: Verify Everything Works

### Test the Application
1. **Frontend**: http://localhost:3000 should show the landing page
2. **Backend API**: http://localhost:8001/docs should show API documentation
3. **Health Check**: http://localhost:8001/api/health should return status

### Create Test Account
1. Go to http://localhost:3000
2. Click "Get Started" or navigate to registration
3. Create an account with:
   - Name: Test User
   - Email: test@company.com
   - Organization: Test Company
   - Password: TestPass123!

### Test Core Features
1. **Login**: Use your test account credentials
2. **Dashboard**: Should show real-time statistics
3. **API Testing**: Go to http://localhost:8001/docs to test email scanning

## 🔌 Step 7: Setup Browser Extension

### Load Extension in Chrome
1. Open Google Chrome
2. Go to: `chrome://extensions/`
3. Enable "Developer mode" (toggle in top-right)
4. Click "Load unpacked"
5. Select your `browser-extension` folder
6. The extension should appear in your extensions list

### Test Extension
1. Go to Gmail (https://gmail.com)
2. Open an email
3. The extension should analyze it automatically
4. Check the extension popup by clicking the extension icon

## 🚨 Common Issues and Solutions

### MongoDB Issues
```powershell
# If MongoDB won't start:
net stop MongoDB
net start MongoDB

# If connection fails, check if MongoDB is running:
tasklist | findstr mongod
```

### Python Issues
```powershell
# If Python not found:
# Reinstall Python with "Add to PATH" checked

# If pip not found:
python -m pip install --upgrade pip

# If virtual environment issues:
python -m venv venv --clear
```

### Node.js Issues
```powershell
# If yarn not found:
npm install -g yarn

# If port 3000 busy:
# Find process: netstat -ano | findstr :3000
# Kill process: taskkill /PID <process_id> /F
```

### Extension Issues
```
1. Check Chrome://extensions for errors
2. Verify all extension files are present
3. Check browser console for JavaScript errors
4. Try reloading the extension
```

## 📱 Step 8: Testing Workflow

### Complete Testing Checklist
1. ✅ **Registration**: Create new user account
2. ✅ **Login**: Authenticate with credentials
3. ✅ **Dashboard**: View real-time statistics
4. ✅ **Email Scanning**: Test via API docs
5. ✅ **Browser Extension**: Test on Gmail
6. ✅ **Real-time Updates**: Check WebSocket connection
7. ✅ **Admin Panel**: Create admin user and test

### API Testing via Swagger UI
1. Go to: http://localhost:8001/docs
2. Click "Authorize" and enter your access token
3. Test email scanning endpoint: `POST /api/scan/email`
4. Test link scanning endpoint: `POST /api/scan/link`

## 🔧 Development Commands Reference

```powershell
# Start Backend (in backend folder)
venv\Scripts\activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Start Frontend (in frontend folder)  
yarn start

# Start MongoDB Service
net start MongoDB

# Stop MongoDB Service
net stop MongoDB

# View Backend Logs
# Logs appear in the command prompt where uvicorn is running

# Restart Services (if needed)
# Press Ctrl+C in backend terminal, then restart uvicorn
# Press Ctrl+C in frontend terminal, then run yarn start again
```

## 🔒 Security Notes

- The JWT secret key should be changed for production
- The Gemini API key is included for testing (change for production)
- MongoDB runs without authentication in this local setup
- CORS is configured for localhost only

## 🎯 What Should Work Now

After completing this setup, you should have:

- ✅ **Landing Page**: Professional cybersecurity website
- ✅ **User Authentication**: Register and login functionality  
- ✅ **Dashboard**: Real-time statistics and email scan history
- ✅ **AI-Powered Scanning**: Email and link analysis with Gemini AI
- ✅ **Browser Extension**: Gmail integration with threat detection
- ✅ **Admin Panel**: User management and system monitoring
- ✅ **Real-time Updates**: WebSocket notifications
- ✅ **API Documentation**: Interactive Swagger UI

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs** in your command prompt windows
2. **Verify all services are running** (MongoDB, Backend, Frontend)
3. **Check browser console** for JavaScript errors
4. **Ensure all files are copied correctly** from the original project
5. **Check firewall settings** if services can't communicate

## 🚀 Next Steps

Once everything is working:

1. **Create an admin user** for accessing admin panel
2. **Test all scanning features** with real emails
3. **Customize the branding** and configuration
4. **Add more test users** for comprehensive testing
5. **Plan for production deployment**

---

**🎉 Congratulations!** You now have a fully functional AI-powered cybersecurity platform running on your Windows machine!