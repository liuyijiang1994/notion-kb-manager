import { useQuery } from '@tanstack/react-query';
import { monitoringApi } from '../api/monitoring';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { HealthCard } from '../components/dashboard/HealthCard';
import { StatisticsCards } from '../components/dashboard/StatisticsCards';
import { QueueStatus } from '../components/dashboard/QueueStatus';

export const DashboardPage = () => {
  const {
    data: health,
    isLoading: healthLoading,
    error: healthError,
  } = useQuery({
    queryKey: ['health'],
    queryFn: monitoringApi.getHealth,
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery({
    queryKey: ['statistics'],
    queryFn: monitoringApi.getStatistics,
    refetchInterval: 10000, // Auto-refresh every 10 seconds
  });

  const {
    data: queues,
    isLoading: queuesLoading,
    error: queuesError,
  } = useQuery({
    queryKey: ['queues'],
    queryFn: monitoringApi.getQueues,
    refetchInterval: 5000,
  });

  if (healthLoading && statsLoading && queuesLoading) {
    return <LoadingSpinner size="lg" text="Loading dashboard..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">System Dashboard</h1>
        <div className="text-sm text-gray-500">
          Auto-refreshing every 5 seconds
        </div>
      </div>

      {/* Health Status */}
      {healthError && (
        <ErrorAlert message="Failed to load system health" />
      )}
      {health && <HealthCard health={health} />}

      {/* Statistics */}
      {statsError && (
        <ErrorAlert message="Failed to load statistics" />
      )}
      {stats && <StatisticsCards statistics={stats.statistics} />}

      {/* Queue Status */}
      {queuesError && (
        <ErrorAlert message="Failed to load queue status" />
      )}
      {queues && <QueueStatus queues={queues.queues} />}
    </div>
  );
};
