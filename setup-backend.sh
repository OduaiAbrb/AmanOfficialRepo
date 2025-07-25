#!/bin/bash

echo "🐍 Setting up Aman Cybersecurity Backend..."

# Create backend directory
mkdir -p aman-cybersecurity-platform/backend
cd aman-cybersecurity-platform/backend

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
motor==3.3.2
pymongo==4.6.0
python-dotenv==1.0.0
bcrypt==4.1.2
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
slowapi==0.1.9
validators==0.22.0
passlib[bcrypt]==1.7.4
emergentintegrations
websockets==12.0
EOF

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Create .env file
cat > .env << 'EOF'
MONGO_URL=mongodb://localhost:27017
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ENVIRONMENT=development
GEMINI_API_KEY=AIzaSyBUPx4B7pH-f-ECKgGrl-4zCihpRB2hglY
EOF

echo "✅ Backend setup complete!"
echo "🚀 To start backend: uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
echo "📖 Don't forget to copy all Python files from the project!"