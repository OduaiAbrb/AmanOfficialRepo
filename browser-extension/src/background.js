// Background service worker for Aman Cybersecurity Extension
console.log('Aman Cybersecurity Extension - Background script loaded');

// API Configuration
const API_BASE_URL = 'http://localhost:8001/api';

// Extension installation
chrome.runtime.onInstalled.addListener((details) => {
  console.log('Extension installed:', details.reason);
  
  // Set default settings
  chrome.storage.sync.set({
    extensionEnabled: true,
    scanningEnabled: true,
    realTimeProtection: true,
    blockSuspicious: false,
    showNotifications: true
  });
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received message:', request);

  switch (request.action) {
    case 'scanEmail':
      handleEmailScan(request.data, sendResponse);
      return true; // Keep message channel open for async response
      
    case 'scanLink':
      handleLinkScan(request.data, sendResponse);
      return true;
      
    case 'getSettings':
      getExtensionSettings(sendResponse);
      return true;
      
    case 'updateSettings':
      updateExtensionSettings(request.data, sendResponse);
      return true;
      
    default:
      console.log('Unknown action:', request.action);
      sendResponse({ error: 'Unknown action' });
  }
});

// Email scanning function
async function handleEmailScan(emailData, sendResponse) {
  try {
    console.log('Scanning email:', emailData);
    
    // Mock scan result for now - will integrate with backend API
    const scanResult = await performEmailScan(emailData);
    
    // Store scan result
    await storeScanResult(scanResult);
    
    sendResponse({
      success: true,
      result: scanResult
    });
  } catch (error) {
    console.error('Email scan error:', error);
    sendResponse({
      success: false,
      error: error.message
    });
  }
}

// Link scanning function
async function handleLinkScan(linkData, sendResponse) {
  try {
    console.log('Scanning link:', linkData);
    
    const scanResult = await performLinkScan(linkData);
    
    sendResponse({
      success: true,
      result: scanResult
    });
  } catch (error) {
    console.error('Link scan error:', error);
    sendResponse({
      success: false,
      error: error.message
    });
  }
}

// Mock email scanning (will be replaced with API calls)
async function performEmailScan(emailData) {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Mock analysis logic
  const suspiciousKeywords = ['urgent', 'verify account', 'click here', 'limited time', 'suspended'];
  const suspiciousScore = suspiciousKeywords.reduce((score, keyword) => {
    if (emailData.body.toLowerCase().includes(keyword)) {
      return score + 20;
    }
    return score;
  }, 0);
  
  let riskLevel = 'safe';
  let riskScore = Math.min(suspiciousScore, 100);
  
  if (riskScore >= 60) {
    riskLevel = 'danger';
  } else if (riskScore >= 30) {
    riskLevel = 'warning';
  }
  
  return {
    id: generateScanId(),
    timestamp: new Date().toISOString(),
    riskLevel: riskLevel,
    riskScore: riskScore,
    explanation: generateExplanation(riskLevel, riskScore),
    threats: detectThreats(emailData),
    emailData: {
      subject: emailData.subject,
      sender: emailData.sender,
      recipient: emailData.recipient
    }
  };
}

// Mock link scanning
async function performLinkScan(linkData) {
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Simple mock logic for dangerous domains
  const dangerousDomains = ['bit.ly', 'tinyurl.com', 'suspicious-site.com'];
  const isDangerous = dangerousDomains.some(domain => linkData.url.includes(domain));
  
  return {
    id: generateScanId(),
    timestamp: new Date().toISOString(),
    url: linkData.url,
    riskLevel: isDangerous ? 'danger' : 'safe',
    riskScore: isDangerous ? 80 : 10,
    explanation: isDangerous ? 'Potentially dangerous shortened URL detected' : 'Link appears safe'
  };
}

// Helper functions
function generateScanId() {
  return 'scan_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function generateExplanation(riskLevel, riskScore) {
  switch (riskLevel) {
    case 'danger':
      return 'High risk phishing attempt detected. Multiple suspicious indicators found.';
    case 'warning':
      return 'Potentially suspicious email. Exercise caution before clicking links or providing information.';
    default:
      return 'Email appears safe. No major threats detected.';
  }
}

function detectThreats(emailData) {
  const threats = [];
  
  if (emailData.body.includes('verify account')) {
    threats.push('Account verification request');
  }
  if (emailData.body.includes('click here')) {
    threats.push('Suspicious link request');
  }
  if (emailData.body.includes('urgent')) {
    threats.push('Urgency manipulation');
  }
  
  return threats;
}

// Storage functions
async function storeScanResult(result) {
  try {
    const stored = await chrome.storage.local.get(['scanResults']);
    const scanResults = stored.scanResults || [];
    
    scanResults.unshift(result);
    
    // Keep only last 100 results
    if (scanResults.length > 100) {
      scanResults.splice(100);
    }
    
    await chrome.storage.local.set({ scanResults });
  } catch (error) {
    console.error('Failed to store scan result:', error);
  }
}

// Settings functions
async function getExtensionSettings(sendResponse) {
  try {
    const settings = await chrome.storage.sync.get([
      'extensionEnabled',
      'scanningEnabled', 
      'realTimeProtection',
      'blockSuspicious',
      'showNotifications'
    ]);
    
    sendResponse({
      success: true,
      settings: settings
    });
  } catch (error) {
    sendResponse({
      success: false,
      error: error.message
    });
  }
}

async function updateExtensionSettings(newSettings, sendResponse) {
  try {
    await chrome.storage.sync.set(newSettings);
    
    sendResponse({
      success: true,
      message: 'Settings updated successfully'
    });
  } catch (error) {
    sendResponse({
      success: false,
      error: error.message
    });
  }
}