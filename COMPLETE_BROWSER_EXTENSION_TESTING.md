# Complete Browser Extension Testing Guide
## Aman Cybersecurity Platform - Browser Extension Testing

### 🎯 **PREREQUISITES**
✅ Backend server running at 100% success rate (confirmed)
✅ Frontend authentication working (confirmed)
✅ Chrome browser installed
✅ Gmail/Outlook account for testing

---

## 📋 **STEP 1: INSTALL THE BROWSER EXTENSION**

### 1.1 Enable Chrome Developer Mode
1. Open Google Chrome
2. Navigate to `chrome://extensions/`
3. Toggle **"Developer mode"** ON (top-right corner)
4. You should see "Load unpacked", "Pack extension", and "Update" buttons appear

### 1.2 Load the Extension
1. Click **"Load unpacked"** button
2. Navigate to your project folder: `/app/browser-extension/`
3. Select the entire `browser-extension` folder
4. Click **"Select Folder"**
5. ✅ **Verify**: "Aman Cybersecurity Protection" appears in your extensions list
6. ✅ **Verify**: Extension icon appears in Chrome toolbar (green shield)

### 1.3 Pin the Extension (Recommended)
1. Click the puzzle piece icon in Chrome toolbar
2. Click the pin icon next to "Aman Cybersecurity Protection"
3. The extension icon should now be visible in your toolbar

---

## 🔐 **STEP 2: AUTHENTICATE THE EXTENSION**

### 2.1 Initial Authentication
1. Click the **Aman extension icon** in your Chrome toolbar
2. You should see the extension popup with login prompt
3. Click **"Login to Aman Platform"** 
4. ✅ **Expected**: Opens new tab to the authentication page
5. Complete the login process on the web platform
6. ✅ **Expected**: Success notification appears
7. Return to extension popup - it should now show "Authenticated ✅"

### 2.2 Verify Authentication Status
1. Click the extension icon
2. ✅ **Expected**: Shows your user info and statistics
3. ✅ **Expected**: Shows "Connected to Aman Platform" status
4. ✅ **Expected**: Displays scan counts and recent activity

---

## 📧 **STEP 3: TEST GMAIL INTEGRATION**

### 3.1 Basic Gmail Setup
1. Navigate to **https://mail.google.com**
2. Log into your Gmail account
3. ✅ **Expected**: Console message "Aman Extension: Gmail detected"
4. ✅ **Expected**: Brief notification "Aman Protection Active"

### 3.2 Email Scanning Test - Safe Email
1. Open a **legitimate email** from a trusted sender (e.g., Google, bank)
2. ✅ **Expected**: Security badge appears above email content
3. ✅ **Expected**: 🛡️ **GREEN badge**: "Aman Security: SAFE - Email appears legitimate"
4. ✅ **Expected**: Extension popup shows updated scan count

### 3.3 Email Scanning Test - Suspicious Content
1. Create or find an email with suspicious characteristics:
   - Urgent language ("Act now!", "Limited time!")
   - Suspicious sender domains
   - Generic greetings ("Dear Customer")
2. ✅ **Expected**: ⚠️ **YELLOW badge**: "Aman Security: WARNING - Potentially suspicious"
3. ✅ **Expected**: Detailed explanation of why it's flagged

### 3.4 Link Scanning Test
1. Find an email with external links
2. ✅ **Expected**: Each link should have a small colored badge:
   - 🟢 **Green "SAFE"** - Legitimate domains
   - 🟡 **Yellow "WARNING"** - Suspicious domains
   - 🔴 **Red "DANGER"** - Known malicious domains
3. ✅ **Expected**: Hover over badges shows detailed information

---

## 📨 **STEP 4: TEST OUTLOOK INTEGRATION**

### 4.1 Outlook.com Testing
1. Navigate to **https://outlook.live.com**
2. Log into your Outlook account
3. ✅ **Expected**: Console message "Aman Extension: Outlook detected"
4. Repeat all email scanning tests from Gmail section

### 4.2 Office 365 Testing (if available)
1. Navigate to **https://outlook.office.com** or **https://outlook.office365.com**
2. Log into your Office 365 account
3. Test email scanning functionality
4. ✅ **Expected**: Same functionality as consumer Outlook

---

## 🛠️ **STEP 5: TEST EXTENSION POPUP FUNCTIONALITY**

### 5.1 Statistics Display
1. Click the extension icon
2. ✅ **Verify**: Shows accurate scan counts
3. ✅ **Verify**: Shows threats blocked count
4. ✅ **Verify**: Shows recent activity feed

### 5.2 Settings Management
1. In extension popup, look for settings/options
2. ✅ **Test**: Toggle real-time scanning on/off
3. ✅ **Test**: Toggle notifications on/off
4. ✅ **Verify**: Settings persist after browser restart

### 5.3 Manual Scan Feature
1. In extension popup, look for "Scan Current Page" or similar
2. ✅ **Test**: Click manual scan button
3. ✅ **Expected**: Shows scanning progress
4. ✅ **Expected**: Displays scan results

---

## 🧪 **STEP 6: ADVANCED TESTING SCENARIOS**

### 6.1 Test Error Handling
1. Turn off backend server temporarily
2. Try scanning emails
3. ✅ **Expected**: Graceful fallback to local scanning
4. ✅ **Expected**: "Limited protection mode" notification
5. Restart backend and verify reconnection

### 6.2 Test Multiple Browser Tabs
1. Open Gmail in multiple tabs
2. Test scanning in each tab
3. ✅ **Expected**: Each tab works independently
4. ✅ **Expected**: Extension popup shows combined statistics

### 6.3 Test Browser Restart
1. Close and reopen Chrome
2. ✅ **Verify**: Extension still authenticated
3. ✅ **Verify**: Settings preserved
4. ✅ **Verify**: Scan history maintained

---

## 🔍 **STEP 7: DEBUGGING AND TROUBLESHOOTING**

### 7.1 Check Extension Console
1. Go to `chrome://extensions/`
2. Find "Amen Cybersecurity Protection"
3. Click **"Inspect views: background page"**
4. Check console for any errors
5. ✅ **Expected**: No critical errors

### 7.2 Check Content Script Console
1. On Gmail/Outlook page, press **F12**
2. Go to **Console** tab
3. Look for Aman extension messages
4. ✅ **Expected**: "Extension initialized" messages
5. ✅ **Expected**: No red error messages

### 7.3 Common Issues and Solutions

**Issue**: Extension icon not appearing
- **Solution**: Refresh `chrome://extensions/` page and reload extension

**Issue**: "Not authenticated" message
- **Solution**: Click "Login to Aman Platform" and complete web authentication

**Issue**: No badges appearing on emails
- **Solution**: Check console for errors, verify backend connection

**Issue**: Badges showing but no scanning results
- **Solution**: Verify extension is authenticated and backend is running

---

## 📊 **STEP 8: PERFORMANCE AND SECURITY TESTING**

### 8.1 Performance Test
1. Open Gmail with 50+ emails
2. ✅ **Verify**: Page loads normally (no significant slowdown)
3. ✅ **Verify**: Scanning doesn't block UI interactions
4. ✅ **Verify**: Extension popup opens quickly

### 8.2 Security Test
1. Check network requests in DevTools
2. ✅ **Verify**: All API calls use HTTPS
3. ✅ **Verify**: Authentication tokens handled securely
4. ✅ **Verify**: No sensitive data logged to console

### 8.3 Privacy Test
1. ✅ **Verify**: Email content not stored locally
2. ✅ **Verify**: Only metadata sent to backend
3. ✅ **Verify**: User can disable scanning anytime

---

## ✅ **SUCCESS CRITERIA CHECKLIST**

### Core Functionality ✅
- [ ] Extension installs without errors
- [ ] Authentication flow works correctly
- [ ] Gmail integration shows security badges
- [ ] Outlook integration shows security badges
- [ ] Link scanning works on both platforms
- [ ] Extension popup displays statistics
- [ ] Settings can be modified and persist

### Advanced Features ✅
- [ ] Error handling works gracefully
- [ ] Offline mode provides basic protection
- [ ] Multiple tabs work independently
- [ ] Browser restart preserves authentication
- [ ] Performance remains good with many emails

### Security & Privacy ✅
- [ ] All communications are encrypted
- [ ] No sensitive data exposed in console
- [ ] User authentication is secure
- [ ] Privacy settings are respected

---

## 🎉 **EXPECTED RESULTS SUMMARY**

**After completing all tests, you should have:**
1. ✅ Working browser extension that protects Gmail and Outlook
2. ✅ Real-time email and link scanning with AI-powered threat detection
3. ✅ Professional security badges and notifications
4. ✅ Seamless integration with the web platform authentication
5. ✅ Statistics and activity tracking in extension popup
6. ✅ Robust error handling and offline capabilities

**If any test fails, check:**
- Backend server is running (confirmed working at 100%)
- Extension is properly authenticated
- Console messages for specific error details
- Network connectivity to the backend API

---

## 📞 **TESTING SUPPORT**

The browser extension integrates with the fully functional backend API (100% success rate) and uses the same AI-powered scanning technology as the web platform. All backend functionality has been verified and is production-ready.

For any issues during testing, check the browser console (F12) and the extension's background page console for detailed error messages.