import { apiClient } from './client';
import type { ApiResponse, ImportTask, WorkflowResponse } from './types';

export const importsApi = {
  /**
   * Import a single URL
   */
  importSingleLink: async (url: string, metadata?: { title?: string; tags?: string[] }): Promise<ImportTask> => {
    const response = await apiClient.post<never, ApiResponse<{ task_id: number; total: number; imported: number }>>(
      '/links/import/manual',
      { text: url, task_name: 'Manual URL Import' }
    );
    return {
      id: response.data!.task_id,
      status: 'completed',
      created_at: new Date().toISOString(),
      total_links: response.data!.total,
      processed_links: response.data!.imported,
    };
  },

  /**
   * Import multiple URLs
   */
  importBatchLinks: async (urls: string[]): Promise<ImportTask> => {
    const text = urls.join('\n');
    const response = await apiClient.post<never, ApiResponse<{ task_id: number; total: number; imported: number }>>(
      '/links/import/manual',
      { text, task_name: 'Batch URL Import' }
    );
    return {
      id: response.data!.task_id,
      status: 'completed',
      created_at: new Date().toISOString(),
      total_links: response.data!.total,
      processed_links: response.data!.imported,
    };
  },

  /**
   * Upload and import bookmark file
   */
  uploadBookmarkFile: async (file: File): Promise<ImportTask> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<never, ApiResponse<{ task_id: number; total: number; imported: number }>>(
      '/links/import/favorites',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return {
      id: response.data!.task_id,
      status: 'completed',
      created_at: new Date().toISOString(),
      total_links: response.data!.total,
      processed_links: response.data!.imported,
    };
  },

  /**
   * Start workflow for an import task
   * Triggers: Import → Parse → AI → Notion
   */
  startWorkflow: async (importTaskId: number, config?: {
    parse?: boolean;
    ai_process?: boolean;
    export_notion?: boolean;
  }): Promise<WorkflowResponse> => {
    const response = await apiClient.post<never, ApiResponse<WorkflowResponse>>(
      '/workflows/start',
      {
        import_task_id: importTaskId,
        ...config,
      }
    );
    return response.data!;
  },

  /**
   * Get workflow status
   */
  getWorkflowStatus: async (importTaskId: number): Promise<WorkflowResponse> => {
    const response = await apiClient.get<never, ApiResponse<WorkflowResponse>>(
      `/workflows/${importTaskId}/status`
    );
    return response.data!;
  },
};
