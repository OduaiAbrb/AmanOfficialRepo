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

    // Send auth data to extension
    const sendAuthToExtension = (authData) => {
        try {
            window.postMessage({ type: 'AUTH_SUCCESS', data: authData }, '*');
        } catch (error) {
            console.error('❌ Failed to send auth to extension:', error);
        }
    };

    const logout = async () => {
        try {
            if (authToken) {
                try {
                    await axios.post(`${API_BASE_URL}/auth/logout`);
                } catch (error) {
                    console.warn('Logout endpoint failed:', error);
                }
            }
            localStorage.removeItem('authToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            delete axios.defaults.headers.common['Authorization'];
            setAuthToken(null);
            setUser(null);
            console.log('✅ Logged out successfully');
        } catch (error) {
            console.error('❌ Logout error:', error);
        }
    };

    const refreshToken = async () => {
        try {
            const storedRefreshToken = localStorage.getItem('refreshToken');
            if (!storedRefreshToken) throw new Error('No refresh token available');

            const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                refresh_token: storedRefreshToken,
            });

            if (response.data.access_token) {
                localStorage.setItem('authToken', response.data.access_token);
                setAuthToken(response.data.access_token);
                axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
                return response.data.access_token;
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
                const newToken = await refreshToken();
                if (newToken) {
                    try {
                        const retry = await axios.get(`${API_BASE_URL}/user/profile`);
                        return retry.data;
                    } catch (err) {
                        logout();
                        return null;
                    }
                } else {
                    logout();
                    return null;
                }
            }
            return null;
        }
    };

    const login = async (email, password) => {
        try {
            const response = await axios.post(`${API_BASE_URL}/auth/login`, { email, password });

            if (response.data.success) {
                const { access_token, refresh_token, user: userData } = response.data;
                localStorage.setItem('authToken', access_token);
                localStorage.setItem('refreshToken', refresh_token);
                localStorage.setItem('user', JSON.stringify(userData));

                setAuthToken(access_token);
                setUser(userData);

                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

                sendAuthToExtension({ token: access_token, email: userData.email, name: userData.name });

                return { success: true, user: userData };
            }
        } catch (error) {
            const message = error.response?.data?.detail || 'Login failed. Please try again.';
            return { success: false, error: message };
        }
    };

    const register = async (name, email, password, organization) => {
        try {
            const response = await axios.post(`${API_BASE_URL}/auth/register`, {
                name, email, password, organization,
            });

            if (response.status === 200 && response.data.success) {
                return await login(email, password);
            }
        } catch (error) {
            const detail = error.response?.data?.detail;
            let errorMessage = 'Registration failed. Please try again.';
            if (typeof detail === 'string') errorMessage = detail;
            else if (Array.isArray(detail)) errorMessage = detail.map(e => e.msg).join(', ');
            else if (typeof detail === 'object') errorMessage = detail?.msg || detail?.type;
            return { success: false, error: errorMessage };
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
                    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
                    const verifiedUser = await getCurrentUser();
                    if (verifiedUser) {
                        setUser(verifiedUser);
                        sendAuthToExtension({
                            token: token,
                            email: verifiedUser.email,
                            name: verifiedUser.name
                        });
                    } else {
                        logout();
                    }
                } catch (error) {
                    logout();
                }
            }
            setLoading(false);
        };

        checkAuthStatus();
    }, []);

    // Axios response interceptor to refresh tokens automatically
    useEffect(() => {
        const interceptor = axios.interceptors.response.use(
            (response) => response,
            async (error) => {
                if (error.response?.status === 401 && authToken) {
                    const newToken = await refreshToken();
                    if (newToken) {
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
        isAuthenticated: !!user && !!authToken,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
