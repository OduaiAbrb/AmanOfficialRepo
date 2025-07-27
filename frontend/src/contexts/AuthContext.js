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

    // Set up axios defaults
    useEffect(() => {
        const token = localStorage.getItem('authToken');
        if (token) {
            setAuthToken(token);
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
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