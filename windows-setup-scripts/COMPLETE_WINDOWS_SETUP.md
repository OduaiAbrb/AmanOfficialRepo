# 🪟 COMPLETE Windows Setup for Aman Cybersecurity Platform

## 📦 What You Need to Download/Install First

### Required Software Downloads
1. **MongoDB Community Server**: https://www.mongodb.com/try/download/community
   - Version: Latest (6.0+)
   - Select: Windows x64, MSI
   - During install: Enable "Run as service" + Install Compass

2. **Node.js**: https://nodejs.org/
   - Download: LTS version (18.x or higher)
   - Install with default settings

3. **Python**: https://python.org/downloads/
   - Download: Latest 3.8+ version
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation

4. **Git**: https://git-scm.com/download/win (optional, for version control)

## 🗂️ Files You Need to Copy

### Backend Files (.py files)
Copy all these files to your `backend/` folder:
```
server.py              (Main FastAPI application)
database.py            (MongoDB connection - FIXED VERSION PROVIDED)
auth.py                (User authentication)
security.py            (Security utilities)
models.py              (Data models)
ai_scanner.py          (AI-powered scanning)
ai_cost_manager.py     (AI cost tracking)
admin_manager.py       (Admin panel backend)
email_scanner.py       (Email analysis logic)
feedback_system.py     (User feedback)
threat_intelligence.py (Threat detection)
realtime_manager.py    (WebSocket manager)
requirements.txt       (Python dependencies)
```

### Frontend Files (React app)
Copy all these to your `frontend/` folder:
```
package.json           (Node.js dependencies)
tailwind.config.js     (CSS framework config)
postcss.config.js      (CSS processing)
src/                   (All React components)
├── App.js
├── index.js
├── components/
│   ├── LandingPage.js
│   ├── Dashboard.js
│   ├── LoginForm.js
│   ├── RegisterForm.js
│   ├── AuthPage.js
│   ├── ProtectedRoute.js
│   ├── RealTimeNotifications.js
│   └── AdminDashboard.js
├── contexts/
│   └── AuthContext.js
└── hooks/
    └── useWebSocket.js
public/                (Static files)
├── index.html
└── extension-auth.js
```

### Browser Extension Files
Copy all these to your `browser-extension/` folder:
```
manifest.json          (Extension configuration)
src/
└── background.js      (Service worker - FIXED VERSION PROVIDED)
content/
├── content.js         (Gmail/Outlook integration)
└── content.css        (Styling)
popup/
├── popup.html         (Extension popup)
├── popup.css          (Popup styling)
└── popup.js           (Popup functionality)
icons/                 (Extension icons)
├── icon16.png
├── icon48.png
└── icon128.png
```

## 🔧 Quick Setup Commands

### Option 1: Automated Setup (Recommended)
1. Run the setup script: `windows-setup-scripts\setup-windows.bat`
2. Copy all project files to their folders
3. Create the .env files (see below)
4. Run `windows-setup-scripts\start-backend.bat`
5. Run `windows-setup-scripts\start-frontend.bat` (in new window)

### Option 2: Manual Setup
```powershell
# 1. Create project structure
mkdir aman-cybersecurity-platform
cd aman-cybersecurity-platform
mkdir backend frontend browser-extension

# 2. Setup Python backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# 3. Setup React frontend (new window)
cd frontend
npm install -g yarn
yarn install

# 4. Start services (separate windows)
# Backend: uvicorn server:app --host 0.0.0.0 --port 8001 --reload
# Frontend: yarn start
```

## 📝 Configuration Files (.env)

### Backend Configuration (`backend\.env`)
```env
MONGO_URL=mongodb://localhost:27017
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-for-production
ENVIRONMENT=development
GEMINI_API_KEY=AIzaSyBUPx4B7pH-f-ECKgGrl-4zCihpRB2hglY
```

### Frontend Configuration (`frontend\.env`)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_LOCAL_BASE_URL=http://localhost:8001
DANGEROUSLY_DISABLE_HOST_CHECK=true
```

## 🎯 Testing Your Setup

### 1. Verify Services Are Running
- MongoDB: Service should auto-start with Windows
- Backend: http://localhost:8001 (API docs at /docs)
- Frontend: http://localhost:3000 (main website)

### 2. Create Test Account
```
Name: Test User
Email: test@company.com
Organization: Test Company
Password: TestPass123!
```

### 3. Test Core Features
1. **Registration/Login**: Create and login with test account
2. **Dashboard**: Should show real-time statistics
3. **Email Scanning**: Test via API docs (http://localhost:8001/docs)
4. **Browser Extension**: Load in Chrome from `chrome://extensions/`

### 4. API Testing Examples
Go to http://localhost:8001/docs and test:

**Email Scan Test:**
```json
{
  "email_subject": "Urgent: Verify Your Account",
  "email_body": "Click here to verify your account immediately",
  "sender": "noreply@suspicious-site.com",
  "recipient": "test@company.com"
}
```

**Link Scan Test:**
```json
{
  "url": "http://bit.ly/suspicious-link",
  "context": "Click here for free money"
}
```

## 🔍 Troubleshooting Guide

### MongoDB Issues
```powershell
# Check if MongoDB is running
net start | findstr MongoDB

# Start MongoDB manually
net start MongoDB

# If MongoDB won't start, check Windows Services:
# Windows Key + R → services.msc → Find "MongoDB Server"
```

### Python Issues
```powershell
# Python not found
python --version
# If error, reinstall Python with "Add to PATH" checked

# Virtual environment issues
python -m venv venv --clear
venv\Scripts\activate
```

### React Issues
```powershell
# Port 3000 busy
# Find what's using port: netstat -ano | findstr :3000
# Kill process: taskkill /PID <process_id> /F

# Dependency issues
npm install -g yarn
yarn install --legacy-peer-deps
```

### Browser Extension Issues
1. Go to `chrome://extensions/`
2. Enable "Developer mode"
3. Check for errors in extension
4. Try reloading extension
5. Check browser console (F12) for errors

## 📊 What Should Work After Setup

- ✅ **Landing Page**: Professional cybersecurity website
- ✅ **Authentication**: User registration and login
- ✅ **Dashboard**: Real-time threat statistics
- ✅ **AI Scanning**: Email and link analysis with Gemini AI
- ✅ **Browser Extension**: Gmail integration with threat detection
- ✅ **Admin Panel**: User management (create admin user first)
- ✅ **Real-time Updates**: WebSocket notifications
- ✅ **API Documentation**: Interactive testing interface

## 🚨 Common Error Solutions

**"Module not found" errors:**
- Make sure you activated the Python virtual environment
- Install missing packages: `pip install <package-name>`

**"Permission denied" errors:**
- Run Command Prompt as Administrator
- Check Windows Defender isn't blocking Python

**"Port already in use" errors:**
- Change ports in .env files
- Or kill processes using the ports

**Database connection errors:**
- Ensure MongoDB service is running
- Check MongoDB Compass can connect to localhost:27017

**AI scanning not working:**
- Verify Gemini API key is valid
- Check internet connection
- AI will fallback to basic scanning if unavailable

## 🎉 Success Indicators

If setup is successful, you should see:

1. **Backend Console**: "Application startup completed successfully"
2. **Frontend Console**: "webpack compiled successfully"
3. **Website Loading**: Landing page at localhost:3000
4. **API Working**: Can register/login users
5. **Extension Active**: Shows up in Chrome extensions

## 📞 Support

If you encounter issues:
1. Check the command prompt windows for error messages
2. Verify all files were copied correctly
3. Ensure .env files are created properly
4. Check Windows Firewall isn't blocking connections
5. Try running Command Prompt as Administrator

---

**🚀 Once everything works, you'll have a complete AI-powered cybersecurity platform running locally on Windows!**