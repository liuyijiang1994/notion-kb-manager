import { Settings as SettingsIcon } from 'lucide-react';
import { ApiTokensSection } from '../components/settings/ApiTokensSection';
import { ModelConfigSection } from '../components/settings/ModelConfigSection';
import { ProcessingParamsSection } from '../components/settings/ProcessingParamsSection';

export const SettingsPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <SettingsIcon className="h-8 w-8 text-gray-700" />
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        </div>
      </div>

      <div className="space-y-6 max-w-4xl">
        {/* API Tokens Section */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">API Tokens</h2>
            <p className="text-sm text-gray-500 mt-1">
              Configure your API keys for Notion and OpenAI integration
            </p>
          </div>
          <div className="p-6">
            <ApiTokensSection />
          </div>
        </div>

        {/* Model Configuration Section */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">AI Model Configuration</h2>
            <p className="text-sm text-gray-500 mt-1">
              Configure OpenAI model settings and parameters
            </p>
          </div>
          <div className="p-6">
            <ModelConfigSection />
          </div>
        </div>

        {/* Processing Parameters Section */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Processing Parameters</h2>
            <p className="text-sm text-gray-500 mt-1">
              Configure batch processing and quality settings
            </p>
          </div>
          <div className="p-6">
            <ProcessingParamsSection />
          </div>
        </div>
      </div>
    </div>
  );
};
