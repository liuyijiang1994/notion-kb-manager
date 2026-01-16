import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle, Loader, AlertCircle } from 'lucide-react';
import { configApi } from '../../api/config';
import { PasswordInput } from '../common/PasswordInput';
import { FormInput } from '../common/FormInput';

export const ApiTokensSection = () => {
  const queryClient = useQueryClient();
  const [notionKey, setNotionKey] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiBaseUrl, setApiBaseUrl] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const [testResult, setTestResult] = useState<{
    type: 'notion' | 'openai';
    success: boolean;
    message: string;
  } | null>(null);

  // Load existing config
  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: configApi.getConfig,
  });

  // Update state when config loads
  useEffect(() => {
    if (config && !hasChanges) {
      setNotionKey(config.notion_api_key || '');
      setApiKey(config.openai_api_key || '');
      setApiBaseUrl(config.openai_base_url || '');
    }
  }, [config, hasChanges]);

  // Save config mutation
  const saveMutation = useMutation({
    mutationFn: () =>
      configApi.updateConfig({
        notion_api_key: notionKey || undefined,
        openai_api_key: apiKey || undefined,
        openai_base_url: apiBaseUrl || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      setHasChanges(false);
    },
  });

  // Test Notion connection
  const testNotionMutation = useMutation({
    mutationFn: async () => {
      // Save config first, then test
      await configApi.updateConfig({ notion_api_key: notionKey });
      return await configApi.testNotionConnection();
    },
    onSuccess: (data) => {
      setTestResult({ type: 'notion', ...data });
    },
    onError: (err: any) => {
      setTestResult({
        type: 'notion',
        success: false,
        message: err.response?.data?.error?.message || 'Failed to test connection',
      });
    },
  });

  // Test OpenAI connection
  const testOpenAIMutation = useMutation({
    mutationFn: configApi.testOpenAIConnection,
    onSuccess: (data) => {
      setTestResult({ type: 'openai', ...data });
    },
    onError: () => {
      setTestResult({
        type: 'openai',
        success: false,
        message: 'Failed to test connection',
      });
    },
  });

  const handleNotionKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNotionKey(e.target.value);
    setHasChanges(true);
    setTestResult(null);
  };

  const handleApiKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setApiKey(e.target.value);
    setHasChanges(true);
    setTestResult(null);
  };

  const handleApiBaseUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setApiBaseUrl(e.target.value);
    setHasChanges(true);
    setTestResult(null);
  };

  const handleSave = () => {
    saveMutation.mutate();
    setTestResult(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="h-8 w-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Notion API Key */}
      <div>
        <PasswordInput
          label="Notion API Key"
          name="notion_key"
          value={notionKey}
          onChange={handleNotionKeyChange}
          placeholder="secret_..."
          helperText="Get your Notion API key from https://www.notion.so/my-integrations"
          disabled={saveMutation.isPending}
        />
        <button
          type="button"
          onClick={() => testNotionMutation.mutate()}
          disabled={!notionKey || testNotionMutation.isPending || saveMutation.isPending}
          className="mt-2 px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {testNotionMutation.isPending && <Loader className="h-4 w-4 animate-spin" />}
          Test Connection
        </button>
      </div>

      {/* AI API Base URL */}
      <div>
        <FormInput
          label="AI API Base URL"
          name="api_base_url"
          value={apiBaseUrl}
          onChange={handleApiBaseUrlChange}
          placeholder="https://ark.cn-beijing.volces.com/api/v3"
          disabled={saveMutation.isPending}
        />
      </div>

      {/* AI API Key */}
      <div>
        <PasswordInput
          label="AI API Key"
          name="api_key"
          value={apiKey}
          onChange={handleApiKeyChange}
          placeholder="Enter your AI API key"
          helperText="API key for your AI service (OpenAI, Volcengine, etc.)"
          disabled={saveMutation.isPending}
        />
        <button
          type="button"
          onClick={() => testOpenAIMutation.mutate()}
          disabled={!apiKey || testOpenAIMutation.isPending || saveMutation.isPending}
          className="mt-2 px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {testOpenAIMutation.isPending && <Loader className="h-4 w-4 animate-spin" />}
          Test Connection
        </button>
      </div>

      {/* Test Result */}
      {testResult && (
        <div
          className={`rounded-lg p-4 flex items-center gap-3 ${
            testResult.success
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}
        >
          {testResult.success ? (
            <CheckCircle className="h-5 w-5 text-green-600" />
          ) : (
            <AlertCircle className="h-5 w-5 text-red-600" />
          )}
          <div>
            <p
              className={`text-sm font-medium ${
                testResult.success ? 'text-green-900' : 'text-red-900'
              }`}
            >
              {testResult.type === 'notion' ? 'Notion' : 'OpenAI'} Connection Test
            </p>
            <p
              className={`text-sm ${testResult.success ? 'text-green-700' : 'text-red-700'}`}
            >
              {testResult.message}
            </p>
          </div>
        </div>
      )}

      {/* Save Success */}
      {saveMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <p className="text-sm font-medium text-green-900">Settings saved successfully!</p>
        </div>
      )}

      {/* Save Error */}
      {saveMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <p className="text-sm font-medium text-red-900">Failed to save settings</p>
        </div>
      )}

      {/* Save Button */}
      <div className="flex items-center gap-4 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={handleSave}
          disabled={!hasChanges || saveMutation.isPending}
          className="px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {saveMutation.isPending && <Loader className="h-5 w-5 animate-spin" />}
          {saveMutation.isPending ? 'Saving...' : 'Save Changes'}
        </button>

        {hasChanges && (
          <p className="text-sm text-gray-500">You have unsaved changes</p>
        )}

        {config && (
          <div className="ml-auto text-xs text-gray-500">
            Current keys: Notion{' '}
            {config.notion_api_key ? (
              <span className="text-green-600 font-medium">configured</span>
            ) : (
              <span className="text-gray-400">not set</span>
            )}
            , AI API{' '}
            {config.openai_api_key ? (
              <span className="text-green-600 font-medium">configured</span>
            ) : (
              <span className="text-gray-400">not set</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
