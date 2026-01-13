import { apiClient } from './client';
import type { ApiResponse, Task, TaskItem, PaginatedResponse } from './types';

export const tasksApi = {
  /**
   * Get all tasks with optional filtering
   */
  getTasks: async (params?: {
    status?: string;
    type?: string;
    page?: number;
    limit?: number;
  }): Promise<Task[]> => {
    const response = await apiClient.get<never, ApiResponse<{ tasks: Task[] }>>(
      '/tasks/history',
      { params }
    );
    return response.data!.tasks;
  },

  /**
   * Get a specific task by ID
   */
  getTask: async (id: number): Promise<Task> => {
    const response = await apiClient.get<never, ApiResponse<{ task: Task }>>(
      `/tasks/history/${id}`
    );
    return response.data!.task;
  },

  /**
   * Get task items (detailed status of each item in a task)
   */
  getTaskItems: async (
    taskId: number,
    params?: { status?: string; page?: number; limit?: number }
  ): Promise<PaginatedResponse<TaskItem>> => {
    const response = await apiClient.get<never, ApiResponse<PaginatedResponse<TaskItem>>>(
      `/tasks/history/${taskId}/items`,
      { params }
    );
    return response.data!;
  },

  /**
   * Retry a failed task
   */
  retryTask: async (id: number): Promise<Task> => {
    const response = await apiClient.post<never, ApiResponse<{ task: Task }>>(
      `/tasks/history/${id}/retry`
    );
    return response.data!.task;
  },

  /**
   * Rerun a task (clone and execute again)
   */
  rerunTask: async (id: number): Promise<Task> => {
    const response = await apiClient.post<never, ApiResponse<{ task: Task }>>(
      `/tasks/history/${id}/rerun`
    );
    return response.data!.task;
  },

  /**
   * Cancel a running task
   */
  cancelTask: async (id: number): Promise<string> => {
    const response = await apiClient.delete<never, ApiResponse<{ message: string }>>(
      `/tasks/history/${id}`
    );
    return response.data!.message;
  },

  /**
   * Get task statistics
   */
  getTaskStats: async (): Promise<any> => {
    const response = await apiClient.get<never, ApiResponse>('/tasks/statistics');
    return response.data;
  },
};
