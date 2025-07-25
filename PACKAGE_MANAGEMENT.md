# Package Management Guide - Avoiding Lock File Conflicts

## 🚨 Problem Solved!

The package-lock.json conflicts have been resolved. Here's what was done and how to prevent future issues:

## ✅ What Was Fixed

1. **Removed package-lock.json**: Deleted the conflicting npm lock file
2. **Cleaned node_modules**: Removed and reinstalled all dependencies
3. **Fresh Yarn Installation**: Created a clean yarn.lock file
4. **Added .gitignore**: Prevents package-lock.json from being committed
5. **Created Cleanup Script**: Easy way to fix future conflicts

## 🛠️ Quick Fix Commands

If you encounter package conflicts again, run:

```bash
# Navigate to frontend directory
cd /app/frontend

# Remove conflicting files
rm -f package-lock.json
rm -rf node_modules
rm -f yarn.lock

# Clean install with Yarn
yarn install

# Restart frontend
sudo supervisorctl restart frontend
```

Or use the automated script:
```bash
/app/scripts/cleanup-packages.sh
```

## 📋 Best Practices

### ✅ DO:
- **Use Yarn exclusively**: `yarn add package-name`
- **Commit yarn.lock**: Always include yarn.lock in git commits
- **Use yarn install**: For installing dependencies from package.json

### ❌ DON'T:
- **Don't use npm**: Avoid `npm install` or `npm add`
- **Don't commit package-lock.json**: It conflicts with yarn.lock
- **Don't mix package managers**: Stick to yarn only

## 🔧 Commands Reference

### Installing Dependencies:
```bash
# Install from package.json
yarn install

# Add new dependency
yarn add package-name

# Add dev dependency
yarn add --dev package-name

# Remove dependency
yarn remove package-name
```

### Troubleshooting:
```bash
# Check yarn version
yarn --version

# Clear yarn cache
yarn cache clean

# Check for issues
yarn check

# Upgrade dependencies
yarn upgrade
```

## 📁 File Status After Fix

Current frontend directory should have:
- ✅ `package.json` - Project dependencies
- ✅ `yarn.lock` - Yarn lock file (commit this)
- ✅ `node_modules/` - Installed packages (don't commit)
- ❌ `package-lock.json` - Should NOT exist

## 🚀 Verification

After running the cleanup, verify everything works:

1. **Check frontend is running**:
   ```bash
   sudo supervisorctl status frontend
   ```

2. **Test the application**:
   - Visit http://localhost:3000 (landing page)
   - Visit http://localhost:3000/dashboard (dashboard)

3. **Check for errors**:
   ```bash
   tail -f /var/log/supervisor/frontend.*.log
   ```

## 🎯 Why This Happened

Package conflicts occur when both `package-lock.json` (npm) and `yarn.lock` (yarn) exist in the same project. They have different dependency resolution algorithms, causing:
- Merge conflicts in git
- Inconsistent dependency versions
- Build issues

By using only Yarn and yarn.lock, we ensure consistent package management.

## 📞 Support

If you encounter package issues again:
1. Run the cleanup script: `/app/scripts/cleanup-packages.sh`
2. Check the .gitignore includes package-lock.json
3. Always use yarn commands instead of npm
4. Commit yarn.lock but never package-lock.json

The Aman Cybersecurity Platform is now running with clean package management! 🎉