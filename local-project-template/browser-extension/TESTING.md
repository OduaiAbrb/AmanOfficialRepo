# Browser Extension Testing Instructions

## Prerequisites
- Google Chrome browser
- Gmail or Outlook account for testing
- Backend server running on localhost:8001
- Extension files located in `/app/browser-extension/`

## Step 1: Install the Extension

### 1.1 Enable Developer Mode
1. Open Chrome and go to `chrome://extensions/`
2. Toggle "Developer mode" ON in the top-right corner

### 1.2 Load Extension
1. Click "Load unpacked" button
2. Navigate to `/app/browser-extension/` folder
3. Select the folder and click "Select Folder"
4. Verify "Aman Cybersecurity Protection" appears in extensions list

## Step 2: Test Gmail Integration

### 2.1 Basic Setup
1. Navigate to https://mail.google.com
2. Log into your Gmail account
3. Look for the "Aman Protection Active" notification (appears for 3 seconds)

### 2.2 Email Scanning Test
1. Open any email in your inbox
2. **Expected Result**: Security badge should appear above email content
3. **Badge Types**:
   - 🛡️ **GREEN**: "Aman Security: SAFE" - Email appears legitimate
   - ⚠️ **YELLOW**: "Aman Security: WARNING" - Potentially suspicious 
   - ⚠️ **RED**: "Aman Security: DANGER" - High risk phishing attempt

### 2.3 Link Scanning Test
1. Open an email containing links
2. **Expected Result**: Links should show small colored badges
3. **Badge Types**:
   - Green "SAFE" badge
   - Yellow "WARNING" badge  
   - Red "DANGER" badge

## Step 3: Test Outlook Integration

### 3.1 Outlook.com Testing
1. Navigate to https://outlook.live.com
2. Log into your Outlook account
3. Repeat the same tests as Gmail above

### 3.2 Office 365 Testing (if available)
1. Navigate to https://outlook.office.com
2. Log into your Office 365 account
3. Test email scanning functionality

## Step 4: Test Extension Popup

### 4.1 Open Popup
1. Click the Aman extension icon in Chrome toolbar
2. **Expected Result**: Popup window should open

### 4.2 Verify Popup Contents
Check that popup displays:
- ✅ **Header**: "Aman Security" with status indicator
- ✅ **Statistics**: "Today's Protection" with three metrics
- ✅ **Activity**: "Recent Activity" section
- ✅ **Actions**: Toggle, refresh, and dashboard buttons
- ✅ **Settings**: Real-time protection and notification toggles

### 4.3 Test Popup Functionality
1. **Toggle Protection**: Click "Disable Protection" button
   - Status should change to "Disabled"
   - Button should change to "Enable Protection"
2. **Refresh Scan**: Click "Refresh Scan" button
   - Button should show "Refreshing..." temporarily
3. **Open Dashboard**: Click "Open Dashboard" button
   - Should open new tab to localhost:3000/dashboard
4. **Settings Toggles**: Test both toggle switches
   - Should save settings properly

## Step 5: Advanced Testing

### 5.1 Mock Threat Detection
Test emails containing these keywords to trigger warnings:
- "urgent"
- "verify account"
- "click here"
- "limited time"
- "suspended"

### 5.2 Storage Testing
1. Open Chrome DevTools (F12)
2. Go to Application tab > Storage > Chrome Extension
3. Check that scan results are being stored

### 5.3 Console Logging
1. Open Chrome DevTools (F12)
2. Go to Console tab
3. Look for Aman extension log messages
4. Should see initialization and scanning messages

## Expected Test Results

### ✅ Successful Installation
- Extension appears in Chrome extensions list
- No error messages during installation
- Extension icon visible in toolbar

### ✅ Gmail/Outlook Integration  
- Security badges appear on emails
- Link badges appear on suspicious links
- No console errors when scanning

### ✅ Popup Functionality
- All statistics display correctly
- Buttons and toggles work properly
- Recent activity shows scan results

### ✅ Real-time Scanning
- New emails get scanned automatically
- Scanning indicator appears briefly
- Results stored and displayed in popup

## Troubleshooting Common Issues

### Extension Not Loading
- **Issue**: Extension doesn't appear after loading
- **Solution**: Check for manifest.json errors, reload extension

### No Security Badges
- **Issue**: Emails don't show security indicators
- **Solution**: Refresh page, check if extension is enabled

### Popup Not Working
- **Issue**: Clicking extension icon does nothing
- **Solution**: Check for popup.html path issues, reload extension

### API Connection Errors
- **Issue**: Extension can't connect to backend
- **Solution**: Verify backend server is running on localhost:8001

## Manual Testing Checklist

### Basic Functionality
- [ ] Extension installs without errors
- [ ] Extension icon appears in Chrome toolbar
- [ ] Popup opens when clicking icon
- [ ] Status shows "Active" by default

### Gmail Testing
- [ ] Gmail loads with extension active
- [ ] Opening emails triggers scanning
- [ ] Security badges appear on emails
- [ ] Link badges appear on links
- [ ] Different threat levels show different colors

### Outlook Testing  
- [ ] Outlook loads with extension active
- [ ] Email scanning works on Outlook
- [ ] Security indicators display properly

### Popup Interface
- [ ] Statistics display real numbers
- [ ] Recent activity shows scan results
- [ ] Toggle buttons work correctly
- [ ] Settings save properly
- [ ] Dashboard button opens correct URL

### Performance
- [ ] Extension doesn't slow down email loading
- [ ] Scanning completes quickly
- [ ] No memory leaks or high CPU usage
- [ ] Smooth user experience

## Test Data Examples

### Safe Email Indicators
- Subject: "Weekly Team Meeting Reminder"
- Content: Normal business communication
- **Expected**: Green "SAFE" badge

### Warning Email Indicators  
- Subject: "Verify Your Account Information"
- Content: Contains "verify account" keyword
- **Expected**: Yellow "WARNING" badge

### Danger Email Indicators
- Subject: "Urgent: Claim Your Prize Now!"
- Content: Contains multiple suspicious keywords
- **Expected**: Red "DANGER" badge

## Success Criteria

The extension test is successful if:
1. ✅ Extension installs and loads without errors
2. ✅ Email scanning works on Gmail and/or Outlook
3. ✅ Security badges appear with appropriate colors
4. ✅ Popup interface displays statistics and controls
5. ✅ All buttons and toggles function correctly
6. ✅ No console errors or performance issues

This completes the browser extension testing protocol.