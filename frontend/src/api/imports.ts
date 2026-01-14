import { apiClient } from './client';
import type { ApiResponse, ImportTask, WorkflowResponse } from './types';

export const importsApi = {
  /**
   * Import a single URL
   */
  importSingleLink: async (url: string, metadata?: { title?: string; tags?: string[] }): Promise<ImportTask> => {
    const response = await apiClient.post<never, ApiResponse<{ task: ImportTask }>>(
      '/import/link',
      { url, ...metadata }
    );
    return response.data!.task;
  },

  /**
   * Import multiple URLs
   */
  importBatchLinks: async (urls: string[]): Promise<ImportTask> => {
    const response = await apiClient.post<never, ApiResponse<{ task: ImportTask }>>(
      '/import/links',
      { urls }
    );
    return response.data!.task;
  },

  /**
   * Upload and import bookmark file
   */
  uploadBookmarkFile: async (file: File): Promise<ImportTask> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<never, ApiResponse<{ task: ImportTask }>>(
      '/import/bookmarks',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data!.task;
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
