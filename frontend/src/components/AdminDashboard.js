import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import useWebSocket from '../hooks/useWebSocket';
import axios from 'axios';

const AdminDashboard = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const [currentPage, setCurrentPage] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // WebSocket for real-time updates
  const { isConnected, requestStatistics } = useWebSocket();

  useEffect(() => {
    // Check if user has admin access
    if (!isAuthenticated || !user || !['admin', 'super_admin'].includes(user.role)) {
      window.location.href = '/dashboard';
      return;
    }
    setLoading(false);
  }, [isAuthenticated, user]);

  const renderContent = () => {
    switch (currentPage) {
      case 'overview':
        return <AdminOverview />;
      case 'users':
        return <UserManagement />;
      case 'threats':
        return <ThreatManagement />;
      case 'system':
        return <SystemMonitoring />;
      case 'audit':
        return user?.role === 'super_admin' ? <AuditLog /> : <AccessDenied />;
      default:
        return <AdminOverview />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Admin Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">A</span>
                </div>
                <h1 className="text-xl font-bold text-gray-900">Admin Panel</h1>
              </div>
              
              {/* Real-time Status */}
              <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${
                isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                <div className={`w-1.5 h-1.5 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`} />
                <span>{isConnected ? 'Live' : 'Offline'}</span>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                {user?.name} ({user?.role})
              </div>
              <button
                onClick={logout}
                className="text-gray-500 hover:text-red-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white shadow-sm min-h-screen">
          <nav className="mt-8">
            <div className="px-4 space-y-1">
              {[
                { id: 'overview', label: 'Dashboard', icon: '📊', access: ['admin', 'super_admin'] },
                { id: 'users', label: 'User Management', icon: '👥', access: ['admin', 'super_admin'] },
                { id: 'threats', label: 'Threat Analysis', icon: '🛡️', access: ['admin', 'super_admin'] },
                { id: 'system', label: 'System Monitor', icon: '⚙️', access: ['admin', 'super_admin'] },
                { id: 'audit', label: 'Audit Logs', icon: '📋', access: ['super_admin'] }
              ].map((item) => (
                item.access.includes(user?.role) && (
                  <button
                    key={item.id}
                    onClick={() => setCurrentPage(item.id)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      currentPage === item.id
                        ? 'bg-green-100 text-green-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <span className="mr-3 text-lg">{item.icon}</span>
                    {item.label}
                  </button>
                )
              ))}
            </div>
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-8">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

// Admin Overview Component
const AdminOverview = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAdminStats();
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchAdminStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAdminStats = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await axios.get(`${backendUrl}/api/admin/dashboard/stats`);
      setStats(response.data.statistics);
      setError('');
    } catch (error) {
      console.error('Error fetching admin stats:', error);
      setError('Failed to load admin statistics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading admin statistics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">⚠️ {error}</div>
        <button 
          onClick={fetchAdminStats}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Users',
      value: stats?.total_users || 0,
      subtitle: `${stats?.active_users || 0} active`,
      icon: '👥',
      color: 'blue'
    },
    {
      title: 'Organizations',
      value: stats?.total_organizations || 0,
      subtitle: `${stats?.active_organizations || 0} active`,
      icon: '🏢',
      color: 'indigo'
    },
    {
      title: 'Today\'s Scans',
      value: stats?.today_scans || 0,
      subtitle: `${stats?.today_threats || 0} threats found`,
      icon: '🔍',
      color: 'green'
    },
    {
      title: 'Threats Blocked',
      value: stats?.total_threats_blocked || 0,
      subtitle: `Avg risk: ${stats?.avg_risk_score || 0}%`,
      icon: '🛡️',
      color: 'red'
    },
    {
      title: 'AI Usage Cost',
      value: `$${(stats?.ai_usage_cost || 0).toFixed(4)}`,
      subtitle: 'Today',
      icon: '🤖',
      color: 'purple'
    },
    {
      title: 'Cache Hit Rate',
      value: `${((stats?.cache_hit_rate || 0) * 100).toFixed(1)}%`,
      subtitle: 'Performance',
      icon: '⚡',
      color: 'yellow'
    }
  ];

  const getColorClasses = (color) => {
    const colors = {
      blue: 'bg-blue-500 text-blue-600 bg-blue-50',
      indigo: 'bg-indigo-500 text-indigo-600 bg-indigo-50',
      green: 'bg-green-500 text-green-600 bg-green-50',
      red: 'bg-red-500 text-red-600 bg-red-50',
      purple: 'bg-purple-500 text-purple-600 bg-purple-50',
      yellow: 'bg-yellow-500 text-yellow-600 bg-yellow-50'
    };
    return colors[color] || colors.blue;
  };

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Admin Dashboard</h2>
        <p className="text-gray-600">System overview and key metrics</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {statCards.map((stat, index) => {
          const colorClasses = getColorClasses(stat.color).split(' ');
          return (
            <div key={index} className="bg-white rounded-lg shadow-sm p-6 border">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${colorClasses[2]} mr-4`}>
                  <span className="text-2xl">{stat.icon}</span>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                  <div className="text-sm text-gray-500">{stat.title}</div>
                  <div className={`text-xs ${colorClasses[1]}`}>{stat.subtitle}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm p-6 border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'View Users', icon: '👥', action: 'users' },
            { label: 'Analyze Threats', icon: '🛡️', action: 'threats' },
            { label: 'System Health', icon: '⚙️', action: 'system' },
            { label: 'Audit Logs', icon: '📋', action: 'audit' }
          ].map((action, index) => (
            <button
              key={index}
              className="flex items-center justify-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <span className="text-2xl mr-2">{action.icon}</span>
              <span className="font-medium">{action.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// User Management Component  
const UserManagement = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">User Management</h2>
      <div className="bg-white rounded-lg shadow-sm p-6 border text-center">
        <div className="text-6xl mb-4">👥</div>
        <h3 className="text-xl font-semibold mb-2">User Management Interface</h3>
        <p className="text-gray-600 mb-4">Comprehensive user administration coming soon</p>
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-sm text-blue-800">
            Features: User search, role management, status updates, usage analytics
          </p>
        </div>
      </div>
    </div>
  );
};

// Threat Management Component
const ThreatManagement = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Threat Analysis</h2>
      <div className="bg-white rounded-lg shadow-sm p-6 border text-center">
        <div className="text-6xl mb-4">🛡️</div>
        <h3 className="text-xl font-semibold mb-2">Threat Analytics Dashboard</h3>
        <p className="text-gray-600 mb-4">Advanced threat monitoring and analysis</p>
        <div className="bg-red-50 p-4 rounded-lg">
          <p className="text-sm text-red-800">
            Features: Threat timeline, source analysis, risk trends, incident management
          </p>
        </div>
      </div>
    </div>
  );
};

// System Monitoring Component
const SystemMonitoring = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">System Monitoring</h2>
      <div className="bg-white rounded-lg shadow-sm p-6 border text-center">
        <div className="text-6xl mb-4">⚙️</div>
        <h3 className="text-xl font-semibold mb-2">System Health Monitor</h3>
        <p className="text-gray-600 mb-4">Real-time system performance and health metrics</p>
        <div className="bg-green-50 p-4 rounded-lg">
          <p className="text-sm text-green-800">
            Features: API performance, error rates, database stats, WebSocket monitoring
          </p>
        </div>
      </div>
    </div>
  );
};

// Audit Log Component
const AuditLog = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Audit Logs</h2>
      <div className="bg-white rounded-lg shadow-sm p-6 border text-center">
        <div className="text-6xl mb-4">📋</div>
        <h3 className="text-xl font-semibold mb-2">Admin Action Audit Trail</h3>
        <p className="text-gray-600 mb-4">Complete log of all administrative actions</p>
        <div className="bg-purple-50 p-4 rounded-lg">
          <p className="text-sm text-purple-800">
            Features: Action history, user tracking, timestamp logs, compliance reports
          </p>
        </div>
      </div>
    </div>
  );
};

// Access Denied Component
const AccessDenied = () => {
  return (
    <div className="text-center py-12">
      <div className="text-6xl mb-4">🚫</div>
      <h3 className="text-xl font-semibold mb-2 text-red-600">Access Denied</h3>
      <p className="text-gray-600">You don't have permission to access this section.</p>
    </div>
  );
};

export default AdminDashboard;