// Browser Extension Authentication Bridge
// This script helps pass authentication tokens from the web app to the browser extension

(function() {
    'use strict';
    
    console.log('Aman Extension Auth Bridge - Loading');

    // Check if user is logged in and has extension
    function checkExtensionAndAuth() {
        // Get auth token from localStorage or wherever it's stored
        const authToken = localStorage.getItem('authToken') || 
                         sessionStorage.getItem('authToken') ||
                         getCookie('authToken');
        
        const userEmail = localStorage.getItem('userEmail') || 
                         sessionStorage.getItem('userEmail') ||
                         getCookie('userEmail');
        
        if (authToken && userEmail) {
            // Try to communicate with extension
            if (window.chrome && window.chrome.runtime) {
                try {
                    // Send authentication data to extension
                    window.chrome.runtime.sendMessage(
                        'aman-cybersecurity-extension', // Extension ID placeholder
                        {
                            action: 'authenticate',
                            data: {
                                token: authToken,
                                email: userEmail
                            }
                        },
                        function(response) {
                            if (window.chrome.runtime.lastError) {
                                console.log('Extension not found or not responding');
                            } else if (response && response.success) {
                                console.log('Extension authenticated successfully');
                                showExtensionAuthSuccess();
                            }
                        }
                    );
                } catch (error) {
                    console.log('Could not communicate with extension:', error);
                }
            }
        }
    }
    
    // Get cookie value by name
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    // Show success message when extension is authenticated
    function showExtensionAuthSuccess() {
        // Create a subtle notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f0fdf4;
            border: 1px solid #24fa39;
            color: #166534;
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            animation: slideInRight 0.3s ease-out;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 16px;">🛡️</span>
                <span>Browser Extension Connected</span>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; color: #166534; font-size: 18px; cursor: pointer; margin-left: 8px;">×</button>
            </div>
        `;
        
        // Add animation
        if (!document.querySelector('#extension-auth-styles')) {
            const style = document.createElement('style');
            style.id = 'extension-auth-styles';
            style.textContent = `
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.opacity = '0';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }
    
    // Listen for authentication events
    window.addEventListener('storage', function(e) {
        if (e.key === 'authToken' || e.key === 'userEmail') {
            setTimeout(checkExtensionAndAuth, 500);
        }
    });
    
    // Check on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(checkExtensionAndAuth, 1000);
        });
    } else {
        setTimeout(checkExtensionAndAuth, 1000);
    }
    
    // Export function for manual triggering
    window.amanExtensionAuth = {
        checkAuth: checkExtensionAndAuth,
        sendAuthToExtension: function(token, email) {
            if (window.chrome && window.chrome.runtime) {
                try {
                    window.chrome.runtime.sendMessage(
                        'aman-cybersecurity-extension',
                        {
                            action: 'authenticate',
                            data: { token: token, email: email }
                        },
                        function(response) {
                            console.log('Manual auth response:', response);
                        }
                    );
                } catch (error) {
                    console.log('Manual auth failed:', error);
                }
            }
        }
    };
    
    console.log('Aman Extension Auth Bridge - Loaded');
})();