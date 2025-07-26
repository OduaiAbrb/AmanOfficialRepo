// Background service worker for Aman Cybersecurity Extension
console.log('Aman Cybersecurity Extension - Background script loaded');

// API Configuration - Use environment variable for backend URL
const API_BASE_URL = 'https://a7ef5366-e6cc-4ff4-9acc-af148819b2aa.preview.emergentagent.com/api';

// Authentication state
let authToken = null;
let isAuthenticated = false;

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

  // Check for existing authentication
  checkAuthentication();
});

// Check authentication status
async function checkAuthentication() {
  try {
    const stored = await chrome.storage.local.get(['authToken', 'userEmail']);
    if (stored.authToken) {
      authToken = stored.authToken;
      // Verify token is still valid
      const isValid = await verifyAuthToken(stored.authToken);
      if (isValid) {
        isAuthenticated = true;
        console.log('Extension authenticated for user:', stored.userEmail);
      } else {
        // Token expired, clear storage
        await chrome.storage.local.remove(['authToken', 'userEmail']);
        isAuthenticated = false;
      }
    }
  } catch (error) {
    console.error('Authentication check failed:', error);
  }
}

// Verify auth token with backend
async function verifyAuthToken(token) {
  try {
    const response = await fetch(`${API_BASE_URL}/user/profile`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.ok;
  } catch (error) {
    console.error('Token verification failed:', error);
    return false;
  }
}

// Prompt user to authenticate
async function promptAuthentication() {
  try {
    // Open authentication page
    const authUrl = `https://a7ef5366-e6cc-4ff4-9acc-af148819b2aa.preview.emergentagent.com/`;
    await chrome.tabs.create({ url: authUrl });
    
    // Show notification
    if (chrome.notifications) {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: '../icons/icon48.png',
        title: 'Aman Security Authentication',
        message: 'Please log in to enable email protection features.'
      });
    }
  } catch (error) {
    console.error('Authentication prompt failed:', error);
  }
}

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
      
    case 'authenticate':
      handleAuthentication(request.data, sendResponse);
      return true;
      
    case 'getAuthStatus':
      sendResponse({ 
        success: true, 
        authenticated: isAuthenticated,
        token: authToken 
      });
      break;
      
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

// Handle authentication
async function handleAuthentication(authData, sendResponse) {
  try {
    if (authData.token && authData.email) {
      // Store authentication data
      await chrome.storage.local.set({
        authToken: authData.token,
        userEmail: authData.email
      });
      
      authToken = authData.token;
      isAuthenticated = true;
      
      console.log('Extension authenticated successfully');
      
      sendResponse({
        success: true,
        message: 'Authentication successful'
      });
    } else {
      sendResponse({
        success: false,
        error: 'Invalid authentication data'
      });
    }
  } catch (error) {
    console.error('Authentication handling failed:', error);
    sendResponse({
      success: false,
      error: error.message
    });
  }
}

// Email scanning function with AI backend integration
async function handleEmailScan(emailData, sendResponse) {
  try {
    console.log('Scanning email:', emailData.subject);
    
    // Check authentication
    if (!isAuthenticated) {
      await promptAuthentication();
      sendResponse({
        success: false,
        error: 'Authentication required',
        needsAuth: true
      });
      return;
    }
    
    // Prepare email data for API
    const scanRequest = {
      email_subject: emailData.subject || '',
      email_body: emailData.body || '',
      sender: emailData.sender || '',
      recipient: emailData.recipient || ''
    };
    
    // Call AI-powered email scanning API
    const scanResult = await performEmailScanAPI(scanRequest);
    
    // Transform API response to extension format
    const extensionResult = transformEmailScanResult(scanResult, emailData);
    
    // Store scan result
    await storeScanResult(extensionResult);
    
    sendResponse({
      success: true,
      result: extensionResult
    });
    
  } catch (error) {
    console.error('Email scan error:', error);
    
    // Fallback to local scanning if API fails
    if (error.message.includes('401') || error.message.includes('auth')) {
      await promptAuthentication();
      sendResponse({
        success: false,
        error: 'Authentication expired',
        needsAuth: true
      });
    } else {
      // Use fallback scanning
      const fallbackResult = await performFallbackEmailScan(emailData);
      await storeScanResult(fallbackResult);
      
      sendResponse({
        success: true,
        result: fallbackResult,
        fallback: true
      });
    }
  }
}

// Link scanning function with AI backend integration
async function handleLinkScan(linkData, sendResponse) {
  try {
    console.log('Scanning link:', linkData.url);
    
    if (!isAuthenticated) {
      // For links, provide basic local scanning without authentication
      const localResult = await performLocalLinkScan(linkData);
      sendResponse({
        success: true,
        result: localResult,
        local: true
      });
      return;
    }
    
    // Call AI-powered link scanning API
    const scanResult = await performLinkScanAPI(linkData);
    
    // Transform API response to extension format
    const extensionResult = transformLinkScanResult(scanResult, linkData);
    
    sendResponse({
      success: true,
      result: extensionResult
    });
    
  } catch (error) {
    console.error('Link scan error:', error);
    
    // Fallback to local scanning
    const fallbackResult = await performLocalLinkScan(linkData);
    sendResponse({
      success: true,
      result: fallbackResult,
      fallback: true
    });
  }
}

// AI-powered email scanning API call
async function performEmailScanAPI(emailData) {
  const response = await fetch(`${API_BASE_URL}/scan/email`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(emailData)
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      isAuthenticated = false;
      authToken = null;
      await chrome.storage.local.remove(['authToken', 'userEmail']);
    }
    throw new Error(`API request failed: ${response.status}`);
  }
  
  return await response.json();
}

// AI-powered link scanning API call
async function performLinkScanAPI(linkData) {
  const response = await fetch(`${API_BASE_URL}/scan/link`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      url: linkData.url,
      context: linkData.text || ''
    })
  });
  
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  
  return await response.json();
}

// Transform API email scan result to extension format
function transformEmailScanResult(apiResult, originalData) {
  // Map API status to extension risk level
  const statusToRiskLevel = {
    'safe': 'safe',
    'potential_phishing': 'warning', 
    'phishing': 'danger'
  };
  
  return {
    id: apiResult.id || generateScanId(),
    timestamp: new Date().toISOString(),
    riskLevel: statusToRiskLevel[apiResult.status] || 'safe',
    riskScore: Math.round(apiResult.risk_score || 0),
    explanation: apiResult.explanation || 'Scan completed',
    threats: apiResult.detected_threats || [],
    threatSources: apiResult.threat_sources || [],
    recommendations: apiResult.recommendations || [],
    emailData: {
      subject: originalData.subject,
      sender: originalData.sender,
      recipient: originalData.recipient
    },
    aiPowered: true
  };
}

// Transform API link scan result to extension format
function transformLinkScanResult(apiResult, originalData) {
  const statusToRiskLevel = {
    'safe': 'safe',
    'potential_phishing': 'warning',
    'phishing': 'danger'
  };
  
  return {
    id: generateScanId(),
    timestamp: new Date().toISOString(),
    url: originalData.url,
    riskLevel: statusToRiskLevel[apiResult.status] || 'safe',
    riskScore: Math.round(apiResult.risk_score || 0),
    explanation: apiResult.explanation || 'Link scan completed',
    threatCategories: apiResult.threat_categories || [],
    isShortened: apiResult.is_shortened || false,
    aiPowered: true
  };
}

// Fallback email scanning (when API unavailable)
async function performFallbackEmailScan(emailData) {
  // Simple keyword-based scanning
  const suspiciousKeywords = [
    'urgent', 'verify account', 'click here', 'limited time', 'suspended',
    'congratulations', 'winner', 'claim now', 'act fast', 'expires today'
  ];
  
  const body = (emailData.body || '').toLowerCase();
  const subject = (emailData.subject || '').toLowerCase();
  
  let suspiciousScore = 0;
  const detectedThreats = [];
  
  suspiciousKeywords.forEach(keyword => {
    if (body.includes(keyword) || subject.includes(keyword)) {
      suspiciousScore += 15;
      detectedThreats.push(keyword.replace('_', ' '));
    }
  });
  
  // Check sender domain
  const sender = emailData.sender || '';
  if (!sender.includes('@') || sender.includes('noreply') || sender.includes('no-reply')) {
    suspiciousScore += 10;
  }
  
  const riskScore = Math.min(suspiciousScore, 100);
  let riskLevel = 'safe';
  
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
    explanation: generateFallbackExplanation(riskLevel),
    threats: detectedThreats,
    emailData: {
      subject: emailData.subject,
      sender: emailData.sender,
      recipient: emailData.recipient
    },
    fallback: true
  };
}

// Local link scanning (basic checks)
async function performLocalLinkScan(linkData) {
  const url = linkData.url || '';
  const suspiciousDomains = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co'];
  const dangerousDomains = ['phishing-site.com', 'malware-site.net'];
  
  let riskScore = 0;
  let riskLevel = 'safe';
  let explanation = 'Link appears safe';
  
  // Check for dangerous domains
  if (dangerousDomains.some(domain => url.includes(domain))) {
    riskScore = 90;
    riskLevel = 'danger';
    explanation = 'Known malicious domain detected';
  }
  // Check for shortened URLs
  else if (suspiciousDomains.some(domain => url.includes(domain))) {
    riskScore = 40;
    riskLevel = 'warning';
    explanation = 'Shortened URL - exercise caution';
  }
  // Check for suspicious patterns
  else if (url.includes('login') || url.includes('verify') || url.includes('secure')) {
    riskScore = 25;
    riskLevel = 'warning';
    explanation = 'URL contains authentication-related keywords';
  }
  
  return {
    id: generateScanId(),
    timestamp: new Date().toISOString(),
    url: url,
    riskLevel: riskLevel,
    riskScore: riskScore,
    explanation: explanation,
    local: true
  };
}

// Helper functions
function generateScanId() {
  return 'scan_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function generateFallbackExplanation(riskLevel) {
  switch (riskLevel) {
    case 'danger':
      return 'High risk indicators detected. Multiple suspicious patterns found.';
    case 'warning':
      return 'Potentially suspicious content. Exercise caution with this email.';
    default:
      return 'Email appears safe. No major threats detected.';
  }
}

// Storage functions (enhanced)
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
    
    // Update badge if threats detected
    updateExtensionBadge(result);
    
  } catch (error) {
    console.error('Failed to store scan result:', error);
  }
}

// Update extension badge based on scan results
async function updateExtensionBadge(result) {
  try {
    if (result.riskLevel === 'danger') {
      await chrome.action.setBadgeText({ text: '!' });
      await chrome.action.setBadgeBackgroundColor({ color: '#ef4444' });
    } else if (result.riskLevel === 'warning') {
      await chrome.action.setBadgeText({ text: '?' });
      await chrome.action.setBadgeBackgroundColor({ color: '#f59e0b' });
    }
    
    // Clear badge after 5 seconds
    setTimeout(async () => {
      await chrome.action.setBadgeText({ text: '' });
    }, 5000);
    
  } catch (error) {
    console.error('Failed to update badge:', error);
  }
}

// Settings functions (enhanced)
async function getExtensionSettings(sendResponse) {
  try {
    const settings = await chrome.storage.sync.get([
      'extensionEnabled',
      'scanningEnabled', 
      'realTimeProtection',
      'blockSuspicious',
      'showNotifications'
    ]);
    
    // Add authentication status
    settings.isAuthenticated = isAuthenticated;
    settings.userEmail = authToken ? (await chrome.storage.local.get(['userEmail'])).userEmail : null;
    
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

// Initialize on startup
chrome.runtime.onStartup.addListener(() => {
  checkAuthentication();
});

console.log('Aman Cybersecurity Extension - Background script initialized with AI integration');