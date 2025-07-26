# 🏠 Aman Cybersecurity Platform - Local Development Setup

## 📋 Prerequisites

```bash
# Install these on your local machine:
1. Node.js v16+ (https://nodejs.org/)
2. Python 3.8+ (https://python.org/)  
3. MongoDB v4.4+ (https://mongodb.com/)
4. Git (https://git-scm.com/)
5. Yarn: npm install -g yarn
```

## 📁 Project Structure

Create this folder structure on your machine:

```
aman-cybersecurity-platform/
├── backend/
│   ├── requirements.txt
│   ├── server.py
│   ├── database.py
│   ├── auth.py
│   ├── security.py
│   ├── models.py
│   ├── ai_scanner.py
│   ├── ai_cost_manager.py
│   ├── admin_manager.py
│   ├── email_scanner.py
│   ├── feedback_system.py
│   ├── threat_intelligence.py
│   ├── realtime_manager.py
│   └── .env
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   └── hooks/
│   ├── public/
│   └── .env
├── browser-extension/
└── README.md
```

## 🔧 Environment Setup

### Backend Environment (.env file in backend folder):
```env
MONGO_URL=mongodb://localhost:27017
JWT_SECRET_KEY=your-super-secret-jwt-key-here-change-this
ENVIRONMENT=development
GEMINI_API_KEY=AIzaSyBUPx4B7pH-f-ECKgGrl-4zCihpRB2hglY
```

### Frontend Environment (.env file in frontend folder):
```env
REACT_APP_BACKEND_URL=http://localhost:8001/api
REACT_APP_LOCAL_BASE_URL=http://localhost:8001/api
DANGEROUSLY_DISABLE_HOST_CHECK=true
```

## 🗄️ Database Setup

```bash
# 1. Start MongoDB
mongod --dbpath /your/data/path

# 2. Create database (automatic on first connection)
# Database: aman_cybersecurity
# Collections will be created automatically
```

## 🐍 Backend Setup

```bash
# Navigate to backend folder
cd backend/

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install specific packages if missing
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Start backend server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

## ⚛️ Frontend Setup

```bash
# Navigate to frontend folder
cd frontend/

# Install dependencies  
yarn install

# Start development server
yarn start
```

## 🌐 Access URLs

Once everything is running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Admin Panel**: http://localhost:3000/admin

## 👤 Test Accounts

Create these accounts after setup:

**Regular User:**
- Name: Test User
- Email: test@company.com
- Password: TestPass123!

**Admin User:**
- Name: Admin User  
- Email: admin@cybersec.com
- Password: AdminPass123!

Then manually update the admin role in MongoDB:
```javascript
db.users.updateOne({email: "admin@cybersec.com"}, {$set: {role: "admin"}})
```

## 🧪 Testing

1. **Register/Login**: Test user authentication
2. **Dashboard**: Verify real-time statistics
3. **AI Scanning**: Test email/link scanning via API docs
4. **Admin Panel**: Access admin features with admin account
5. **Browser Extension**: Load unpacked extension in Chrome

## 🔧 Development Commands

```bash
# Backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend  
yarn start

# MongoDB
mongod --dbpath /your/data/path

# View logs
# Backend logs appear in terminal
# Frontend logs appear in browser console
```

## 🚨 Troubleshooting

**Common Issues:**

1. **Port conflicts**: Change ports in .env files
2. **MongoDB connection**: Ensure MongoDB is running
3. **Dependencies**: Run pip install / yarn install again
4. **API key issues**: Verify Gemini API key is valid
5. **CORS errors**: Check REACT_APP_BACKEND_URL matches backend

## 📦 Production Deployment

For production deployment:
1. Set ENVIRONMENT=production in backend .env
2. Update frontend .env with production backend URL
3. Use proper secrets for JWT_SECRET_KEY
4. Set up SSL/HTTPS
5. Configure proper CORS settings

## 🎯 Features Available

- ✅ AI-powered email/link scanning
- ✅ Real-time dashboard with WebSocket
- ✅ Admin panel with user management
- ✅ Browser extension for Gmail/Outlook
- ✅ Cost management and analytics
- ✅ Threat intelligence and reporting