import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState('');
  const { login, register, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (email, password) => {
    setError('');
    const result = await login(email, password);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
  };

  const handleRegister = async (name, email, password, organization) => {
    setError('');
    const result = await register(name, email, password, organization);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
  };

  const switchToRegister = () => {
    setIsLogin(false);
    setError('');
  };

  const switchToLogin = () => {
    setIsLogin(true);
    setError('');
  };

  if (isLogin) {
    return (
      <LoginForm
        onLogin={handleLogin}
        onSwitchToRegister={switchToRegister}
        isLoading={isLoading}
        error={error}
      />
    );
  }

  return (
    <RegisterForm
      onRegister={handleRegister}
      onSwitchToLogin={switchToLogin}
      isLoading={isLoading}
      error={error}
    />
  );
};

export default AuthPage;