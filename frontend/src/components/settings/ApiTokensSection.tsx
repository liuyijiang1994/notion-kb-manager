import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle, Loader, AlertCircle } from 'lucide-react';
import { configApi } from '../../api/config';
import { PasswordInput } from '../common/PasswordInput';

export const ApiTokensSection = () => {
  const queryClient = useQueryClient();
  const [notionKey, setNotionKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
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
      setOpenaiKey(config.openai_api_key || '');
    }
  }, [config, hasChanges]);

  // Save config mutation
  const saveMutation = useMutation({
    mutationFn: () =>
      configApi.updateConfig({
        notion_api_key: notionKey || undefined,
        openai_api_key: openaiKey || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      setHasChanges(false);
    },
  });

  // Test Notion connection
  const testNotionMutation = useMutation({
    mutationFn: configApi.testNotionConnection,
    onSuccess: (data) => {
      setTestResult({ type: 'notion', ...data });
    },
    onError: () => {
      setTestResult({
        type: 'notion',
        success: false,
        message: 'Failed to test connection',
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

  const handleOpenaiKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setOpenaiKey(e.target.value);
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

      {/* OpenAI API Key */}
      <div>
        <PasswordInput
          label="OpenAI API Key"
          name="openai_key"
          value={openaiKey}
          onChange={handleOpenaiKeyChange}
          placeholder="sk-..."
          helperText="Get your OpenAI API key from https://platform.openai.com/api-keys"
          disabled={saveMutation.isPending}
        />
        <button
          type="button"
          onClick={() => testOpenAIMutation.mutate()}
          disabled={!openaiKey || testOpenAIMutation.isPending || saveMutation.isPending}
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
            , OpenAI{' '}
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
