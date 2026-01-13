import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { tasksApi } from '../api/tasks';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { TaskTable } from '../components/tasks/TaskTable';

export const TasksPage = () => {
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const {
    data: tasks,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['tasks', statusFilter],
    queryFn: () =>
      tasksApi.getTasks(statusFilter !== 'all' ? { status: statusFilter } : undefined),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  const filteredTasks =
    statusFilter === 'all'
      ? tasks
      : tasks?.filter((task) => task.status === statusFilter);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Tasks</h1>
        <div className="text-sm text-gray-500">
          Auto-refreshing every 5 seconds
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center gap-4">
          <label htmlFor="status-filter" className="text-sm font-medium text-gray-700">
            Filter by Status:
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>

          {tasks && (
            <div className="text-sm text-gray-600">
              Showing {filteredTasks?.length || 0} of {tasks.length} tasks
            </div>
          )}
        </div>
      </div>

      {/* Error */}
      {error && <ErrorAlert message="Failed to load tasks" />}

      {/* Loading */}
      {isLoading && <LoadingSpinner size="lg" text="Loading tasks..." />}

      {/* Tasks Table */}
      {tasks && <TaskTable tasks={filteredTasks || []} />}
    </div>
  );
};
