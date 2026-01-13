import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/auth';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import type { LoginRequest } from '../api/types';

export const useAuth = () => {
  const { login: setAuth, logout: clearAuth, ...authState } = useAuthStore();
  const navigate = useNavigate();

  const loginMutation = useMutation({
    mutationFn: (credentials: LoginRequest) => authApi.login(credentials),
    onSuccess: (data) => {
      setAuth(data.access_token, data.refresh_token, data.user);
      navigate('/dashboard');
    },
  });

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      clearAuth();
      navigate('/login');
    },
  });

  const logout = () => {
    logoutMutation.mutate();
  };

  return {
    ...authState,
    login: loginMutation.mutate,
    logout,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    isLoggingOut: logoutMutation.isPending,
  };
};
