import { apiClient } from './client';
import type { ApiResponse, Config } from './types';

export const configApi = {
  /**
   * Get current configuration
   */
  getConfig: async (): Promise<Config> => {
    const response = await apiClient.get<never, ApiResponse<Config>>('/config');
    return response.data!;
  },

  /**
   * Update configuration
   */
  updateConfig: async (config: Partial<Config>): Promise<Config> => {
    const response = await apiClient.put<never, ApiResponse<Config>>('/config', config);
    return response.data!;
  },

  /**
   * Test Notion API connection
   */
  testNotionConnection: async (): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post<never, ApiResponse<{ success: boolean; message: string }>>(
      '/config/test-notion'
    );
    return response.data!;
  },

  /**
   * Test OpenAI API connection
   */
  testOpenAIConnection: async (): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post<never, ApiResponse<{ success: boolean; message: string }>>(
      '/config/test-openai'
    );
    return response.data!;
  },
};
