#!/bin/bash

echo "⚛️ Setting up Aman Cybersecurity Frontend..."

# Navigate to project root or create it
mkdir -p aman-cybersecurity-platform/frontend
cd aman-cybersecurity-platform/frontend

# Create package.json
cat > package.json << 'EOF'
{
  "name": "aman-cybersecurity-frontend",
  "version": "2.0.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.4",
    "@testing-library/react": "^13.3.0",
    "@testing-library/user-event": "^13.5.0",
    "axios": "^1.4.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.1",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.0"
  }
}
EOF

# Create .env file
cat > .env << 'EOF'
REACT_APP_BACKEND_URL=http://localhost:8001/api
REACT_APP_LOCAL_BASE_URL=http://localhost:8001/api
DANGEROUSLY_DISABLE_HOST_CHECK=true
EOF

# Create basic public/index.html
mkdir -p public
cat > public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="AI-powered cybersecurity platform for SMEs" />
    <title>Aman Cybersecurity Platform</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
    <!-- Browser Extension Authentication Bridge -->
    <script src="%PUBLIC_URL%/extension-auth.js"></script>
  </body>
</html>
EOF

# Create src directory structure
mkdir -p src/components
mkdir -p src/contexts  
mkdir -p src/hooks

# Install dependencies
echo "📦 Installing Node.js dependencies..."
if command -v yarn &> /dev/null; then
    yarn install
else
    npm install
fi

# Install Tailwind CSS
echo "🎨 Setting up Tailwind CSS..."
if command -v yarn &> /dev/null; then
    yarn add -D tailwindcss postcss autoprefixer
    yarn tailwindcss init -p
else
    npm install -D tailwindcss postcss autoprefixer
    npx tailwindcss init -p
fi

# Create tailwind config
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        primary: '#24fa39',
        secondary: '#1a1a1a',
      }
    },
  },
  plugins: [],
}
EOF

# Create basic CSS files
cat > src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
EOF

cat > src/App.css << 'EOF'
.App {
  text-align: center;
}

.App-logo {
  height: 40vmin;
  pointer-events: none;
}

@media (prefers-reduced-motion: no-preference) {
  .App-logo {
    animation: App-logo-spin infinite 20s linear;
  }
}

.App-header {
  background-color: #282c34;
  padding: 20px;
  color: white;
}

.App-link {
  color: #61dafb;
}

@keyframes App-logo-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
EOF

echo "✅ Frontend setup complete!"
echo "🚀 To start frontend: yarn start (or npm start)"
echo "📖 Don't forget to copy all React component files from the project!"