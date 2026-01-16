import { useState, useMemo } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Loader } from 'lucide-react';
import { importsApi } from '../../api/imports';
import { FormTextarea } from '../common/FormTextarea';
import { FormToggle } from '../common/FormToggle';
import { isValidUrl, extractUrlsFromText } from '../../utils/validation';

export const BatchImportForm = () => {
  const navigate = useNavigate();
  const [urlsText, setUrlsText] = useState('');
  const [autoStart, setAutoStart] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Parse and validate URLs
  const urlsInfo = useMemo(() => {
    const extractedUrls = extractUrlsFromText(urlsText);
    const validUrls: string[] = [];
    const invalidUrls: string[] = [];
    const duplicates: string[] = [];

    extractedUrls.forEach((url) => {
      if (isValidUrl(url)) {
        if (validUrls.includes(url)) {
          duplicates.push(url);
        } else {
          validUrls.push(url);
        }
      } else if (url.trim()) {
        invalidUrls.push(url);
      }
    });

    return {
      validUrls,
      invalidUrls,
      duplicates,
      total: extractedUrls.length,
    };
  }, [urlsText]);

  const importMutation = useMutation({
    mutationFn: async () => {
      const task = await importsApi.importBatchLinks(urlsInfo.validUrls);

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
      setUrlsText('');

      // Navigate to tasks page after 2 seconds
      setTimeout(() => {
        navigate('/tasks');
      }, 2000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.error?.message || 'Failed to import URLs');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    // Validate
    if (!urlsText.trim()) {
      setError('Please enter at least one URL');
      return;
    }

    if (urlsInfo.validUrls.length === 0) {
      setError('No valid URLs found. Please check your input.');
      return;
    }

    importMutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-3xl">
      <FormTextarea
        label="URLs to Import"
        name="urls"
        value={urlsText}
        onChange={(e) => setUrlsText(e.target.value)}
        placeholder="https://example.com/article-1&#10;https://example.com/article-2&#10;https://example.com/article-3"
        rows={10}
        error={error}
        disabled={importMutation.isPending}
        helperText="Enter one URL per line or comma-separated"
      />

      {/* URL Statistics */}
      {urlsText && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Valid URLs:</span>
              <span className="ml-2 font-semibold text-green-600">
                {urlsInfo.validUrls.length}
              </span>
            </div>
            {urlsInfo.invalidUrls.length > 0 && (
              <div>
                <span className="text-gray-600">Invalid URLs:</span>
                <span className="ml-2 font-semibold text-red-600">
                  {urlsInfo.invalidUrls.length}
                </span>
              </div>
            )}
            {urlsInfo.duplicates.length > 0 && (
              <div>
                <span className="text-gray-600">Duplicates:</span>
                <span className="ml-2 font-semibold text-yellow-600">
                  {urlsInfo.duplicates.length}
                </span>
              </div>
            )}
          </div>

          {urlsInfo.invalidUrls.length > 0 && (
            <div className="pt-2 border-t border-gray-300">
              <p className="text-sm font-medium text-red-700 mb-1">Invalid URLs:</p>
              <ul className="text-xs text-red-600 space-y-1 max-h-20 overflow-y-auto">
                {urlsInfo.invalidUrls.map((url, idx) => (
                  <li key={idx} className="truncate">
                    {url}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <FormToggle
        label="Auto-start Processing Workflow"
        name="autoStart"
        checked={autoStart}
        onChange={setAutoStart}
        disabled={importMutation.isPending}
        helperText="Automatically start parsing, AI processing, and Notion export for all URLs"
      />

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <div>
            <p className="text-sm font-medium text-green-900">
              Successfully imported {urlsInfo.validUrls.length} URLs!
            </p>
            <p className="text-sm text-green-700">Redirecting to Tasks page...</p>
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={importMutation.isPending || success || urlsInfo.validUrls.length === 0}
          className="px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {importMutation.isPending && <Loader className="h-5 w-5 animate-spin" />}
          {importMutation.isPending
            ? 'Importing...'
            : `Import ${urlsInfo.validUrls.length} URL${urlsInfo.validUrls.length !== 1 ? 's' : ''}`}
        </button>

        {!success && (
          <button
            type="button"
            onClick={() => {
              setUrlsText('');
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
