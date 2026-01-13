import { BarChart3 } from 'lucide-react';
import type { QueueInfo } from '../../api/types';

interface QueueStatusProps {
  queues: QueueInfo[];
}

export const QueueStatus = ({ queues }: QueueStatusProps) => {
  const getQueueColor = (pending: number) => {
    if (pending > 100) return 'bg-red-500';
    if (pending > 50) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getProgressPercentage = (queue: QueueInfo) => {
    const total = queue.total || 1;
    return Math.min((queue.pending / total) * 100, 100);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center gap-3 mb-6">
        <BarChart3 className="h-6 w-6 text-gray-700" />
        <h2 className="text-xl font-semibold text-gray-900">Queue Status</h2>
      </div>

      <div className="space-y-4">
        {queues.map((queue) => (
          <div key={queue.name} className="border-b border-gray-100 last:border-0 pb-4 last:pb-0">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <h3 className="font-semibold text-gray-900 capitalize">{queue.name}</h3>
                <span className="text-sm text-gray-500">
                  {queue.pending} pending
                </span>
              </div>
              <div className="text-sm text-gray-600">
                <span className="font-medium">{queue.running}</span> running,{' '}
                <span className="font-medium text-red-600">{queue.failed}</span> failed
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
              <div
                className={`h-full ${getQueueColor(queue.pending)} transition-all duration-300`}
                style={{ width: `${getProgressPercentage(queue)}%` }}
              />
            </div>

            {/* Queue Stats */}
            <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
              <span>Finished: {queue.finished}</span>
              <span>Scheduled: {queue.scheduled}</span>
              <span>Total: {queue.total}</span>
            </div>
          </div>
        ))}
      </div>

      {queues.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>No queue data available</p>
        </div>
      )}
    </div>
  );
};
