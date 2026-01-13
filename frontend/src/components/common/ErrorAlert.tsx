import { AlertCircle, X } from 'lucide-react';

interface ErrorAlertProps {
  title?: string;
  message: string;
  onClose?: () => void;
}

export const ErrorAlert = ({ title = 'Error', message, onClose }: ErrorAlertProps) => {
  return (
    <div className="rounded-lg bg-red-50 border border-red-200 p-4">
      <div className="flex items-start">
        <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="text-sm font-medium text-red-800">{title}</h3>
          <p className="mt-1 text-sm text-red-700">{message}</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="ml-3 flex-shrink-0 inline-flex text-red-400 hover:text-red-600"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
};
