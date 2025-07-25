# Aman Cybersecurity Browser Extension

A Chrome extension that provides real-time phishing detection and protection for Gmail and Outlook.

## Features

- **Real-time Email Scanning**: Automatically scans incoming emails for phishing attempts
- **Visual Safety Indicators**: Clear badges showing email safety status (Safe/Warning/Danger)
- **Link Protection**: Scans and labels links within emails
- **Gmail & Outlook Support**: Works with Gmail, Outlook.com, and Office 365
- **Lightweight Design**: Minimal performance impact on email platforms
- **Privacy-Focused**: Processes emails locally with secure API communication

## Installation

### Development Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the `/app/browser-extension` directory
4. The extension should now appear in your extensions list

### Production Installation (Future)

Will be available on the Chrome Web Store once published.

## Usage

### Initial Setup

1. After installation, the extension automatically activates
2. Navigate to Gmail or Outlook
3. You'll see a brief "Aman Protection Active" notification
4. The extension will start scanning emails automatically

### Email Scanning

- **Automatic Scanning**: New emails are scanned as they load
- **Visual Indicators**: Each email gets a security badge:
  - 🛡️ **GREEN (Safe)**: Email appears legitimate
  - ⚠️ **YELLOW (Warning)**: Potentially suspicious content
  - ⚠️ **RED (Danger)**: High risk phishing attempt

### Link Protection

- Links within emails are automatically scanned
- Dangerous links get labeled with warning badges
- Hover over badges for additional information

### Extension Popup

Click the extension icon to access:

- **Protection Status**: Current scanning status
- **Today's Stats**: Emails scanned, threats blocked, risk level
- **Recent Activity**: Last 5 email scans with details
- **Quick Actions**: Toggle protection, refresh scan, open dashboard
- **Settings**: Real-time protection and notification preferences

## Technical Details

### Architecture

- **Manifest V3**: Uses the latest Chrome extension API
- **Service Worker**: Background processing for email analysis
- **Content Scripts**: Inject scanning functionality into email platforms
- **Storage API**: Secure local storage for scan results and settings

### Supported Platforms

- **Gmail**: `mail.google.com`
- **Outlook.com**: `outlook.live.com`
- **Office 365**: `outlook.office.com`, `outlook.office365.com`

### API Integration

The extension communicates with the Aman cybersecurity backend:
- **Backend URL**: `http://localhost:8001/api`
- **Endpoints**: Email scanning, link analysis, threat intelligence
- **Security**: All communication is encrypted and logged

## Privacy & Security

### Data Handling

- **Local Processing**: Initial analysis happens locally
- **Secure Transmission**: API calls use HTTPS encryption
- **No Storage**: Email content is not permanently stored
- **Anonymous Scanning**: Personal information is not collected

### Permissions

The extension requires these permissions:
- **activeTab**: Access current email tab for scanning
- **storage**: Store scan results and user preferences
- **scripting**: Inject scanning functionality
- **host_permissions**: Access Gmail and Outlook domains

## Development

### File Structure

```
browser-extension/
├── manifest.json          # Extension configuration
├── src/
│   └── background.js      # Service worker
├── content/
│   ├── content.js         # Email platform integration
│   └── content.css        # Styling for indicators
├── popup/
│   ├── popup.html         # Extension popup interface
│   ├── popup.css          # Popup styling
│   └── popup.js           # Popup functionality
├── icons/                 # Extension icons
└── README.md             # This file
```

### Key Components

1. **Background Script** (`src/background.js`)
   - Handles API communication
   - Manages extension settings
   - Processes scan requests

2. **Content Script** (`content/content.js`)
   - Integrates with Gmail/Outlook
   - Extracts email content
   - Displays security indicators

3. **Popup Interface** (`popup/`)
   - User control panel
   - Statistics display
   - Settings management

### Testing

1. Load the extension in Chrome developer mode
2. Navigate to Gmail or Outlook
3. Open or compose an email to trigger scanning
4. Check the extension popup for activity logs
5. Verify security badges appear on emails

## Configuration

### Default Settings

- **Extension Enabled**: `true`
- **Real-time Protection**: `true`
- **Notifications**: `true`
- **Block Suspicious**: `false` (warning only)

### Customization

Users can modify settings through:
- Extension popup toggles
- Chrome extension options page (future)
- Dashboard integration

## Troubleshooting

### Common Issues

1. **Extension Not Working**
   - Verify it's enabled in `chrome://extensions/`
   - Check that Gmail/Outlook is supported version
   - Refresh the email page

2. **No Security Badges**
   - Check if extension popup shows "Active" status
   - Verify real-time protection is enabled
   - Try refreshing the scan from popup

3. **API Connection Issues**
   - Ensure backend server is running on localhost:8001
   - Check browser console for error messages
   - Verify network connectivity

### Debug Information

- Check browser console (F12) for error logs
- Review extension popup for scan activity
- Monitor network tab for API calls

## Future Enhancements

- **Custom Rules**: User-defined scanning criteria
- **Whitelist/Blacklist**: Manual domain management
- **Advanced Analytics**: Detailed threat reports
- **Mobile Support**: Extension for mobile browsers
- **Team Management**: Organization-wide policies

## Support

For technical support or feature requests:
- **Dashboard**: Access through extension popup
- **Documentation**: Available in main application
- **Contact**: Through main Aman cybersecurity platform

## Version History

### v1.0.0 (Current)
- Initial release
- Gmail and Outlook support
- Real-time scanning
- Visual security indicators
- Basic popup interface
- Local storage for scan results