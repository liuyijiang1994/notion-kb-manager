import { FileText, Activity, CheckCircle, AlertCircle } from 'lucide-react';
import type { Statistics } from '../../api/types';

interface StatisticsCardsProps {
  statistics: Statistics;
}

export const StatisticsCards = ({ statistics }: StatisticsCardsProps) => {
  const cards = [
    {
      title: 'Total Tasks',
      value: statistics.total_tasks,
      icon: FileText,
      color: 'blue',
    },
    {
      title: 'Running Tasks',
      value: statistics.running_tasks,
      icon: Activity,
      color: 'yellow',
    },
    {
      title: 'Completed Tasks',
      value: statistics.completed_tasks,
      icon: CheckCircle,
      color: 'green',
    },
    {
      title: 'Failed Tasks',
      value: statistics.failed_tasks,
      icon: AlertCircle,
      color: 'red',
    },
  ];

  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card) => (
        <div
          key={card.title}
          className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg ${colorClasses[card.color as keyof typeof colorClasses]}`}>
              <card.icon className="h-6 w-6" />
            </div>
          </div>
          <h3 className="text-gray-600 text-sm font-medium mb-1">{card.title}</h3>
          <p className="text-3xl font-bold text-gray-900">{card.value.toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
};
