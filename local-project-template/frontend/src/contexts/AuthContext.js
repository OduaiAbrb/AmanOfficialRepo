import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [authToken, setAuthToken] = useState(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Initialize auth state from localStorage
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    const userData = localStorage.getItem('userData');

    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setAuthToken(token);
        setUser(parsedUser);
        setIsAuthenticated(true);
        
        // Set default axios header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
        // Verify token is still valid
        verifyToken(token);
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        logout();
      }
    }
    setIsLoading(false);
  }, []);

  // Verify token validity
  const verifyToken = async (token) => {
    try {
      const response = await axios.get(`${backendUrl}/api/user/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.status === 200) {
        setUser(response.data);
        localStorage.setItem('userData', JSON.stringify(response.data));
      }
    } catch (error) {
      console.error('Token verification failed:', error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        logout(); // Token is invalid, logout user
      }
    }
  };

  // Login function
  const login = async (email, password) => {
    try {
      setIsLoading(true);
      
      const response = await axios.post(`${backendUrl}/api/auth/login`, {
        email,
        password
      });

      if (response.status === 200 && response.data.access_token) {
        const { access_token, refresh_token } = response.data;
        
        // Store tokens
        localStorage.setItem('authToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);
        
        // Set axios default header
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        // Get user profile
        const profileResponse = await axios.get(`${backendUrl}/api/user/profile`);
        const userData = profileResponse.data;
        
        // Update state
        setAuthToken(access_token);
        setUser(userData);
        setIsAuthenticated(true);
        
        // Store user data
        localStorage.setItem('userData', JSON.stringify(userData));
        localStorage.setItem('userEmail', userData.email);
        
        // Try to authenticate browser extension
        setTimeout(() => {
          if (window.amanExtensionAuth) {
            window.amanExtensionAuth.sendAuthToExtension(access_token, userData.email);
          }
        }, 500);
        
        return { success: true, user: userData };
      }
    } catch (error) {
      console.error('Login error:', error);
      let errorMessage = 'Login failed. Please try again.';
      
      if (error.response?.status === 401) {
        errorMessage = 'Invalid email or password.';
      } else if (error.response?.status === 423) {
        errorMessage = 'Account temporarily locked. Please try again later.';
      } else if (error.response?.status === 429) {
        errorMessage = 'Too many login attempts. Please try again later.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  };

  // Register function
  const register = async (name, email, password, organization) => {
    try {
      setIsLoading(true);
      
      const response = await axios.post(`${backendUrl}/api/auth/register`, {
        name,
        email,
        password,
        organization
      });

      if (response.status === 200 && response.data.success) {
        // After successful registration, automatically log in
        return await login(email, password);
      }
    } catch (error) {
      console.error('Registration error:', error);
      let errorMessage = 'Registration failed. Please try again.';
      
      if (error.response?.status === 400) {
        errorMessage = error.response.data.detail || 'Invalid registration data.';
      } else if (error.response?.status === 429) {
        errorMessage = 'Too many registration attempts. Please try again later.';
      }
      
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    // Clear tokens and user data
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userData');
    localStorage.removeItem('userEmail');
    
    // Clear axios header
    delete axios.defaults.headers.common['Authorization'];
    
    // Update state
    setAuthToken(null);
    setUser(null);
    setIsAuthenticated(false);
  };

  // Refresh token function
  const refreshAuthToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        logout();
        return false;
      }

      const response = await axios.post(`${backendUrl}/api/auth/refresh`, {
        refresh_token: refreshToken
      });

      if (response.status === 200 && response.data.access_token) {
        const { access_token, refresh_token } = response.data;
        
        // Update tokens
        localStorage.setItem('authToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);
        
        // Set axios header
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        setAuthToken(access_token);
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      return false;
    }
  };

  // Update user profile
  const updateProfile = async (updateData) => {
    try {
      const response = await axios.put(`${backendUrl}/api/user/profile`, updateData);
      
      if (response.status === 200) {
        // Get updated profile
        const profileResponse = await axios.get(`${backendUrl}/api/user/profile`);
        const updatedUser = profileResponse.data;
        
        setUser(updatedUser);
        localStorage.setItem('userData', JSON.stringify(updatedUser));
        
        return { success: true, user: updatedUser };
      }
    } catch (error) {
      console.error('Profile update error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Profile update failed' 
      };
    }
  };

  // Get user settings
  const getUserSettings = async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/user/settings`);
      return { success: true, settings: response.data };
    } catch (error) {
      console.error('Get settings error:', error);
      return { success: false, error: 'Failed to load settings' };
    }
  };

  // Update user settings
  const updateUserSettings = async (settings) => {
    try {
      const response = await axios.put(`${backendUrl}/api/user/settings`, settings);
      
      if (response.status === 200) {
        return { success: true, message: 'Settings updated successfully' };
      }
    } catch (error) {
      console.error('Update settings error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Settings update failed' 
      };
    }
  };

  // Set up axios interceptor for automatic token refresh
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          const refreshed = await refreshAuthToken();
          if (refreshed) {
            // Retry the original request with new token
            return axios(originalRequest);
          }
        }
        
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, []);

  const value = {
    user,
    isAuthenticated,
    isLoading,
    authToken,
    login,
    register,
    logout,
    updateProfile,
    getUserSettings,
    updateUserSettings,
    refreshAuthToken
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};