import { CheckCircle2, XCircle, Database, Activity } from 'lucide-react';
import type { SystemHealth } from '../../api/types';

interface HealthCardProps {
  health: SystemHealth;
}

export const HealthCard = ({ health }: HealthCardProps) => {
  const isHealthy = health.redis === 'connected' && health.queues_healthy;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">System Health</h2>
        <div className="flex items-center gap-2">
          {isHealthy ? (
            <>
              <CheckCircle2 className="h-6 w-6 text-green-500" />
              <span className="font-medium text-green-600">Healthy</span>
            </>
          ) : (
            <>
              <XCircle className="h-6 w-6 text-red-500" />
              <span className="font-medium text-red-600">Unhealthy</span>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Redis Status */}
        <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
          <Database className="h-8 w-8 text-blue-500" />
          <div>
            <p className="text-sm text-gray-600">Redis</p>
            <p className="font-semibold text-gray-900 capitalize">{health.redis}</p>
            {health.redis_version && (
              <p className="text-xs text-gray-500">v{health.redis_version}</p>
            )}
          </div>
        </div>

        {/* Workers Status */}
        <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
          <Activity className="h-8 w-8 text-green-500" />
          <div>
            <p className="text-sm text-gray-600">Workers</p>
            <p className="font-semibold text-gray-900">{health.workers.total} Total</p>
            <p className="text-xs text-gray-500">
              {health.workers.busy} busy, {health.workers.idle} idle
            </p>
          </div>
        </div>

        {/* Queues Status */}
        <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
          <CheckCircle2 className={`h-8 w-8 ${health.queues_healthy ? 'text-green-500' : 'text-red-500'}`} />
          <div>
            <p className="text-sm text-gray-600">Queues</p>
            <p className="font-semibold text-gray-900">
              {health.queues_healthy ? 'Healthy' : 'Issues Detected'}
            </p>
            <p className="text-xs text-gray-500">
              {Object.keys(health.queues).length} queues monitored
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
