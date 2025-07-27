import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [authToken, setAuthToken] = useState(null);

    const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';


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
        // Handle FastAPI validation errors that might be objects
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          // Handle validation error array
          errorMessage = error.response.data.detail.map(err => err.msg || err.type || 'Validation error').join(', ');
        } else if (typeof error.response.data.detail === 'object') {
          // Handle validation error object
          errorMessage = error.response.data.detail.msg || error.response.data.detail.type || 'Invalid input';
        }
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
        // Handle FastAPI validation errors that might be objects
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          // Handle validation error array
          errorMessage = error.response.data.detail.map(err => err.msg || err.type || 'Validation error').join(', ');
        } else if (typeof error.response.data.detail === 'object') {
          // Handle validation error object  
          errorMessage = error.response.data.detail.msg || error.response.data.detail.type || 'Invalid registration data';
        } else {
          errorMessage = 'Invalid registration data.';
        }
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
        error: (() => {
          const detail = error.response?.data?.detail;
          if (typeof detail === 'string') {
            return detail;
          } else if (Array.isArray(detail)) {
            return detail.map(err => err.msg || err.type || 'Validation error').join(', ');
          } else if (typeof detail === 'object' && detail) {
            return detail.msg || detail.type || 'Profile update failed';
          }
          return 'Profile update failed';
        })()
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
    }, []);

    // Update axios defaults when token changes
    useEffect(() => {
        if (authToken) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
        } else {
            delete axios.defaults.headers.common['Authorization'];
        }
    }, [authToken]);

    const login = async (email, password) => {
        try {
            console.log('🔐 Attempting login...');
            
            const response = await axios.post(`${API_BASE_URL}/auth/login`, {
                email,
                password
            });

            if (response.data.success) {
                const { access_token, refresh_token, user: userData } = response.data;
                
                console.log('✅ Login successful');
                
                // Store tokens
                localStorage.setItem('authToken', access_token);
                localStorage.setItem('refreshToken', refresh_token);
                localStorage.setItem('user', JSON.stringify(userData));
                
                // Update state
                setAuthToken(access_token);
                setUser(userData);
                
                // Set axios default header
                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
                
                // Send auth data to extension
                sendAuthToExtension({
                    token: access_token,
                    email: userData.email,
                    name: userData.name
                });
                
                return { success: true, user: userData };
            }
        } catch (error) {
            console.error('❌ Login error:', error);
            const message = error.response?.data?.detail || 'Login failed. Please try again.';
            return { success: false, error: message };
        }
    };

    const register = async (userData) => {
        try {
            console.log('📝 Attempting registration...');
            
            const response = await axios.post(`${API_BASE_URL}/auth/register`, userData);
            
            if (response.data.success) {
                console.log('✅ Registration successful, logging in...');
                // After successful registration, automatically log in
                const loginResult = await login(userData.email, userData.password);
                return loginResult;
            }
        } catch (error) {
            console.error('❌ Registration error:', error);
            const message = error.response?.data?.detail || 'Registration failed. Please try again.';
            return { success: false, error: message };
        }
    };

    const logout = async () => {
        try {
            // Call logout endpoint to invalidate token on server
            if (authToken) {
                try {
                    await axios.post(`${API_BASE_URL}/auth/logout`);
                } catch (error) {
                    console.warn('Logout endpoint failed:', error);
                    // Continue with local logout even if server logout fails
                }
            }
            
            // Clear local storage
            localStorage.removeItem('authToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            
            // Clear state
            setAuthToken(null);
            setUser(null);
            
            // Clear axios default header
            delete axios.defaults.headers.common['Authorization'];
            
            console.log('✅ Logged out successfully');
            
        } catch (error) {
            console.error('❌ Logout error:', error);
        }
    };

    const refreshToken = async () => {
        try {
            const storedRefreshToken = localStorage.getItem('refreshToken');
            if (!storedRefreshToken) {
                throw new Error('No refresh token available');
            }

            console.log('🔄 Refreshing token...');

            const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                refresh_token: storedRefreshToken
            });

            if (response.data.success) {
                const { access_token } = response.data;
                
                localStorage.setItem('authToken', access_token);
                setAuthToken(access_token);
                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
                
                console.log('✅ Token refreshed successfully');
                return access_token;
            }
        } catch (error) {
            console.error('❌ Token refresh failed:', error);
            logout();
            return null;
        }
    };

    const getCurrentUser = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/user/profile`);
            return response.data;
        } catch (error) {
            if (error.response?.status === 401) {
                console.log('🔄 Token expired, attempting refresh...');
                // Try to refresh token
                const newToken = await refreshToken();
                if (newToken) {
                    // Retry the request
                    try {
                        const response = await axios.get(`${API_BASE_URL}/user/profile`);
                        return response.data;
                    } catch (retryError) {
                        console.error('❌ Retry failed:', retryError);
                        logout();
                        return null;
                    }
                } else {
                    logout();
                    return null;
                }
            }
            console.error('❌ Get current user error:', error);
            return null;
        }
    };

    const sendAuthToExtension = (authData) => {
        try {
            // Send auth data via postMessage for extension
            window.postMessage({
                type: 'AUTH_SUCCESS',
                data: authData
            }, '*');
            
            console.log('📤 Auth data sent to extension');
        } catch (error) {
            console.error('❌ Failed to send auth to extension:', error);
        }
    };

    // Check authentication status on mount
    useEffect(() => {
        const checkAuthStatus = async () => {
            const token = localStorage.getItem('authToken');
            const storedUser = localStorage.getItem('user');
            
            if (token && storedUser) {
                try {
                    setAuthToken(token);
                    const userData = JSON.parse(storedUser);
                    setUser(userData);
                    
                    console.log('🔍 Verifying stored token...');
                    
                    // Verify token is still valid
                    const currentUser = await getCurrentUser();
                    if (currentUser) {
                        setUser(currentUser);
                        // Send auth to extension for existing sessions
                        sendAuthToExtension({
                            token: token,
                            email: currentUser.email,
                            name: currentUser.name
                        });
                        console.log('✅ Token verified, user authenticated');
                    } else {
                        console.log('❌ Token verification failed');
                    }
                } catch (error) {
                    console.error('❌ Auth check failed:', error);
                    logout();
                }
            } else {
                console.log('ℹ️ No stored authentication found');
            }
            
            setLoading(false);
        };

        checkAuthStatus();
    }, []);

    // Axios response interceptor for handling 401 errors
    useEffect(() => {
        const interceptor = axios.interceptors.response.use(
            (response) => response,
            async (error) => {
                if (error.response?.status === 401 && authToken) {
                    console.log('🔄 API returned 401, attempting token refresh...');
                    // Try to refresh token
                    const newToken = await refreshToken();
                    if (newToken) {
                        // Retry the original request
                        error.config.headers['Authorization'] = `Bearer ${newToken}`;
                        return axios.request(error.config);
                    }
                }
                return Promise.reject(error);
            }
        );

        return () => {
            axios.interceptors.response.eject(interceptor);
        };
    }, [authToken]);

    const value = {
        user,
        authToken,
        loading,
        login,
        register,
        logout,
        refreshToken,
        getCurrentUser,
        isAuthenticated: !!user && !!authToken
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;