# Browser Extension Installation & Testing Guide

## Quick Installation Steps

### 1. Open Chrome Extensions Page
- Open Google Chrome
- Navigate to `chrome://extensions/`
- Toggle "Developer mode" ON (top-right corner)

### 2. Load the Extension
- Click "Load unpacked" button
- Navigate to and select the `/app/browser-extension` folder
- The extension should appear in your extensions list

### 3. Verify Installation
- Look for "Aman Cybersecurity Protection" in your extensions
- The extension icon should appear in the Chrome toolbar
- Click the icon to open the popup interface

## Testing the Extension

### 1. Gmail Testing
- Navigate to `https://mail.google.com`
- Log into your Gmail account
- Open any email
- Look for the Aman security badge above the email content
- Check for link badges on any links within emails

### 2. Outlook Testing
- Navigate to `https://outlook.live.com` or `https://outlook.office.com`
- Log into your Outlook account
- Open any email
- Look for security indicators and badges

### 3. Extension Popup Testing
- Click the Aman extension icon in Chrome toolbar
- Verify the popup shows:
  - Protection status (Active/Disabled)
  - Today's statistics
  - Recent activity
  - Quick action buttons
  - Settings toggles

## Expected Behavior

### Email Scanning
- New emails automatically get scanned when opened
- Security badges appear above email content:
  - 🛡️ **GREEN**: Safe email
  - ⚠️ **YELLOW**: Warning/Suspicious
  - ⚠️ **RED**: Danger/Phishing

### Link Protection
- Links within emails get scanned automatically
- Dangerous links show warning badges
- Safe links may show small "SAFE" indicators

### Popup Statistics
- Shows count of emails scanned today
- Displays threats blocked count
- Shows overall risk level
- Lists recent scanning activity

## Troubleshooting

### Extension Not Loading
- Check that developer mode is enabled
- Ensure the manifest.json file exists in the extension folder
- Look for error messages in the Chrome extensions page

### No Security Badges
- Verify the extension is enabled
- Check that you're on a supported email platform (Gmail/Outlook)
- Try refreshing the email page
- Click "Refresh Scan" in the extension popup

### API Connection Issues
- Ensure the backend server is running on localhost:8001
- Check browser console (F12) for error messages
- Verify the extension popup shows "Active" status

## Current Limitations

### Mock Data
- The extension currently uses mock scanning logic
- Real API integration will be implemented in future phases
- Scanning results are based on simple keyword detection

### Icon Placeholders
- Extension icons are currently placeholders
- Proper icons will be added in production version

### Testing Environment
- Extension is configured for development/testing
- Works with localhost backend (localhost:8001)
- Production version will use different API endpoints

## Next Steps

1. **Install and test the extension** following the steps above
2. **Verify basic functionality** on Gmail or Outlook
3. **Check the popup interface** for statistics and controls
4. **Report any issues** or unexpected behavior

The browser extension provides the core user-facing functionality for the Aman cybersecurity platform, offering real-time protection directly within the user's email interface.