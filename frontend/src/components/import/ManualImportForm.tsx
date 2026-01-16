import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Loader } from 'lucide-react';
import { importsApi } from '../../api/imports';
import { FormInput } from '../common/FormInput';
import { FormToggle } from '../common/FormToggle';
import { isValidUrl } from '../../utils/validation';

export const ManualImportForm = () => {
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [autoStart, setAutoStart] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const importMutation = useMutation({
    mutationFn: async () => {
      const task = await importsApi.importSingleLink(url);

      // TODO: Implement workflow start when backend endpoint is ready
      // if (autoStart) {
      //   await importsApi.startWorkflow(task.id, {
      //     parse: true,
      //     ai_process: true,
      //     export_notion: true,
      //   });
      // }

      return task;
    },
    onSuccess: () => {
      setSuccess(true);
      setUrl('');

      // Navigate to tasks page after 2 seconds
      setTimeout(() => {
        navigate('/tasks');
      }, 2000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.error?.message || 'Failed to import URL');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    // Validate URL
    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }

    if (!isValidUrl(url)) {
      setError('Please enter a valid URL (must start with http:// or https://)');
      return;
    }

    importMutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
      <FormInput
        label="URL to Import"
        name="url"
        type="url"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://example.com/article"
        required
        error={error}
        disabled={importMutation.isPending}
      />

      <FormToggle
        label="Auto-start Processing Workflow"
        name="autoStart"
        checked={autoStart}
        onChange={setAutoStart}
        disabled={importMutation.isPending}
        helperText="Automatically start parsing, AI processing, and Notion export"
      />

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <div>
            <p className="text-sm font-medium text-green-900">Import successful!</p>
            <p className="text-sm text-green-700">Redirecting to Tasks page...</p>
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={importMutation.isPending || success}
          className="px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {importMutation.isPending && <Loader className="h-5 w-5 animate-spin" />}
          {importMutation.isPending ? 'Importing...' : 'Import URL'}
        </button>

        {!success && (
          <button
            type="button"
            onClick={() => {
              setUrl('');
              setError('');
            }}
            disabled={importMutation.isPending}
            className="px-6 py-2.5 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Clear
          </button>
        )}
      </div>
    </form>
  );
};
