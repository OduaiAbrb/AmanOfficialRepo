// Extension Authentication Bridge - Complete Version
console.log('🔗 Extension Auth Bridge Loading...');

// Extension ID - Replace with your actual extension ID when published
const EXTENSION_ID = 'your-extension-id-here';

// Function to send auth data to extension
function sendAuthToExtension(authData) {
    try {
        console.log('📤 Sending auth data to extension:', authData.email);
        
        // Method 1: PostMessage for content script communication
        window.postMessage({
            type: 'AMAN_AUTH_SUCCESS',
            source: 'web_app',
            data: authData
        }, window.location.origin);
        
        // Method 2: Chrome extension API (if available)
        if (window.chrome && window.chrome.runtime) {
            // Try to send to extension
            chrome.runtime.sendMessage(
                EXTENSION_ID,
                {
                    action: 'authenticate',
                    data: authData
                },
                (response) => {
                    if (chrome.runtime.lastError) {
                        console.log('⚠️ Extension not available:', chrome.runtime.lastError.message);
                    } else if (response) {
                        console.log('✅ Extension auth response:', response);
                        
                        // Show success notification
                        showAuthNotification('success', `Extension authenticated for ${authData.email}`);
                    }
                }
            );
        }
        
        // Method 3: Local storage for extension to read
        localStorage.setItem('aman_extension_auth', JSON.stringify({
            ...authData,
            timestamp: Date.now()
        }));
        
        console.log('✅ Auth data broadcast complete');
        return true;
    } catch (error) {
        console.error('❌ Failed to send auth to extension:', error);
        return false;
    }
}

// Show authentication notification
function showAuthNotification(type, message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : '#ef4444'};
        color: white;
        padding: 12px 16px;
        border-radius: 6px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        font-family: system-ui, sans-serif;
        font-size: 14px;
        max-width: 300px;
        animation: slideIn 0.3s ease-out;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 16px;">${type === 'success' ? '✅' : '❌'}</span>
            <span>${message}</span>
        </div>
    `;
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Listen for auth success from React app
window.addEventListener('message', (event) => {
    // Security check
    if (event.origin !== window.location.origin) {
        return;
    }
    
    if (event.data.type === 'AUTH_SUCCESS' && event.data.data) {
        console.log('🔐 Auth success detected from React app');
        const success = sendAuthToExtension(event.data.data);
        
        if (success) {
            showAuthNotification('success', 'Extension authentication successful!');
        } else {
            showAuthNotification('error', 'Extension authentication failed');
        }
    }
});

// Check for existing auth on page load
function checkExistingAuth() {
    try {
        const token = localStorage.getItem('authToken');
        const user = localStorage.getItem('user');
        
        if (token && user) {
            const userData = JSON.parse(user);
            console.log('🔍 Found existing auth, sending to extension...');
            
            sendAuthToExtension({
                token: token,
                email: userData.email,
                name: userData.name || userData.email
            });
        } else {
            console.log('ℹ️ No existing auth found');
        }
    } catch (error) {
        console.error('❌ Failed to check existing auth:', error);
    }
}

// Handle logout
function handleLogout() {
    try {
        // Clear extension auth data
        localStorage.removeItem('aman_extension_auth');
        
        // Notify extension of logout
        if (window.chrome && window.chrome.runtime) {
            chrome.runtime.sendMessage(
                EXTENSION_ID,
                { action: 'logout' },
                (response) => {
                    if (!chrome.runtime.lastError && response) {
                        console.log('✅ Extension logout successful');
                    }
                }
            );
        }
        
        // PostMessage for content scripts
        window.postMessage({
            type: 'AMAN_LOGOUT',
            source: 'web_app'
        }, window.location.origin);
        
        console.log('✅ Logout broadcast complete');
        
    } catch (error) {
        console.error('❌ Logout broadcast failed:', error);
    }
}

// Listen for logout events
window.addEventListener('beforeunload', () => {
    // Don't logout extension when just refreshing/navigating
    // Extension should maintain auth across page changes
});

// Listen for storage changes (logout from other tab)
window.addEventListener('storage', (event) => {
    if (event.key === 'authToken' && event.newValue === null) {
        console.log('🚪 Logout detected from storage change');
        handleLogout();
    }
});

// Extension status checker
async function checkExtensionStatus() {
    try {
        if (window.chrome && window.chrome.runtime) {
            chrome.runtime.sendMessage(
                EXTENSION_ID,
                { action: 'getAuthStatus' },
                (response) => {
                    if (!chrome.runtime.lastError && response) {
                        console.log('📊 Extension status:', response);
                        
                        if (!response.authenticated) {
                            // Extension not authenticated, try to authenticate
                            checkExistingAuth();
                        }
                    }
                }
            );
        }
    } catch (error) {
        console.log('⚠️ Extension status check failed:', error);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM ready, initializing auth bridge...');
    
    // Check for existing auth
    setTimeout(checkExistingAuth, 1000);
    
    // Check extension status
    setTimeout(checkExtensionStatus, 2000);
    
    console.log('✅ Extension Auth Bridge Ready');
});

// Export functions for React app to use
window.amanExtensionBridge = {
    sendAuth: sendAuthToExtension,
    handleLogout: handleLogout,
    checkStatus: checkExtensionStatus
};

console.log('🔗 Extension Auth Bridge Loaded Successfully');