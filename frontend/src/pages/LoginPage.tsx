import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { Database, Eye, EyeOff } from 'lucide-react';

export const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoggingIn, loginError } = useAuth();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login({ username, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-blue-100 p-3 rounded-full">
              <Database className="h-12 w-12 text-blue-600" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Notion KB Manager</h1>
          <p className="text-gray-600 mt-2">Sign in to your account</p>
        </div>

        {/* Error Alert */}
        {loginError && (
          <div className="mb-6">
            <ErrorAlert
              message={
                (loginError as any)?.response?.data?.error?.message ||
                'Invalid username or password'
              }
            />
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your username"
              required
              autoComplete="username"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                placeholder="Enter your password"
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoggingIn}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 active:bg-blue-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoggingIn ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* Default Credentials */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-2">Default credentials for testing:</p>
            <div className="bg-gray-50 rounded-lg p-3 text-sm">
              <p className="font-mono text-gray-700">
                <span className="font-semibold">Username:</span> admin
              </p>
              <p className="font-mono text-gray-700 mt-1">
                <span className="font-semibold">Password:</span> admin123
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
