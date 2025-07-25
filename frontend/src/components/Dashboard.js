import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import useWebSocket from '../hooks/useWebSocket';
import RealTimeNotifications from './RealTimeNotifications';
import axios from 'axios';

const Dashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentPage, setCurrentPage] = useState('overview');
  const [stats, setStats] = useState(null);
  const [recentEmails, setRecentEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // WebSocket connection for real-time updates
  const { 
    statistics: realtimeStats, 
    isConnected, 
    connectionStatus,
    requestStatistics 
  } = useWebSocket();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/auth');
      return;
    }
    
    // Fetch initial dashboard data
    fetchDashboardData();
    
    // Set current page based on URL
    const path = location.pathname.split('/')[2] || 'overview';
    setCurrentPage(path);
  }, [location, isAuthenticated, navigate]);

  // Update stats when real-time data is received
  useEffect(() => {
    if (realtimeStats) {
      setStats(prevStats => ({
        ...prevStats,
        phishing_emails_caught: realtimeStats.threats_blocked || 0,
        emails_scanned: realtimeStats.today_scans || 0,
        potential_phishing: Math.max(0, (realtimeStats.today_scans || 0) - (realtimeStats.threats_blocked || 0)),
        avg_risk_score: realtimeStats.avg_risk_score || 0
      }));
      
      // Update recent emails from real-time data
      if (realtimeStats.recent_scans) {
        setRecentEmails(realtimeStats.recent_scans);
      }
      
      setLoading(false);
    }
  }, [realtimeStats]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const [statsResponse, emailsResponse] = await Promise.all([
        axios.get(`${backendUrl}/api/dashboard/stats`),
        axios.get(`${backendUrl}/api/dashboard/recent-emails`)
      ]);
      
      setStats(statsResponse.data);
      setRecentEmails(emailsResponse.data.emails || []);
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        // Authentication failed, redirect to login
        logout();
        navigate('/auth');
        return;
      }
      
      setError('Failed to load dashboard data. Please try again.');
      
      // Fallback to mock data only if there's a network error
      if (!error.response) {
        setStats({
          phishing_caught: 23,
          safe_emails: 1247,
          potential_phishing: 12
        });
        setRecentEmails([
          {
            id: "1",
            subject: "Urgent: Verify Your Account Details",
            sender: "security@fake-bank.com",
            time: "2 hours ago",
            status: "phishing"
          },
          {
            id: "2", 
            subject: "Q4 Security Report - Review Required",
            sender: "security-team@techcorp.com",
            time: "4 hours ago",
            status: "safe"
          },
          {
            id: "3",
            subject: "System Maintenance Notification",
            sender: "admin@suspicious-domain.net",
            time: "6 hours ago", 
            status: "potential_phishing"
          }
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navigationItems = [
    { id: 'overview', icon: '📊', label: 'Dashboard Overview', path: '/dashboard' },
    { id: 'analysis', icon: '🔍', label: 'Threat Analysis', path: '/dashboard/analysis', comingSoon: true },
    { id: 'behavior', icon: '📈', label: 'Behavior Analysis', path: '/dashboard/behavior', comingSoon: true },
    { id: 'reports', icon: '📋', label: 'Security Reports', path: '/dashboard/reports', comingSoon: true },
    { id: 'intelligence', icon: '🧠', label: 'Threat Intelligence', path: '/dashboard/intelligence', comingSoon: true },
    { id: 'team', icon: '👥', label: 'Team Overview', path: '/dashboard/team', comingSoon: true },
    { id: 'profile', icon: '👤', label: 'User Profile', path: '/dashboard/profile' },
    { id: 'settings', icon: '⚙️', label: 'Settings', path: '/dashboard/settings' }
  ];

  const handleNavigation = (item) => {
    setCurrentPage(item.id);
    navigate(item.path);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'phishing': return 'bg-red-100 text-red-800 border-red-200';
      case 'safe': return 'bg-green-100 text-green-800 border-green-200';
      case 'potential_phishing': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'phishing': return '🚨';
      case 'safe': return '✅';
      case 'potential_phishing': return '⚠️';
      default: return '📧';
    }
  };

  const renderMainContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-gray-600">Loading dashboard data...</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-4xl">⚠️</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Error Loading Data</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button 
              onClick={fetchDashboardData}
              className="btn-primary"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    if (currentPage === 'profile') {
      return <ProfilePage user={user} />;
    }
    
    if (currentPage === 'settings') {
      return <SettingsPage />;
    }
    
    if (navigationItems.find(item => item.id === currentPage)?.comingSoon) {
      return <ComingSoonPage pageName={navigationItems.find(item => item.id === currentPage)?.label} />;
    }

    // Dashboard Overview
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
            <p className="text-gray-600 mt-1">Welcome back, {user?.name || 'User'}</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
              System Active
            </div>
            <div className="text-sm text-gray-500">
              Last scan: 2 minutes ago
            </div>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Phishing Emails Caught</p>
                <p className="text-3xl font-bold text-red-600">{stats?.phishing_caught || 0}</p>
              </div>
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-red-600 text-2xl">🚨</span>
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-gray-500">
              <span className="text-red-600 font-medium">↑ 12%</span>
              <span className="ml-2">from last week</span>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Safe Emails</p>
                <p className="text-3xl font-bold text-green-600">{stats?.safe_emails || 0}</p>
              </div>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 text-2xl">✅</span>
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-gray-500">
              <span className="text-green-600 font-medium">↑ 8%</span>
              <span className="ml-2">from last week</span>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Potential Phishing</p>
                <p className="text-3xl font-bold text-yellow-600">{stats?.potential_phishing || 0}</p>
              </div>
              <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-yellow-600 text-2xl">⚠️</span>
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-gray-500">
              <span className="text-yellow-600 font-medium">↓ 3%</span>
              <span className="ml-2">from last week</span>
            </div>
          </div>
        </div>

        {/* Recent Emails */}
        <div className="bg-white rounded-lg shadow-lg border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">Recent Email Scans</h2>
              <button className="text-primary hover:text-primary-dark font-medium">
                View All
              </button>
            </div>
          </div>
          <div className="divide-y divide-gray-200">
            {recentEmails.length > 0 ? (
              recentEmails.map((email) => (
                <div key={email.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl">{getStatusIcon(email.status)}</div>
                      <div>
                        <h3 className="font-medium text-gray-900">{email.subject}</h3>
                        <p className="text-sm text-gray-600">From: {email.sender}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(email.status)}`}>
                        {email.status.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="text-sm text-gray-500">{email.time}</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-12 text-center">
                <div className="text-6xl mb-4">📧</div>
                <p className="text-gray-500">No recent email scans available</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-white shadow-lg transition-all duration-300 flex flex-col`}>
        {/* Logo */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">A</span>
            </div>
            {sidebarOpen && (
              <h1 className="text-xl font-bold text-gray-900">
                <span className="text-primary">Aman</span>
              </h1>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navigationItems.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => handleNavigation(item)}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                    currentPage === item.id
                      ? 'bg-primary text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <span className="text-lg">{item.icon}</span>
                  {sidebarOpen && (
                    <>
                      <span className="font-medium">{item.label}</span>
                      {item.comingSoon && (
                        <span className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded">
                          Soon
                        </span>
                      )}
                    </>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* User Info */}
        {sidebarOpen && (
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                <span className="text-gray-600 font-medium">
                  {user?.name ? user.name.split(' ').map(n => n[0]).join('').toUpperCase() : 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.name || 'User'}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user?.organization || 'Organization'}
                </p>
              </div>
              <button
                onClick={handleLogout}
                className="text-gray-400 hover:text-red-600 transition-colors"
                title="Logout"
              >
                🚪
              </button>
            </div>
          </div>
        )}

        {/* Sidebar Toggle */}
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-full flex items-center justify-center p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
          >
            <span className="text-lg">{sidebarOpen ? '◀' : '▶'}</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8">
        {renderMainContent()}
      </div>

      {/* Call to Action - Bottom Right */}
      <div className="fixed bottom-6 right-6 z-50">
        <button className="bg-primary hover:bg-primary-dark text-white font-semibold px-6 py-3 rounded-full shadow-lg transition-all hover:shadow-xl">
          Quick Scan
        </button>
      </div>
    </div>
  );
};

// Profile Page Component
const ProfilePage = ({ user }) => {
  const { updateProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: user?.name || '',
    organization: user?.organization || ''
  });
  const [updating, setUpdating] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setUpdating(true);
    setMessage('');

    const result = await updateProfile(formData);
    
    if (result.success) {
      setMessage('Profile updated successfully!');
      setIsEditing(false);
    } else {
      setMessage(result.error || 'Failed to update profile');
    }
    
    setUpdating(false);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">User Profile</h1>
        <button
          onClick={() => setIsEditing(!isEditing)}
          className="btn-secondary"
        >
          {isEditing ? 'Cancel' : 'Edit Profile'}
        </button>
      </div>
      
      {message && (
        <div className={`p-4 rounded-md ${message.includes('success') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {message}
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-8">
        <div className="flex items-center space-x-6 mb-8">
          <div className="w-24 h-24 bg-gray-300 rounded-full flex items-center justify-center">
            <span className="text-gray-600 font-bold text-2xl">
              {user?.name ? user.name.split(' ').map(n => n[0]).join('').toUpperCase() : 'U'}
            </span>
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{user?.name || 'User'}</h2>
            <p className="text-gray-600">{user?.role || 'Security Analyst'}</p>
            <p className="text-sm text-gray-500 mt-1">
              Joined {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Recently'}
            </p>
          </div>
        </div>

        {isEditing ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>
              <div>
                <label htmlFor="organization" className="block text-sm font-medium text-gray-700 mb-2">
                  Organization
                </label>
                <input
                  type="text"
                  id="organization"
                  name="organization"
                  value={formData.organization}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={updating}
                className="btn-primary disabled:opacity-50"
              >
                {updating ? 'Updating...' : 'Save Changes'}
              </button>
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <p className="text-gray-900">{user?.email || 'No email'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Organization</label>
                  <p className="text-gray-900">{user?.organization || 'No organization'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Account Status</label>
                  <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
                    {user?.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Security Status</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Account Security</span>
                  <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Secured</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Email Monitoring</span>
                  <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Active</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Threat Alerts</span>
                  <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Enabled</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">Last Login</span>
                  <span className="text-sm text-gray-600">
                    {user?.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Settings Page Component
const SettingsPage = () => {
  const { getUserSettings, updateUserSettings } = useAuth();
  const [settings, setSettings] = useState({
    email_notifications: true,
    real_time_scanning: true,
    block_suspicious_links: false,
    scan_attachments: true,
    share_threat_intelligence: true
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    const result = await getUserSettings();
    
    if (result.success) {
      setSettings(result.settings);
    } else {
      setMessage('Failed to load settings');
    }
    
    setLoading(false);
  };

  const handleSettingChange = async (key, value) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    
    setSaving(true);
    setMessage('');
    
    const result = await updateUserSettings(newSettings);
    
    if (result.success) {
      setMessage('Settings saved successfully!');
      setTimeout(() => setMessage(''), 3000);
    } else {
      setMessage(result.error || 'Failed to save settings');
      // Revert the setting
      setSettings(settings);
    }
    
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        {saving && (
          <div className="flex items-center text-sm text-gray-600">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2"></div>
            Saving...
          </div>
        )}
      </div>

      {message && (
        <div className={`p-4 rounded-md ${message.includes('success') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Security Settings */}
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Security Settings</h2>
          <div className="space-y-4">
            {[
              { 
                key: 'real_time_scanning', 
                label: 'Real-time Email Scanning', 
                desc: 'Automatically scan emails as they arrive' 
              },
              { 
                key: 'block_suspicious_links', 
                label: 'Block Suspicious Links', 
                desc: 'Automatically block access to dangerous links' 
              },
              { 
                key: 'scan_attachments', 
                label: 'Scan Email Attachments', 
                desc: 'Check attachments for malware and threats' 
              }
            ].map((item) => (
              <div key={item.key} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-700">{item.label}</p>
                  <p className="text-xs text-gray-500">{item.desc}</p>
                </div>
                <button
                  onClick={() => handleSettingChange(item.key, !settings[item.key])}
                  disabled={saving}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-50 ${
                    settings[item.key] ? 'bg-primary' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings[item.key] ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Notification Settings</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Email Notifications</p>
                <p className="text-xs text-gray-500">Receive security alerts via email</p>
              </div>
              <button
                onClick={() => handleSettingChange('email_notifications', !settings.email_notifications)}
                disabled={saving}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-50 ${
                  settings.email_notifications ? 'bg-primary' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.email_notifications ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Privacy Settings */}
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Privacy Settings</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Share Threat Intelligence</p>
                <p className="text-xs text-gray-500">Help improve security by sharing anonymized threat data</p>
              </div>
              <button
                onClick={() => handleSettingChange('share_threat_intelligence', !settings.share_threat_intelligence)}
                disabled={saving}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-50 ${
                  settings.share_threat_intelligence ? 'bg-primary' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.share_threat_intelligence ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Account Settings */}
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Account Settings</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Change Password
              </label>
              <button className="btn-secondary text-sm">Update Password</button>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Account Security
              </label>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Two-factor authentication</span>
                <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Recommended</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Coming Soon Page Component
const ComingSoonPage = ({ pageName }) => (
  <div className="flex items-center justify-center h-96">
    <div className="text-center">
      <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <span className="text-4xl">🚧</span>
      </div>
      <h1 className="text-3xl font-bold text-gray-900 mb-4">{pageName}</h1>
      <p className="text-xl text-gray-600 mb-8">
        This feature is currently under development and will be available soon.
      </p>
      <div className="bg-primary text-white px-6 py-3 rounded-lg font-semibold inline-block">
        Coming Soon ✨
      </div>
    </div>
  </div>
);

export default Dashboard;