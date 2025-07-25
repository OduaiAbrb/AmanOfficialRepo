import React, { useState, useEffect } from 'react';
import useWebSocket from '../hooks/useWebSocket';

const RealTimeNotifications = () => {
  const { 
    notifications, 
    threatAlerts, 
    unreadNotifications, 
    unreadThreatAlerts,
    markNotificationRead,
    markThreatAlertRead,
    clearNotifications,
    requestNotificationPermission,
    isConnected,
    connectionStatus
  } = useWebSocket();
  
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState('notifications'); // 'notifications' or 'threats'
  
  // Request notification permission on component mount
  useEffect(() => {
    requestNotificationPermission();
  }, [requestNotificationPermission]);
  
  // Auto-collapse after 10 seconds if no interaction
  useEffect(() => {
    if (isExpanded) {
      const timer = setTimeout(() => {
        setIsExpanded(false);
      }, 10000);
      
      return () => clearTimeout(timer);
    }
  }, [isExpanded]);
  
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };
  
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'high': return 'border-orange-500 bg-orange-50';
      case 'normal': return 'border-blue-500 bg-blue-50';
      case 'low': return 'border-gray-500 bg-gray-50';
      default: return 'border-blue-500 bg-blue-50';
    }
  };
  
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'threat_detected': return '🚨';
      case 'scan_completed': return '✅';
      case 'system_alert': return '⚠️';
      case 'threat_feed': return '🛡️';
      default: return '📢';
    }
  };
  
  const totalUnread = unreadNotifications + unreadThreatAlerts;
  
  if (!isConnected && connectionStatus !== 'connected') {
    return null; // Don't show notification panel if not connected
  }
  
  return (
    <div className="fixed top-20 right-4 z-50">
      {/* Notification Button */}
      <div className="relative">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="bg-white border border-gray-300 rounded-full p-3 shadow-lg hover:shadow-xl transition-all duration-200 relative"
        >
          <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5-5V9.5a4.5 4.5 0 00-9 0V12l-5 5h5a4.5 4.5 0 009 0z" />
          </svg>
          
          {/* Unread Count Badge */}
          {totalUnread > 0 && (
            <span className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold animate-pulse">
              {totalUnread > 99 ? '99+' : totalUnread}
            </span>
          )}
          
          {/* Connection Status Indicator */}
          <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`} />
        </button>
      </div>
      
      {/* Notification Panel */}
      {isExpanded && (
        <div className="absolute top-16 right-0 w-96 bg-white border border-gray-300 rounded-lg shadow-xl max-h-96 overflow-hidden">
          {/* Header */}
          <div className="border-b border-gray-200 px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex space-x-4">
                <button
                  onClick={() => setActiveTab('notifications')}
                  className={`text-sm font-medium pb-2 border-b-2 transition-colors ${
                    activeTab === 'notifications'
                      ? 'text-green-600 border-green-600'
                      : 'text-gray-500 border-transparent hover:text-gray-700'
                  }`}
                >
                  Notifications ({unreadNotifications})
                </button>
                <button
                  onClick={() => setActiveTab('threats')}
                  className={`text-sm font-medium pb-2 border-b-2 transition-colors ${
                    activeTab === 'threats'
                      ? 'text-red-600 border-red-600'
                      : 'text-gray-500 border-transparent hover:text-gray-700'
                  }`}
                >
                  Threats ({unreadThreatAlerts})
                </button>
              </div>
              
              <button
                onClick={() => setIsExpanded(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          
          {/* Content */}
          <div className="max-h-80 overflow-y-auto">
            {activeTab === 'notifications' && (
              <div>
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-gray-500">
                    <svg className="w-8 h-8 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5-5V9.5a4.5 4.5 0 00-9 0V12l-5 5h5a4.5 4.5 0 009 0z" />
                    </svg>
                    <p>No notifications yet</p>
                  </div>
                ) : (
                  <>
                    {/* Clear All Button */}
                    {notifications.length > 0 && (
                      <div className="p-3 border-b border-gray-100">
                        <button
                          onClick={clearNotifications}
                          className="text-sm text-gray-500 hover:text-gray-700"
                        >
                          Clear all notifications
                        </button>
                      </div>
                    )}
                    
                    {notifications.map((notification, index) => (
                      <div
                        key={notification.id}
                        onClick={() => markNotificationRead(notification.id)}
                        className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${
                          notification.isNew ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                        } ${getPriorityColor(notification.priority)}`}
                      >
                        <div className="flex items-start space-x-3">
                          <div className="text-lg">{getNotificationIcon(notification.type)}</div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {notification.title}
                              </p>
                              {notification.isNew && (
                                <span className="ml-2 inline-block w-2 h-2 bg-blue-500 rounded-full"></span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                              {notification.message}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">
                              {formatTime(notification.timestamp)}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>
            )}
            
            {activeTab === 'threats' && (
              <div>
                {threatAlerts.length === 0 ? (
                  <div className="p-6 text-center text-gray-500">
                    <svg className="w-8 h-8 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.031 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <p>No threats detected</p>
                    <p className="text-xs text-gray-400 mt-1">Your system is secure</p>
                  </div>
                ) : (
                  threatAlerts.map((alert, index) => (
                    <div
                      key={alert.id}
                      onClick={() => markThreatAlertRead(alert.id)}
                      className={`p-4 border-b border-gray-100 hover:bg-red-50 cursor-pointer transition-colors ${
                        alert.isNew ? 'bg-red-50 border-l-4 border-l-red-500' : ''
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="text-lg">🚨</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-red-900 truncate">
                              {alert.title || 'Threat Detected'}
                            </p>
                            {alert.isNew && (
                              <span className="ml-2 inline-block w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                            )}
                          </div>
                          <p className="text-sm text-red-700 mt-1 line-clamp-2">
                            {alert.message}
                          </p>
                          {alert.data && alert.data.risk_score && (
                            <div className="mt-2">
                              <div className="flex items-center space-x-2">
                                <span className="text-xs text-red-600">Risk Score:</span>
                                <div className="flex-1 bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-red-500 h-2 rounded-full"
                                    style={{ width: `${alert.data.risk_score}%` }}
                                  />
                                </div>
                                <span className="text-xs text-red-600 font-medium">
                                  {alert.data.risk_score.toFixed(1)}%
                                </span>
                              </div>
                            </div>
                          )}
                          <p className="text-xs text-gray-400 mt-1">
                            {formatTime(alert.timestamp)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
          
          {/* Footer */}
          <div className="border-t border-gray-200 px-4 py-2">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span className="flex items-center">
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`} />
                {isConnected ? 'Connected' : connectionStatus}
              </span>
              <span>Real-time updates</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RealTimeNotifications;