import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

/**
 * Custom hook for WebSocket connection with automatic reconnection
 * Handles real-time dashboard updates, notifications, and threat alerts
 */
const useWebSocket = (options = {}) => {
  const { user, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [statistics, setStatistics] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [threatAlerts, setThreatAlerts] = useState([]);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = options.maxReconnectAttempts || 5;
  const reconnectInterval = options.reconnectInterval || 3000;
  
  // Get WebSocket URL from environment
  const getWebSocketUrl = useCallback(() => {
    const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
    // Remove /api suffix and convert to WebSocket URL
    const baseUrl = backendUrl.replace(/\/api$/, '');
    const wsUrl = baseUrl.replace(/^https?/, 'ws');
    return `${wsUrl}/ws/${user?.id}`;
  }, [user?.id]);
  
  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!isAuthenticated || !user?.id) {
      console.log('WebSocket: Not authenticated or no user ID');
      return;
    }
    
    try {
      const wsUrl = getWebSocketUrl();
      console.log('WebSocket: Connecting to', wsUrl);
      
      setConnectionStatus('connecting');
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket: Connected successfully');
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        
        // Subscribe to updates
        sendMessage({
          type: 'subscribe',
          subscriptions: ['all', 'statistics', 'notifications', 'threats']
        });
        
        // Request initial statistics
        sendMessage({
          type: 'request_stats'
        });
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);
          handleMessage(message);
        } catch (error) {
          console.error('WebSocket: Failed to parse message', error);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket: Connection error', error);
        setConnectionStatus('error');
      };
      
      wsRef.current.onclose = (event) => {
        console.log('WebSocket: Connection closed', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        // Attempt to reconnect if not intentionally closed
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          scheduleReconnect();
        }
      };
      
    } catch (error) {
      console.error('WebSocket: Connection failed', error);
      setConnectionStatus('error');
      scheduleReconnect();
    }
  }, [isAuthenticated, user?.id, getWebSocketUrl, maxReconnectAttempts]);
  
  // Schedule reconnection attempt
  const scheduleReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current < maxReconnectAttempts) {
      reconnectAttemptsRef.current++;
      const delay = reconnectInterval * Math.pow(1.5, reconnectAttemptsRef.current - 1);
      
      console.log(`WebSocket: Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);
      setConnectionStatus('reconnecting');
      
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, delay);
    } else {
      console.log('WebSocket: Max reconnection attempts reached');
      setConnectionStatus('failed');
    }
  }, [connect, maxReconnectAttempts, reconnectInterval]);
  
  // Handle incoming messages
  const handleMessage = useCallback((message) => {
    switch (message.type) {
      case 'connection_established':
        console.log('WebSocket: Connection established', message.connection_id);
        break;
        
      case 'statistics_update':
        setStatistics(message.data);
        console.log('WebSocket: Statistics updated', message.data);
        break;
        
      case 'notification':
        const notification = {
          ...message.notification,
          id: message.notification.id || Date.now(),
          timestamp: new Date(message.notification.timestamp),
          isNew: true
        };
        
        setNotifications(prev => [notification, ...prev.slice(0, 49)]); // Keep last 50
        
        // Show browser notification if permission granted
        if (Notification.permission === 'granted' && notification.priority === 'high') {
          new Notification(notification.title, {
            body: notification.message,
            icon: '/logo192.png',
            tag: `aman-threat-${notification.id}`
          });
        }
        break;
        
      case 'threat_detected':
        const threatAlert = {
          ...message,
          id: message.id || Date.now(),
          timestamp: new Date(),
          isNew: true
        };
        
        setThreatAlerts(prev => [threatAlert, ...prev.slice(0, 19)]); // Keep last 20
        
        // Show urgent browser notification
        if (Notification.permission === 'granted') {
          new Notification('🚨 Threat Detected!', {
            body: message.message || 'High-risk phishing attempt detected',
            icon: '/logo192.png',
            tag: 'aman-threat-alert',
            requireInteraction: true
          });
        }
        break;
        
      case 'scan_completed':
        console.log('WebSocket: Scan completed', message.scan_result);
        // Trigger statistics update
        sendMessage({ type: 'request_stats' });
        break;
        
      case 'threat_feed_update':
        console.log('WebSocket: Threat feed update', message.data);
        // Add to threat alerts if relevant
        if (message.data.severity === 'high') {
          const feedAlert = {
            id: Date.now(),
            type: 'threat_feed',
            title: 'Threat Intelligence Update',
            message: message.data.description,
            timestamp: new Date(),
            isNew: true
          };
          setThreatAlerts(prev => [feedAlert, ...prev.slice(0, 19)]);
        }
        break;
        
      case 'system_alert':
        console.log('WebSocket: System alert', message.data);
        const systemNotification = {
          id: Date.now(),
          type: 'system_alert',
          title: 'System Alert',
          message: message.data.message,
          timestamp: new Date(),
          priority: message.data.priority,
          isNew: true
        };
        setNotifications(prev => [systemNotification, ...prev.slice(0, 49)]);
        break;
        
      case 'pong':
        // Handle ping/pong for connection health
        break;
        
      case 'error':
        console.error('WebSocket: Server error', message.message);
        break;
        
      default:
        console.log('WebSocket: Unknown message type', message);
    }
  }, []);
  
  // Send message to WebSocket
  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('WebSocket: Failed to send message', error);
        return false;
      }
    }
    return false;
  }, []);
  
  // Request fresh statistics
  const requestStatistics = useCallback(() => {
    return sendMessage({ type: 'request_stats' });
  }, [sendMessage]);
  
  // Mark notification as read
  const markNotificationRead = useCallback((notificationId) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === notificationId ? { ...notif, isNew: false } : notif
      )
    );
  }, []);
  
  // Clear all notifications
  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);
  
  // Mark threat alert as read
  const markThreatAlertRead = useCallback((alertId) => {
    setThreatAlerts(prev => 
      prev.map(alert => 
        alert.id === alertId ? { ...alert, isNew: false } : alert
      )
    );
  }, []);
  
  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
    reconnectAttemptsRef.current = 0;
  }, []);
  
  // Request browser notification permission
  const requestNotificationPermission = useCallback(async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return Notification.permission === 'granted';
  }, []);
  
  // Connection effect
  useEffect(() => {
    if (isAuthenticated && user?.id) {
      connect();
    } else {
      disconnect();
    }
    
    return () => {
      disconnect();
    };
  }, [isAuthenticated, user?.id, connect, disconnect]);
  
  // Ping interval for connection health
  useEffect(() => {
    if (!isConnected) return;
    
    const pingInterval = setInterval(() => {
      sendMessage({ type: 'ping' });
    }, 30000); // Ping every 30 seconds
    
    return () => clearInterval(pingInterval);
  }, [isConnected, sendMessage]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);
  
  return {
    // Connection state
    isConnected,
    connectionStatus,
    
    // Data
    statistics,
    notifications,
    threatAlerts,
    lastMessage,
    
    // Actions
    sendMessage,
    requestStatistics,
    requestNotificationPermission,
    
    // Notification management
    markNotificationRead,
    clearNotifications,
    markThreatAlertRead,
    
    // Connection control
    connect,
    disconnect,
    
    // Derived state
    unreadNotifications: notifications.filter(n => n.isNew).length,
    unreadThreatAlerts: threatAlerts.filter(a => a.isNew).length,
    hasNewData: notifications.some(n => n.isNew) || threatAlerts.some(a => a.isNew)
  };
};

export default useWebSocket;