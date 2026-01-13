import { apiClient } from './client';
import type {
  ApiResponse,
  SystemHealth,
  WorkerInfo,
  QueueInfo,
  Statistics,
} from './types';

export const monitoringApi = {
  /**
   * Get system health status
   */
  getHealth: async (): Promise<SystemHealth> => {
    const response = await apiClient.get<never, ApiResponse<{ health: SystemHealth }>>(
      '/monitoring/health'
    );
    return response.data!.health;
  },

  /**
   * Get detailed system health
   */
  getDetailedHealth: async (): Promise<any> => {
    const response = await apiClient.get<never, ApiResponse>('/monitoring/health/detailed');
    return response.data;
  },

  /**
   * Get system statistics
   */
  getStatistics: async (): Promise<{ statistics: Statistics }> => {
    const response = await apiClient.get<never, ApiResponse<{ statistics: Statistics }>>(
      '/monitoring/statistics'
    );
    return response.data!;
  },

  /**
   * Get worker information
   */
  getWorkers: async (): Promise<{ workers: WorkerInfo[] }> => {
    const response = await apiClient.get<never, ApiResponse<{ workers: WorkerInfo[] }>>(
      '/monitoring/workers'
    );
    return response.data!;
  },

  /**
   * Get queue information
   */
  getQueues: async (): Promise<{ queues: QueueInfo[] }> => {
    const response = await apiClient.get<never, ApiResponse<{ queues: QueueInfo[] }>>(
      '/monitoring/queues'
    );
    return response.data!;
  },

  /**
   * Get Prometheus metrics (returns plain text)
   */
  getMetrics: async (): Promise<string> => {
    const response = await apiClient.get<string>('/monitoring/metrics');
    return response as unknown as string;
  },

  /**
   * Kubernetes readiness probe
   */
  getReadiness: async (): Promise<{ status: string }> => {
    const response = await apiClient.get<never, ApiResponse<{ status: string }>>(
      '/monitoring/health/ready'
    );
    return response.data!;
  },

  /**
   * Kubernetes liveness probe
   */
  getLiveness: async (): Promise<{ status: string }> => {
    const response = await apiClient.get<never, ApiResponse<{ status: string }>>(
      '/monitoring/health/alive'
    );
    return response.data!;
  },
};
