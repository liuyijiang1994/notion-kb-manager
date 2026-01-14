import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle, Loader, AlertCircle, RotateCcw } from 'lucide-react';
import { configApi } from '../../api/config';
import { FormSelect } from '../common/FormSelect';
import { FormSlider } from '../common/FormSlider';
import { FormInput } from '../common/FormInput';

const DEFAULT_CONFIG = {
  openai_model: 'gpt-3.5-turbo',
  temperature: 0.7,
  max_tokens: 2000,
};

export const ModelConfigSection = () => {
  const queryClient = useQueryClient();
  const [model, setModel] = useState(DEFAULT_CONFIG.openai_model);
  const [temperature, setTemperature] = useState(DEFAULT_CONFIG.temperature);
  const [maxTokens, setMaxTokens] = useState(DEFAULT_CONFIG.max_tokens);
  const [hasChanges, setHasChanges] = useState(false);

  // Load existing config
  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: configApi.getConfig,
  });

  // Update state when config loads
  useEffect(() => {
    if (config && !hasChanges) {
      setModel(config.openai_model || DEFAULT_CONFIG.openai_model);
      setTemperature(config.temperature ?? DEFAULT_CONFIG.temperature);
      setMaxTokens(config.max_tokens || DEFAULT_CONFIG.max_tokens);
    }
  }, [config, hasChanges]);

  // Save config mutation
  const saveMutation = useMutation({
    mutationFn: () =>
      configApi.updateConfig({
        openai_model: model,
        temperature,
        max_tokens: maxTokens,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      setHasChanges(false);
    },
  });

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setModel(e.target.value);
    setHasChanges(true);
  };

  const handleTemperatureChange = (value: number) => {
    setTemperature(value);
    setHasChanges(true);
  };

  const handleMaxTokensChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMaxTokens(Number(e.target.value));
    setHasChanges(true);
  };

  const handleReset = () => {
    setModel(DEFAULT_CONFIG.openai_model);
    setTemperature(DEFAULT_CONFIG.temperature);
    setMaxTokens(DEFAULT_CONFIG.max_tokens);
    setHasChanges(true);
  };

  const handleSave = () => {
    saveMutation.mutate();
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
      {/* Model Selection */}
      <FormSelect
        label="OpenAI Model"
        name="model"
        value={model}
        onChange={handleModelChange}
        options={[
          { value: 'gpt-4', label: 'GPT-4 (Most Capable)' },
          { value: 'gpt-4-turbo', label: 'GPT-4 Turbo (Fast & Capable)' },
          { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo (Balanced)' },
          { value: 'gpt-3.5-turbo-16k', label: 'GPT-3.5 Turbo 16K (Large Context)' },
        ]}
        disabled={saveMutation.isPending}
      />

      {/* Temperature Slider */}
      <FormSlider
        label="Temperature"
        name="temperature"
        value={temperature}
        onChange={handleTemperatureChange}
        min={0}
        max={2}
        step={0.1}
        disabled={saveMutation.isPending}
        helperText="Controls randomness: 0 = focused and deterministic, 2 = more creative and random"
        valueFormatter={(v) => v.toFixed(1)}
      />

      {/* Max Tokens */}
      <FormInput
        label="Max Tokens"
        name="max_tokens"
        type="number"
        value={maxTokens.toString()}
        onChange={handleMaxTokensChange}
        disabled={saveMutation.isPending}
        placeholder="2000"
      />

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          <strong>Note:</strong> These settings affect how the AI processes your content. Higher
          temperature values produce more creative outputs, while lower values are more focused.
          Max tokens limits the length of AI-generated content.
        </p>
      </div>

      {/* Save Success */}
      {saveMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <p className="text-sm font-medium text-green-900">Model configuration saved successfully!</p>
        </div>
      )}

      {/* Save Error */}
      {saveMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <p className="text-sm font-medium text-red-900">Failed to save model configuration</p>
        </div>
      )}

      {/* Action Buttons */}
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

        <button
          type="button"
          onClick={handleReset}
          disabled={saveMutation.isPending}
          className="px-6 py-2.5 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          <RotateCcw className="h-5 w-5" />
          Reset to Defaults
        </button>

        {hasChanges && (
          <p className="text-sm text-gray-500">You have unsaved changes</p>
        )}
      </div>
    </div>
  );
};
