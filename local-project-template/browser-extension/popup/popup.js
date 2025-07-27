// Popup JavaScript for Aman Cybersecurity Extension
console.log('Aman Extension Popup - Loading');

// DOM Elements
let extensionStatus;
let statusIndicator;
let statusText;
let emailsScanned;
let threatsBlocked;
let riskScore;
let activityList;
let toggleProtection;
let toggleText;
let refreshScan;
let openDashboard;
let realTimeToggle;
let notificationsToggle;

// State
let currentSettings = {};
let scanResults = [];

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', initializePopup);

function initializePopup() {
    console.log('Initializing popup...');
    
    // Get DOM elements
    extensionStatus = document.getElementById('extensionStatus');
    statusIndicator = document.getElementById('statusIndicator');
    statusText = document.getElementById('statusText');
    emailsScanned = document.getElementById('emailsScanned');
    threatsBlocked = document.getElementById('threatsBlocked');
    riskScore = document.getElementById('riskScore');
    activityList = document.getElementById('activityList');
    toggleProtection = document.getElementById('toggleProtection');
    toggleText = document.getElementById('toggleText');
    refreshScan = document.getElementById('refreshScan');
    openDashboard = document.getElementById('openDashboard');
    realTimeToggle = document.getElementById('realTimeToggle');
    notificationsToggle = document.getElementById('notificationsToggle');
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial data
    loadExtensionData();
}

function setupEventListeners() {
    // Toggle protection button
    toggleProtection.addEventListener('click', handleToggleProtection);
    
    // Refresh scan button
    refreshScan.addEventListener('click', handleRefreshScan);
    
    // Open dashboard button
    openDashboard.addEventListener('click', handleOpenDashboard);
    
    // Settings toggles
    realTimeToggle.addEventListener('change', handleRealTimeToggle);
    notificationsToggle.addEventListener('change', handleNotificationsToggle);
    
    // Footer links
    document.getElementById('settingsLink').addEventListener('click', () => {
        chrome.runtime.openOptionsPage();
    });
    
    document.getElementById('helpLink').addEventListener('click', () => {
        chrome.tabs.create({ url: 'https://help.amansecurity.com' });
    });
    
    document.getElementById('aboutLink').addEventListener('click', () => {
        chrome.tabs.create({ url: 'https://amansecurity.com/about' });
    });
}

function loadExtensionData() {
    console.log('Loading extension data...');
    
    // Load settings and auth status
    chrome.runtime.sendMessage({ action: 'getSettings' }, (response) => {
        if (response && response.success) {
            currentSettings = response.settings;
            updateUI();
        }
    });
    
    // Check authentication status
    chrome.runtime.sendMessage({ action: 'getAuthStatus' }, (response) => {
        if (response && response.success) {
            updateAuthUI(response.authenticated, response.userEmail);
        }
    });
    
    // Load scan results
    chrome.storage.local.get(['scanResults'], (result) => {
        scanResults = result.scanResults || [];
        updateStats();
        updateActivity();
    });
}

function updateAuthUI(isAuthenticated, userEmail) {
    const authSection = document.getElementById('authSection');
    const statsSection = document.querySelector('.stats-section');
    
    if (!authSection) {
        // Create auth section if it doesn't exist
        const authDiv = document.createElement('div');
        authDiv.id = 'authSection';
        authDiv.className = 'auth-section';
        
        if (isAuthenticated) {
            authDiv.innerHTML = `
                <div class="auth-status authenticated">
                    <div class="auth-icon">✓</div>
                    <div>
                        <div class="auth-title">Authenticated</div>
                        <div class="auth-email">${userEmail || 'User'}</div>
                    </div>
                </div>
            `;
        } else {
            authDiv.innerHTML = `
                <div class="auth-status not-authenticated">
                    <div class="auth-icon">⚠</div>
                    <div>
                        <div class="auth-title">Login Required</div>
                        <div class="auth-message">Log in for AI-powered protection</div>
                    </div>
                    <button class="auth-btn" id="loginBtn">Login</button>
                </div>
            `;
            
            // Add login button listener
            setTimeout(() => {
                const loginBtn = document.getElementById('loginBtn');
                if (loginBtn) {
                    loginBtn.addEventListener('click', handleLogin);
                }
            }, 100);
        }
        
        // Insert after header
        const header = document.querySelector('.header');
        header.parentNode.insertBefore(authDiv, statsSection);
    }
    
    // Update stats visibility based on auth
    if (statsSection) {
        statsSection.style.opacity = isAuthenticated ? '1' : '0.5';
    }
}

function handleLogin() {
    // Open login page
    chrome.tabs.create({ 
        url: 'https://f8e0a18c-634d-449c-bde8-c523f13f683c.preview.emergentagent.com/auth'
    });
}

function updateUI() {
    // Update status
    const isEnabled = currentSettings.extensionEnabled;
    statusIndicator.className = `status-indicator ${isEnabled ? 'active' : ''}`;
    statusText.textContent = isEnabled ? 'Active' : 'Disabled';
    
    // Update toggle button
    toggleText.textContent = isEnabled ? 'Disable Protection' : 'Enable Protection';
    toggleProtection.className = `action-btn primary ${isEnabled ? '' : 'disabled'}`;
    
    // Update settings toggles
    realTimeToggle.checked = currentSettings.realTimeProtection;
    notificationsToggle.checked = currentSettings.showNotifications;
}

function updateStats() {
    const today = new Date().toDateString();
    const todayScans = scanResults.filter(scan => 
        new Date(scan.timestamp).toDateString() === today
    );
    
    const threatsToday = todayScans.filter(scan => 
        scan.riskLevel === 'danger' || scan.riskLevel === 'warning'
    );
    
    // Calculate average risk score
    const avgRisk = todayScans.length > 0 
        ? todayScans.reduce((sum, scan) => sum + scan.riskScore, 0) / todayScans.length
        : 0;
    
    let riskLevel = 'Low';
    if (avgRisk >= 60) riskLevel = 'High';
    else if (avgRisk >= 30) riskLevel = 'Medium';
    
    // Update stats display
    emailsScanned.textContent = todayScans.length;
    threatsBlocked.textContent = threatsToday.length;
    riskScore.textContent = riskLevel;
    
    // Update stat colors based on risk
    riskScore.style.color = riskLevel === 'High' ? '#ef4444' : 
                           riskLevel === 'Medium' ? '#f59e0b' : '#24fa39';
}

function updateActivity() {
    // Clear existing activity
    activityList.innerHTML = '';
    
    if (scanResults.length === 0) {
        activityList.innerHTML = '<div class="no-activity">No recent activity</div>';
        return;
    }
    
    // Show last 5 results
    const recentScans = scanResults.slice(0, 5);
    
    recentScans.forEach(scan => {
        const activityItem = createActivityItem(scan);
        activityList.appendChild(activityItem);
    });
}

function createActivityItem(scan) {
    const item = document.createElement('div');
    item.className = 'activity-item';
    
    const iconClass = scan.riskLevel;
    const iconSymbol = scan.riskLevel === 'safe' ? '✓' : 
                      scan.riskLevel === 'warning' ? '⚠' : '⚠';
    
    const timeAgo = getTimeAgo(new Date(scan.timestamp));
    
    item.innerHTML = `
        <div class="activity-icon ${iconClass}">
            ${iconSymbol}
        </div>
        <div class="activity-content">
            <div class="activity-title">
                ${scan.emailData.subject || 'Email Scan'}
            </div>
            <div class="activity-details">
                ${scan.explanation}
            </div>
        </div>
        <div class="activity-time">
            ${timeAgo}
        </div>
    `;
    
    return item;
}

function getTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
}

function handleToggleProtection() {
    const newState = !currentSettings.extensionEnabled;
    
    chrome.runtime.sendMessage({
        action: 'updateSettings',
        data: { extensionEnabled: newState }
    }, (response) => {
        if (response && response.success) {
            currentSettings.extensionEnabled = newState;
            updateUI();
            
            // Notify content scripts
            chrome.tabs.query({ url: ['*://mail.google.com/*', '*://outlook.live.com/*'] }, (tabs) => {
                tabs.forEach(tab => {
                    chrome.tabs.sendMessage(tab.id, {
                        action: 'toggleExtension',
                        enabled: newState
                    });
                });
            });
        }
    });
}

function handleRefreshScan() {
    // Add loading state
    refreshScan.classList.add('loading');
    refreshScan.textContent = 'Refreshing...';
    
    // Notify content scripts to refresh
    chrome.tabs.query({ 
        url: ['*://mail.google.com/*', '*://outlook.live.com/*', '*://outlook.office.com/*'] 
    }, (tabs) => {
        tabs.forEach(tab => {
            chrome.tabs.sendMessage(tab.id, {
                action: 'refreshScanning'
            });
        });
    });
    
    // Reset button after delay
    setTimeout(() => {
        refreshScan.classList.remove('loading');
        refreshScan.textContent = 'Refresh Scan';
        
        // Reload data
        loadExtensionData();
    }, 2000);
}

function handleOpenDashboard() {
    // Use the correct production URL
    chrome.tabs.create({ 
        url: 'https://f8e0a18c-634d-449c-bde8-c523f13f683c.preview.emergentagent.com/dashboard' 
    });
}

function handleRealTimeToggle() {
    chrome.runtime.sendMessage({
        action: 'updateSettings',
        data: { realTimeProtection: realTimeToggle.checked }
    }, (response) => {
        if (response && response.success) {
            currentSettings.realTimeProtection = realTimeToggle.checked;
        }
    });
}

function handleNotificationsToggle() {
    chrome.runtime.sendMessage({
        action: 'updateSettings',
        data: { showNotifications: notificationsToggle.checked }
    }, (response) => {
        if (response && response.success) {
            currentSettings.showNotifications = notificationsToggle.checked;
        }
    });
}

// Listen for storage changes to update UI
chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'local' && changes.scanResults) {
        scanResults = changes.scanResults.newValue || [];
        updateStats();
        updateActivity();
    }
});

// Listen for runtime messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.action) {
        case 'updatePopup':
            loadExtensionData();
            sendResponse({ success: true });
            break;
    }
});

console.log('Aman Extension Popup - Initialized');