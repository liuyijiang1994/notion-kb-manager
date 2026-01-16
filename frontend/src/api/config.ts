import { apiClient } from './client';
import type { ApiResponse, Config } from './types';

export const configApi = {
  /**
   * Get current configuration (aggregates from multiple endpoints)
   */
  getConfig: async (): Promise<Config> => {
    // Fetch from multiple backend endpoints
    const [modelsRes, paramsRes, notionRes] = await Promise.all([
      apiClient.get<never, ApiResponse<any[]>>('/config/models').catch(() => ({ data: [] })),
      apiClient.get<never, ApiResponse<any>>('/config/parameters').catch(() => ({ data: {} })),
      apiClient.get<never, ApiResponse<any>>('/config/notion').catch(() => ({ data: null })),
    ]);

    const models = modelsRes.data || [];
    const params = paramsRes.data || {};
    const notion = notionRes.data;
    const defaultModel = models.find((m: any) => m.is_default) || models[0];

    return {
      notion_api_key: notion ? '***' : undefined, // Masked on backend
      openai_api_key: defaultModel ? '***' : undefined, // Masked on backend
      openai_base_url: defaultModel?.api_url || '',
      openai_model: defaultModel?.name || 'gpt-3.5-turbo',
      temperature: 0.7,
      max_tokens: defaultModel?.max_tokens || 2000,
      quality_threshold: params.quality_threshold || 70,
      batch_size: params.batch_size || 10,
      auto_export: true,
      retry_attempts: 3,
      timeout: defaultModel?.timeout || 30,
    };
  },

  /**
   * Update configuration
   */
  updateConfig: async (config: Partial<Config>): Promise<Config> => {
    const updates: Promise<any>[] = [];

    // Update Notion config if provided
    if (config.notion_api_key) {
      updates.push(
        apiClient.post('/config/notion', {
          api_token: config.notion_api_key,
        })
      );
    }

    // Update AI model config if provided
    if (config.openai_api_key || config.openai_base_url) {
      // Get existing models
      const modelsRes = await apiClient.get<never, ApiResponse<any[]>>('/config/models');
      const models = modelsRes.data || [];
      const defaultModel = models.find((m: any) => m.is_default);

      if (defaultModel) {
        // Update existing model
        updates.push(
          apiClient.put(`/config/models/${defaultModel.id}`, {
            name: config.openai_model || defaultModel.name,
            api_url: config.openai_base_url || defaultModel.api_url,
            ...(config.openai_api_key ? { api_token: config.openai_api_key } : {}),
            max_tokens: config.max_tokens || defaultModel.max_tokens,
            timeout: config.timeout || defaultModel.timeout,
          })
        );
      } else if (config.openai_api_key && config.openai_base_url) {
        // Create new model
        updates.push(
          apiClient.post('/config/models', {
            name: config.openai_model || 'default-model',
            api_url: config.openai_base_url,
            api_token: config.openai_api_key,
            max_tokens: config.max_tokens || 2000,
            timeout: config.timeout || 30,
            rate_limit: 60,
            is_default: true,
          })
        );
      }
    }

    // Update parameters if provided
    if (config.quality_threshold !== undefined || config.batch_size !== undefined) {
      updates.push(
        apiClient.put('/config/parameters', {
          quality_threshold: config.quality_threshold,
          batch_size: config.batch_size,
        })
      );
    }

    await Promise.all(updates);

    // Return updated config
    return configApi.getConfig();
  },

  /**
   * Test Notion API connection
   */
  testNotionConnection: async (): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post<never, ApiResponse<any>>(
      '/config/notion/test'
    );
    const result = response.data!;
    return {
      success: result.success || false,
      message: result.message || (result.success ? 'Connection successful' : 'Connection failed'),
    };
  },

  /**
   * Test OpenAI API connection
   */
  testOpenAIConnection: async (): Promise<{ success: boolean; message: string }> => {
    // TODO: Backend doesn't have this endpoint yet
    return { success: true, message: 'Test not implemented yet' };
  },
};
