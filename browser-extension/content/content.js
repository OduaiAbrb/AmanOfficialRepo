// Content script for Gmail and Outlook integration
console.log('Aman Cybersecurity Extension - Content script loaded');

// Configuration
const EXTENSION_ID = 'aman-cybersecurity';
let isEnabled = true;
let scanningActive = false;

// DOM selectors for different email platforms
const SELECTORS = {
  gmail: {
    emailBody: '[data-message-id] .ii.gt div',
    emailSubject: '[data-message-id] h2',
    emailSender: '[data-message-id] .go span[email]',
    emailContainer: '[data-message-id]',
    links: '[data-message-id] a[href]'
  },
  outlook: {
    emailBody: '[aria-label="Message body"]',
    emailSubject: '[aria-label="Message subject"]',
    emailSender: '.allowTextSelection',
    emailContainer: '.wide-content-host',
    links: '.wide-content-host a[href]'
  }
};

// Detect email platform
function detectPlatform() {
  const hostname = window.location.hostname;
  if (hostname.includes('mail.google.com')) {
    return 'gmail';
  } else if (hostname.includes('outlook')) {
    return 'outlook';
  }
  return null;
}

// Initialize the extension
function initialize() {
  const platform = detectPlatform();
  if (!platform) {
    console.log('Aman Extension: Unsupported platform');
    return;
  }
  
  console.log(`Aman Extension: Initializing for ${platform}`);
  
  // Load extension settings
  loadSettings();
  
  // Start monitoring for new emails
  startEmailMonitoring(platform);
  
  // Add extension indicator
  addExtensionIndicator();
}

// Load extension settings
function loadSettings() {
  chrome.runtime.sendMessage({ action: 'getSettings' }, (response) => {
    if (response && response.success) {
      isEnabled = response.settings.extensionEnabled;
      console.log('Extension settings loaded:', response.settings);
    }
  });
}

// Monitor for new emails
function startEmailMonitoring(platform) {
  const observer = new MutationObserver((mutations) => {
    if (!isEnabled) return;
    
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          processNewEmails(node, platform);
        }
      });
    });
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
  
  // Process existing emails
  processExistingEmails(platform);
}

// Process existing emails on page load
function processExistingEmails(platform) {
  console.log('Processing existing emails...');
  
  const emailContainers = document.querySelectorAll(SELECTORS[platform].emailContainer);
  emailContainers.forEach((container) => {
    if (!container.querySelector('.aman-security-badge')) {
      processEmail(container, platform);
    }
  });
}

// Process new emails
function processNewEmails(node, platform) {
  if (node.matches && node.matches(SELECTORS[platform].emailContainer)) {
    processEmail(node, platform);
  }
  
  const emailContainers = node.querySelectorAll ? node.querySelectorAll(SELECTORS[platform].emailContainer) : [];
  emailContainers.forEach((container) => {
    if (!container.querySelector('.aman-security-badge')) {
      processEmail(container, platform);
    }
  });
}

// Process individual email
function processEmail(emailContainer, platform) {
  try {
    const emailData = extractEmailData(emailContainer, platform);
    if (!emailData) return;
    
    console.log('Processing email:', emailData.subject);
    
    // Add scanning indicator
    addScanningIndicator(emailContainer);
    
    // Scan the email
    scanEmail(emailData, emailContainer);
    
    // Scan links in the email
    scanLinksInEmail(emailContainer, platform);
    
  } catch (error) {
    console.error('Error processing email:', error);
  }
}

// Extract email data
function extractEmailData(container, platform) {
  try {
    const selectors = SELECTORS[platform];
    
    const subjectElement = container.querySelector(selectors.emailSubject);
    const senderElement = container.querySelector(selectors.emailSender);
    const bodyElement = container.querySelector(selectors.emailBody);
    
    if (!bodyElement) return null;
    
    return {
      subject: subjectElement ? subjectElement.textContent.trim() : 'No Subject',
      sender: senderElement ? (senderElement.getAttribute('email') || senderElement.textContent.trim()) : 'Unknown Sender',
      recipient: getCurrentUserEmail(),
      body: bodyElement.textContent.trim(),
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    console.error('Error extracting email data:', error);
    return null;
  }
}

// Get current user email (best effort)
function getCurrentUserEmail() {
  try {
    // Gmail
    const gmailElement = document.querySelector('[data-hovercard-id]');
    if (gmailElement) {
      return gmailElement.getAttribute('data-hovercard-id');
    }
    
    // Outlook
    const outlookElement = document.querySelector('[data-automationid="ContextualMenuButton"]');
    if (outlookElement) {
      return outlookElement.textContent.trim();
    }
    
    return 'user@unknown.com';
  } catch (error) {
    return 'user@unknown.com';
  }
}

// Scan email
function scanEmail(emailData, container) {
  chrome.runtime.sendMessage({
    action: 'scanEmail',
    data: emailData
  }, (response) => {
    if (response && response.success) {
      displayScanResult(container, response.result);
    } else {
      console.error('Email scan failed:', response?.error);
      removeScanningIndicator(container);
    }
  });
}

// Scan links in email
function scanLinksInEmail(container, platform) {
  const links = container.querySelectorAll(SELECTORS[platform].links);
  
  links.forEach((link) => {
    if (link.href && !link.querySelector('.aman-link-badge')) {
      scanLink(link);
    }
  });
}

// Scan individual link
function scanLink(linkElement) {
  const linkData = {
    url: linkElement.href,
    text: linkElement.textContent.trim()
  };
  
  chrome.runtime.sendMessage({
    action: 'scanLink',
    data: linkData
  }, (response) => {
    if (response && response.success) {
      addLinkIndicator(linkElement, response.result);
    }
  });
}

// Add scanning indicator
function addScanningIndicator(container) {
  const indicator = document.createElement('div');
  indicator.className = 'aman-scanning-indicator';
  indicator.innerHTML = `
    <div style="
      display: inline-flex;
      align-items: center;
      background: #f0f9ff;
      border: 1px solid #e0f2fe;
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 12px;
      color: #0284c7;
      margin: 4px 0;
    ">
      <div style="
        width: 12px;
        height: 12px;
        border: 2px solid #0284c7;
        border-radius: 50%;
        border-top: 2px solid transparent;
        animation: spin 1s linear infinite;
        margin-right: 6px;
      "></div>
      Scanning for threats...
    </div>
  `;
  
  // Add spinner animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
  
  container.insertBefore(indicator, container.firstChild);
}

// Remove scanning indicator
function removeScanningIndicator(container) {
  const indicator = container.querySelector('.aman-scanning-indicator');
  if (indicator) {
    indicator.remove();
  }
}

// Display scan result
function displayScanResult(container, result) {
  removeScanningIndicator(container);
  
  const badge = createSecurityBadge(result);
  container.insertBefore(badge, container.firstChild);
  
  // Log result
  console.log('Email scan result:', result);
  
  // Show notification for high-risk emails
  if (result.riskLevel === 'danger' && result.aiPowered) {
    showThreatNotification(result);
  }
}

// Show threat notification
function showThreatNotification(result) {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = 'aman-threat-notification';
  notification.innerHTML = `
    <div style="
      position: fixed;
      top: 20px;
      right: 20px;
      background: #fee2e2;
      border: 2px solid #ef4444;
      border-radius: 8px;
      padding: 12px;
      max-width: 300px;
      z-index: 10000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      animation: slideIn 0.3s ease-out;
    ">
      <div style="display: flex; align-items: start; gap: 8px;">
        <div style="color: #ef4444; font-size: 18px; line-height: 1;">⚠</div>
        <div>
          <div style="font-weight: 600; color: #dc2626; font-size: 14px;">
            Aman Security Alert
          </div>
          <div style="color: #7f1d1d; font-size: 12px; margin-top: 4px;">
            ${result.explanation || 'High-risk phishing attempt detected'}
          </div>
          ${result.aiPowered ? 
            '<div style="color: #991b1b; font-size: 10px; margin-top: 6px;">AI-Powered Detection</div>' : 
            ''
          }
        </div>
        <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                style="
                  background: none; 
                  border: none; 
                  color: #dc2626; 
                  font-size: 16px; 
                  cursor: pointer;
                  padding: 0;
                  line-height: 1;
                ">×</button>
      </div>
    </div>
  `;
  
  // Add animation styles
  if (!document.querySelector('#aman-notification-styles')) {
    const style = document.createElement('style');
    style.id = 'aman-notification-styles';
    style.textContent = `
      @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
    `;
    document.head.appendChild(style);
  }
  
  document.body.appendChild(notification);
  
  // Auto-remove after 8 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.style.opacity = '0';
      setTimeout(() => notification.remove(), 300);
    }
  }, 8000);
}

// Create security badge
function createSecurityBadge(result) {
  const badge = document.createElement('div');
  badge.className = 'aman-security-badge';
  
  const colors = {
    safe: { bg: '#f0fdf4', border: '#24fa39', text: '#166534', icon: '✓' },
    warning: { bg: '#fffbeb', border: '#f59e0b', text: '#92400e', icon: '⚠' },
    danger: { bg: '#fef2f2', border: '#ef4444', text: '#dc2626', icon: '⚠' }
  };
  
  const color = colors[result.riskLevel] || colors.safe;
  
  badge.innerHTML = `
    <div style="
      display: flex;
      align-items: center;
      background: ${color.bg};
      border: 1px solid ${color.border};
      border-radius: 6px;
      padding: 8px 12px;
      margin: 8px 0;
      font-size: 13px;
      font-weight: 500;
      color: ${color.text};
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    ">
      <span style="margin-right: 8px; font-size: 14px;">${color.icon}</span>
      <div>
        <div style="font-weight: 600; margin-bottom: 2px;">
          Aman Security: ${result.riskLevel.toUpperCase()}
        </div>
        <div style="font-size: 11px; opacity: 0.8;">
          ${result.explanation}
        </div>
        ${result.threats.length > 0 ? `
          <div style="font-size: 11px; margin-top: 4px;">
            Threats: ${result.threats.join(', ')}
          </div>
        ` : ''}
      </div>
      <div style="margin-left: auto; font-size: 11px; opacity: 0.7;">
        Risk: ${result.riskScore}%
      </div>
    </div>
  `;
  
  return badge;
}

// Add link indicator
function addLinkIndicator(linkElement, result) {
  const indicator = document.createElement('span');
  indicator.className = 'aman-link-badge';
  
  const colors = {
    safe: { bg: '#24fa39', text: '#ffffff' },
    warning: { bg: '#f59e0b', text: '#ffffff' },
    danger: { bg: '#ef4444', text: '#ffffff' }
  };
  
  const color = colors[result.riskLevel] || colors.safe;
  
  indicator.innerHTML = `
    <span style="
      display: inline-block;
      background: ${color.bg};
      color: ${color.text};
      font-size: 10px;
      font-weight: bold;
      padding: 2px 6px;
      border-radius: 3px;
      margin-left: 4px;
      vertical-align: middle;
    ">
      ${result.riskLevel.toUpperCase()}
    </span>
  `;
  
  linkElement.appendChild(indicator);
}

// Add extension indicator to page
function addExtensionIndicator() {
  const indicator = document.createElement('div');
  indicator.id = 'aman-extension-indicator';
  indicator.innerHTML = `
    <div style="
      position: fixed;
      top: 10px;
      right: 10px;
      background: #24fa39;
      color: white;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
      z-index: 10000;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      opacity: 0.9;
    ">
      🛡️ Aman Protection Active
    </div>
  `;
  
  document.body.appendChild(indicator);
  
  // Hide after 3 seconds
  setTimeout(() => {
    indicator.style.opacity = '0';
    setTimeout(() => indicator.remove(), 500);
  }, 3000);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

// Listen for runtime messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {
    case 'toggleExtension':
      isEnabled = request.enabled;
      console.log('Extension toggled:', isEnabled);
      break;
      
    case 'refreshScanning':
      if (isEnabled) {
        const platform = detectPlatform();
        if (platform) {
          processExistingEmails(platform);
        }
      }
      break;
  }
  
  sendResponse({ success: true });
});

console.log('Aman Cybersecurity Extension - Content script initialized');