#!/bin/bash

# Package Management Cleanup Script for Aman Cybersecurity Platform
# This script ensures clean package management with Yarn only

echo "🧹 Aman Platform - Package Cleanup Script"
echo "=========================================="

# Navigate to frontend directory
cd /app/frontend

echo "📋 Current package files:"
ls -la | grep -E "(package|lock|node_modules)" || echo "No package files found"

echo ""
echo "🗑️  Removing conflicting files..."

# Remove package-lock.json if it exists
if [ -f "package-lock.json" ]; then
    rm package-lock.json
    echo "✅ Removed package-lock.json"
else
    echo "ℹ️  No package-lock.json found"
fi

# Remove node_modules if it exists
if [ -d "node_modules" ]; then
    rm -rf node_modules
    echo "✅ Removed node_modules directory"
else
    echo "ℹ️  No node_modules directory found"
fi

# Remove yarn.lock to start fresh
if [ -f "yarn.lock" ]; then
    rm yarn.lock
    echo "✅ Removed existing yarn.lock"
else
    echo "ℹ️  No yarn.lock found"
fi

echo ""
echo "📦 Installing dependencies with Yarn..."
yarn install

echo ""
echo "🔍 Final package files:"
ls -la | grep -E "(package|lock|node_modules)"

echo ""
echo "✅ Package management cleanup complete!"
echo "ℹ️  Only yarn.lock should exist for package management"
echo "ℹ️  Never commit package-lock.json to avoid conflicts"

echo ""
echo "🚀 Restarting frontend service..."
sudo supervisorctl restart frontend

echo "✅ All done! Frontend should be running cleanly now."