# 🏠 Aman Cybersecurity Platform - Local Development

> AI-powered cybersecurity platform with real-time threat detection, admin panel, and browser extension

## 🚀 Quick Start

```bash
# 1. Install prerequisites
# - Node.js v16+, Python 3.8+, MongoDB, Git

# 2. Start MongoDB
mongod --dbpath /your/mongodb/data/path

# 3. Install dependencies
cd backend && pip install -r requirements.txt && cd ..
cd frontend && yarn install && cd ..

# 4. Start everything
./start-local.sh
```

## 📋 Prerequisites

Install these on your local machine:

- **Node.js v16+**: [Download here](https://nodejs.org/)
- **Python 3.8+**: [Download here](https://python.org/)
- **MongoDB v4.4+**: [Download here](https://www.mongodb.com/)
- **Git**: [Download here](https://git-scm.com/)
- **Yarn**: `npm install -g yarn`

## 🔧 Detailed Setup

### 1. **MongoDB Setup**

**Windows:**
```bash
# Install MongoDB Community Server
# Start MongoDB service or run:
mongod --dbpath C:\data\db
```

**macOS:**
```bash
# With Homebrew
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb/brew/mongodb-community
```

**Linux:**
```bash
# Install MongoDB
sudo apt-get install mongodb
# Or
sudo systemctl start mongodb
```

### 2. **Backend Setup**

```bash
cd backend/

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Emergent AI Integration
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Start backend server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 3. **Frontend Setup**

```bash
cd frontend/

# Install dependencies
yarn install
# OR: npm install

# Start development server
yarn start
# OR: npm start
```

## 🌐 Access URLs

Once all services are running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Admin Panel**: http://localhost:3000/admin
- **Health Check**: http://localhost:8001/api/health

## 👤 Test Accounts

After setup, create these accounts for testing:

### **Regular User Account:**
```
Name: Test User
Email: test@company.com
Password: TestPass123!
Organization: Test Company
```

### **Admin Account:**
```
Name: Admin User
Email: admin@cybersec.com
Password: AdminPass123!
Organization: Aman Security
```

**⚠️ Important**: After creating the admin account, you need to manually update the role in MongoDB:

```javascript
// Connect to MongoDB
mongo

// Switch to database
use aman_cybersecurity

// Update admin role
db.users.updateOne(
  {email: "admin@cybersec.com"}, 
  {$set: {role: "admin"}}
)

// Verify the update
db.users.find({email: "admin@cybersec.com"}, {email: 1, role: 1})
```

## 🧪 Testing Guide

### **1. Basic Functionality**
- ✅ Visit http://localhost:3000
- ✅ Register a new account
- ✅ Login and access dashboard
- ✅ Navigate through different pages

### **2. AI-Powered Scanning**
Visit http://localhost:8001/docs and test:

**Email Scanning:**
```json
{
  "email_subject": "URGENT: Verify Your Account Now",
  "email_body": "Your account will be suspended. Click here to verify immediately.",
  "sender": "security@fake-bank.com",
  "recipient": "test@company.com"
}
```

**Link Scanning:**
```json
{
  "url": "https://bit.ly/suspicious-link"
}
```

### **3. Admin Panel**
- ✅ Login with admin credentials
- ✅ Access http://localhost:3000/admin
- ✅ View system statistics
- ✅ Check user management features

### **4. Browser Extension**
```bash
# Chrome Extension Testing
1. Open Chrome → Extensions → Enable Developer Mode
2. Click "Load Unpacked"
3. Select the browser-extension folder
4. Test on Gmail or Outlook
```

## 📁 Project Structure

```
aman-cybersecurity-platform/
├── backend/                 # FastAPI backend
│   ├── server.py           # Main server file
│   ├── admin_manager.py    # Admin panel logic
│   ├── ai_scanner.py       # AI-powered scanning
│   ├── realtime_manager.py # WebSocket real-time updates
│   ├── database.py         # MongoDB connection
│   ├── auth.py             # Authentication
│   ├── models.py           # Data models
│   └── .env                # Environment variables
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── Dashboard.js
│   │   │   ├── AdminDashboard.js
│   │   │   ├── LandingPage.js
│   │   │   └── ...
│   │   ├── contexts/       # React contexts
│   │   │   └── AuthContext.js
│   │   └── hooks/          # Custom hooks
│   │       └── useWebSocket.js
│   ├── public/
│   └── .env                # Environment variables
├── browser-extension/      # Chrome extension
│   ├── manifest.json
│   ├── src/background.js
│   ├── content/content.js
│   └── popup/
└── README-LOCAL.md         # This file
```

## 🛠️ Development Commands

```bash
# Backend
cd backend/
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend/
yarn start

# MongoDB
mongod --dbpath /your/data/path

# View logs
# Backend: Check terminal output
# Frontend: Check browser console
```

## 🚨 Troubleshooting

### **Common Issues:**

**Port Already in Use:**
```bash
# Kill processes on port 8001 (backend)
lsof -ti:8001 | xargs kill -9

# Kill processes on port 3000 (frontend)  
lsof -ti:3000 | xargs kill -9
```

**MongoDB Connection Issues:**
```bash
# Check if MongoDB is running
ps aux | grep mongod

# Start MongoDB
mongod --dbpath /path/to/your/data

# Check MongoDB logs
tail -f /var/log/mongodb/mongod.log
```

**Python Dependencies:**
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.8+
```

**Node.js Dependencies:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
yarn install
# OR
npm install
```

**Gemini API Issues:**
- Verify API key is valid
- Check internet connection
- Monitor API usage limits

### **Performance Issues:**
```bash
# Check system resources
top
htop

# Monitor MongoDB performance
mongotop
mongostat
```

## 🔐 Security Notes

- Change JWT_SECRET_KEY in production
- Use HTTPS in production
- Set strong passwords for admin accounts
- Keep Gemini API key secure
- Regularly update dependencies

## 🚀 Production Deployment

For production deployment:

1. **Environment Variables:**
   ```env
   ENVIRONMENT=production
   MONGO_URL=mongodb://production-url
   JWT_SECRET_KEY=super-strong-production-key
   ```

2. **Build Frontend:**
   ```bash
   cd frontend/
   yarn build
   ```

3. **Deploy Backend:**
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
   ```

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Ensure MongoDB is running
4. Check browser console for frontend issues
5. Monitor backend terminal for API errors

## 🎯 Features Available

- ✅ **AI-Powered Scanning**: Gemini AI integration for threat detection
- ✅ **Real-Time Dashboard**: Live updates with WebSocket
- ✅ **Admin Panel**: User management and system monitoring
- ✅ **Browser Extension**: Gmail/Outlook integration
- ✅ **Cost Management**: AI usage tracking and optimization
- ✅ **Threat Intelligence**: Advanced threat analysis
- ✅ **Authentication**: JWT-based secure authentication
- ✅ **Responsive Design**: Works on mobile, tablet, desktop

---

**🎉 Happy Development! The Aman Cybersecurity Platform is ready for local development and testing.**