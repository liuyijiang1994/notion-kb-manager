import { apiClient } from './client';
import type { ApiResponse, LoginRequest, LoginResponse, User } from './types';

export const authApi = {
  /**
   * Login with username and password
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<never, ApiResponse<LoginResponse>>(
      '/auth/login',
      credentials
    );
    return response.data!;
  },

  /**
   * Get current user information
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<never, ApiResponse<{ user: User }>>('/auth/me');
    return response.data!.user;
  },

  /**
   * Logout (client-side only)
   */
  logout: async (): Promise<void> => {
    // Backend doesn't have a logout endpoint, just clear token client-side
    localStorage.removeItem('access_token');
  },

  /**
   * Refresh access token
   */
  refresh: async (refreshToken: string): Promise<LoginResponse> => {
    const response = await apiClient.post<never, ApiResponse<LoginResponse>>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data!;
  },

  /**
   * Generate API key
   */
  generateApiKey: async (name: string): Promise<string> => {
    const response = await apiClient.post<never, ApiResponse<{ api_key: string }>>(
      '/auth/generate-api-key',
      { name }
    );
    return response.data!.api_key;
  },
};
