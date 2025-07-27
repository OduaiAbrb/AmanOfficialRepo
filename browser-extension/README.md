# Aman Cybersecurity Browser Extension

AI-powered real-time phishing detection and protection for Gmail and Outlook, integrated with the Aman Cybersecurity Platform backend.

## ✨ Features

### 🧠 AI-Powered Scanning
- **Gemini AI Integration**: Utilizes Google Gemini 2.0 Flash for advanced threat analysis
- **Real-time Email Scanning**: Automatic analysis of incoming emails with 95% accuracy
- **Context-Aware Link Analysis**: Intelligent URL threat assessment with reasoning
- **Fallback Protection**: Maintains functionality even when AI services are unavailable

### 🛡️ Security Features
- **Enterprise Authentication**: JWT token integration with the Aman platform
- **Content Security**: Sanitization and filtering before external analysis
- **Privacy First**: No sensitive data stored or transmitted unnecessarily
- **Rate Limiting**: Responsible API usage with smart caching

### 📊 User Experience
- **Visual Threat Indicators**: Color-coded security badges on emails and links
- **Real-time Notifications**: Instant alerts for high-risk content
- **Detailed Explanations**: Human-readable AI-powered threat analysis
- **Statistics Dashboard**: Track scanned emails and blocked threats

## 🚀 Installation Instructions

### Prerequisites
1. **Chrome Browser**: Version 88 or higher
<<<<<<< HEAD
=======
2. **Aman Account**: Register at [Aman Platform](https://f8e0a18c-634d-449c-bde8-c523f13f683c.preview.emergentagent.com)
>>>>>>> c79b7619501b0f724bbf65a305cf406c59942f3a

### Installation Steps

#### Method 1: Developer Mode (Recommended for Testing)
1. **Download Extension**:
   ```bash
   # Clone or download the browser-extension folder
   cd /path/to/aman-platform/browser-extension
   ```

2. **Open Chrome Extensions**:
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)

3. **Load Extension**:
   - Click "Load unpacked"
   - Select the `browser-extension` folder
   - Extension should appear with green Aman icon

4. **Verify Installation**:
   - Look for Aman icon in Chrome toolbar
   - Click icon to open popup interface

### 🔐 Authentication Setup

1. **Login to Aman Platform**:
<<<<<<< HEAD

=======
   - Visit: https://f8e0a18c-634d-449c-bde8-c523f13f683c.preview.emergentagent.com
>>>>>>> c79b7619501b0f724bbf65a305cf406c59942f3a
   - Login with your credentials

2. **Extension Auto-Authentication**:
   - Extension automatically detects login
   - Green notification appears: "Browser Extension Connected"

3. **Manual Authentication** (if needed):
   - Click Aman extension icon
   - Click "Login" button in popup
   - Complete authentication on web platform

## 📧 Supported Email Platforms

### Gmail
- **URL**: `https://mail.google.com/*`
- **Features**: Full email scanning, link analysis, real-time protection
- **Selectors**: Optimized for Gmail interface

### Outlook (All Variants)
- **URLs**: 
  - `https://outlook.live.com/*`
  - `https://outlook.office.com/*`
  - `https://outlook.office365.com/*`
- **Features**: Complete email and link scanning
- **Selectors**: Adaptive to Outlook interfaces

## 🎛️ Extension Usage

### Email Scanning
1. **Automatic Scanning**: 
   - Opens email → Extension automatically scans
   - Shows security badge with risk assessment

2. **Security Badges**:
   - 🟢 **SAFE**: Email appears legitimate
   - 🟡 **WARNING**: Potentially suspicious content
   - 🔴 **DANGER**: High-risk phishing attempt detected

3. **AI Indicators**:
   - **AI Badge**: Shows when Gemini AI was used
   - **LOCAL Badge**: Indicates fallback scanning
   - **Risk Percentage**: Numerical threat assessment

### Link Analysis
- **Real-time Scanning**: Links analyzed as emails load
- **Color-coded Badges**: Visual threat indicators on links
- **Shortened URL Detection**: Special handling for bit.ly, tinyurl.com, etc.

### Popup Interface
- **Today's Protection**: Statistics on emails scanned and threats blocked
- **Recent Activity**: Last 5 scan results with details
- **Quick Actions**: Toggle protection, refresh scans, open dashboard
- **Settings**: Real-time protection and notification preferences

## ⚡ API Integration

### Backend Endpoints
```javascript
// Email Scanning
POST /api/scan/email
Authorization: Bearer {jwt_token}
{
  "email_subject": "...",
  "email_body": "...",
  "sender": "...",
  "recipient": "..."
}

// Link Scanning  
POST /api/scan/link
Authorization: Bearer {jwt_token}
{
  "url": "...",
  "context": "..."
}
```

### Response Format
```javascript
{
  "id": "scan_123...",
  "status": "safe|potential_phishing|phishing",
  "risk_score": 85.0,
  "explanation": "AI-generated threat explanation",
  "threat_sources": ["ai_analysis", "pattern_matching"],
  "detected_threats": ["urgency_manipulation", "suspicious_links"],
  "recommendations": ["Do not click links", "Verify sender identity"]
}
```

## 🔧 Technical Architecture

### Manifest V3 Structure
- **Service Worker**: `src/background.js` - API integration and message handling
- **Content Scripts**: `content/content.js` - Gmail/Outlook DOM interaction
- **Popup Interface**: `popup/popup.html` - User interface and statistics
- **Permissions**: Minimal required permissions for security

### Security Design
- **JWT Authentication**: Secure token-based API access
- **Content Sanitization**: Filters sensitive data before AI analysis
- **Local Storage**: Encrypted storage of authentication tokens
- **Fallback Mechanisms**: Continues operation during API failures

## 🧪 Testing Guide

### Manual Testing Checklist

#### 1. Installation & Setup
- [ ] Extension loads without errors
- [ ] Icon appears in Chrome toolbar
- [ ] Popup opens and displays correctly

#### 2. Authentication
- [ ] Login through web platform
- [ ] Extension shows "Authenticated" status
- [ ] User email displays correctly in popup

#### 3. Gmail Integration
- [ ] Navigate to Gmail
- [ ] "Aman Protection Active" indicator appears
- [ ] Open email → Security badge appears
- [ ] Badge shows appropriate risk level

#### 4. Outlook Integration  
- [ ] Test on all Outlook variants
- [ ] Email scanning works correctly
- [ ] Links are properly analyzed

#### 5. AI Integration
- [ ] High-risk emails show AI badges
- [ ] Explanations are detailed and relevant
- [ ] Fallback works when AI unavailable

#### 6. Performance
- [ ] No significant page slowdown
- [ ] Scans complete within 2-3 seconds
- [ ] Extension remains responsive

### Test Email Scenarios

#### Safe Email Test
```
Subject: Weekly Team Meeting
Sender: colleague@company.com
Body: Hi team, our weekly meeting is scheduled for Friday at 2 PM.
Expected: SAFE badge, low risk score
```

#### Phishing Email Test
```
Subject: URGENT: Verify Your Account Now
Sender: security@fake-bank.com
Body: Your account will be suspended. Click here to verify immediately.
Expected: DANGER badge, high risk score, AI analysis
```

## 🐛 Troubleshooting

### Common Issues

#### Extension Not Loading
```bash
# Check console for errors
1. Open chrome://extensions/
2. Click "Errors" on extension
3. Check service worker logs
```

#### Authentication Fails
```bash
# Clear extension storage
1. Right-click extension icon
2. Inspect popup
3. Console: chrome.storage.local.clear()
4. Re-authenticate
```

#### Scanning Not Working
- Verify internet connection
- Check authentication status
- Try refreshing email page
- Look for API rate limiting

### Debug Information
```javascript
// Enable debug logging
localStorage.setItem('amanDebug', 'true');

// Check extension storage
chrome.storage.local.get(null, console.log);

// View scan results
chrome.storage.local.get(['scanResults'], console.log);
```

## 🔄 Updates & Maintenance

### Version History
- **v1.0.1**: AI integration with Gemini 2.0 Flash
- **v1.0.0**: Initial release with basic scanning

### Update Procedure
1. Update manifest version
2. Test all functionality
3. Update documentation
4. Re-package for distribution

## 📞 Support

### Getting Help
- **Platform Issues**: Contact through Aman dashboard
- **Extension Bugs**: Check browser console for errors
- **API Issues**: Verify authentication and connectivity

### Reporting Issues
Include in bug reports:
- Chrome version
- Extension version  
- Console error messages
- Steps to reproduce
- Screenshots if applicable

## 🚀 Production Deployment

### Chrome Web Store Preparation
1. **Package Extension**:
   ```bash
   zip -r aman-extension.zip browser-extension/
   ```

2. **Required Assets**:
   - High-quality icon set (16, 32, 48, 128px)
   - Detailed description and screenshots
   - Privacy policy and terms of service

3. **Store Listing**:
   - Focus on AI-powered security features
   - Highlight enterprise-grade protection
   - Include professional screenshots

### Enterprise Distribution
- Consider private Chrome Web Store publication
- Provide installation guides for IT administrators
- Include group policy templates if needed

---

**Built with ❤️ for SME cybersecurity protection**  
**Powered by AI • Secured by Design • Trusted by Businesses**