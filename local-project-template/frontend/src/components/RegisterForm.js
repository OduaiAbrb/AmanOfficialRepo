import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const RegisterForm = ({ onRegister, onSwitchToLogin, isLoading, error }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    organization: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState('');
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });

    // Check password strength
    if (name === 'password') {
      checkPasswordStrength(value);
    }
  };

  const checkPasswordStrength = (password) => {
    if (password.length === 0) {
      setPasswordStrength('');
      return;
    }

    const hasLower = /[a-z]/.test(password);
    const hasUpper = /[A-Z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSpecial = /[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(password);
    const isLongEnough = password.length >= 8;

    const score = [hasLower, hasUpper, hasNumber, hasSpecial, isLongEnough].filter(Boolean).length;

    if (score < 3) {
      setPasswordStrength('weak');
    } else if (score < 5) {
      setPasswordStrength('medium');
    } else {
      setPasswordStrength('strong');
    }
  };

  const getPasswordStrengthColor = () => {
    switch (passwordStrength) {
      case 'weak': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'strong': return 'text-green-600 bg-green-50 border-green-200';
      default: return '';
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validation
    if (formData.password !== formData.confirmPassword) {
      return;
    }
    
    if (!agreedToTerms) {
      return;
    }

    onRegister(formData.name, formData.email, formData.password, formData.organization);
  };

  const passwordsMatch = formData.password === formData.confirmPassword || formData.confirmPassword === '';

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Logo */}
        <div className="flex justify-center">
          <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">A</span>
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
          Join <span className="text-primary">Aman</span> Security
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Create your account and start protecting your organization
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-lg sm:rounded-lg sm:px-10 border border-gray-200">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <span className="text-red-400">⚠️</span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Name Field */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                Full Name
              </label>
              <div className="mt-1">
                <input
                  id="name"
                  name="name"
                  type="text"
                  autoComplete="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                  placeholder="Enter your full name"
                />
              </div>
            </div>

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                  placeholder="Enter your email"
                />
              </div>
            </div>

            {/* Organization Field */}
            <div>
              <label htmlFor="organization" className="block text-sm font-medium text-gray-700">
                Organization <span className="text-gray-400">(Optional)</span>
              </label>
              <div className="mt-1">
                <input
                  id="organization"
                  name="organization"
                  type="text"
                  autoComplete="organization"
                  value={formData.organization}
                  onChange={handleChange}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                  placeholder="Enter your organization name"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="appearance-none block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
                  placeholder="Create a strong password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  <span className="text-gray-400 hover:text-gray-600">
                    {showPassword ? '🙈' : '👁️'}
                  </span>
                </button>
              </div>
              
              {/* Password Strength Indicator */}
              {passwordStrength && (
                <div className={`mt-2 px-3 py-2 rounded-md border text-xs ${getPasswordStrengthColor()}`}>
                  Password strength: <span className="font-medium capitalize">{passwordStrength}</span>
                  {passwordStrength !== 'strong' && (
                    <div className="mt-1 text-xs">
                      Use 8+ characters with uppercase, lowercase, numbers, and symbols
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Confirm Password Field */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirm Password
              </label>
              <div className="mt-1 relative">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={`appearance-none block w-full px-3 py-2 pr-10 border rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm ${
                    passwordsMatch ? 'border-gray-300' : 'border-red-300'
                  }`}
                  placeholder="Confirm your password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  <span className="text-gray-400 hover:text-gray-600">
                    {showConfirmPassword ? '🙈' : '👁️'}
                  </span>
                </button>
              </div>
              {!passwordsMatch && formData.confirmPassword && (
                <p className="mt-1 text-xs text-red-600">Passwords do not match</p>
              )}
            </div>

            {/* Terms Agreement */}
            <div>
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    id="agreedToTerms"
                    name="agreedToTerms"
                    type="checkbox"
                    checked={agreedToTerms}
                    onChange={(e) => setAgreedToTerms(e.target.checked)}
                    className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="agreedToTerms" className="text-gray-700">
                    I agree to the{' '}
                    <a href="#" className="text-primary hover:text-primary-dark font-medium">
                      Terms of Service
                    </a>{' '}
                    and{' '}
                    <a href="#" className="text-primary hover:text-primary-dark font-medium">
                      Privacy Policy
                    </a>
                  </label>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={isLoading || !passwordsMatch || !agreedToTerms || passwordStrength === 'weak'}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Creating account...
                  </>
                ) : (
                  'Create account'
                )}
              </button>
            </div>

            {/* Login Link */}
            <div className="text-center">
              <p className="text-sm text-gray-600">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={onSwitchToLogin}
                  className="font-medium text-primary hover:text-primary-dark"
                >
                  Sign in here
                </button>
              </p>
            </div>

            {/* Back to Landing */}
            <div className="text-center">
              <Link
                to="/"
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                ← Back to homepage
              </Link>
            </div>
          </form>
        </div>
      </div>

      {/* Security Features */}
      <div className="mt-8 text-center">
        <div className="inline-flex items-center space-x-6 px-6 py-3 bg-white border border-gray-200 rounded-lg shadow-sm">
          <div className="flex items-center text-sm text-gray-600">
            <span className="text-green-600 mr-2">🔒</span>
            Enterprise Security
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <span className="text-blue-600 mr-2">🛡️</span>
            Real-time Protection
          </div>
          <div className="flex items-center text-sm text-gray-600">
            <span className="text-purple-600 mr-2">🤖</span>
            AI-Powered Detection
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterForm;