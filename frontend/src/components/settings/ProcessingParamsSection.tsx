import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle, Loader, AlertCircle, RotateCcw } from 'lucide-react';
import { configApi } from '../../api/config';
import { FormSlider } from '../common/FormSlider';
import { FormInput } from '../common/FormInput';
import { FormToggle } from '../common/FormToggle';

const DEFAULT_CONFIG = {
  quality_threshold: 70,
  batch_size: 10,
  retry_attempts: 3,
  timeout: 300,
  auto_export: true,
};

export const ProcessingParamsSection = () => {
  const queryClient = useQueryClient();
  const [qualityThreshold, setQualityThreshold] = useState(DEFAULT_CONFIG.quality_threshold);
  const [batchSize, setBatchSize] = useState(DEFAULT_CONFIG.batch_size);
  const [retryAttempts, setRetryAttempts] = useState(DEFAULT_CONFIG.retry_attempts);
  const [timeout, setTimeout] = useState(DEFAULT_CONFIG.timeout);
  const [autoExport, setAutoExport] = useState(DEFAULT_CONFIG.auto_export);
  const [hasChanges, setHasChanges] = useState(false);

  // Load existing config
  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: configApi.getConfig,
  });

  // Update state when config loads
  useEffect(() => {
    if (config && !hasChanges) {
      setQualityThreshold(config.quality_threshold ?? DEFAULT_CONFIG.quality_threshold);
      setBatchSize(config.batch_size || DEFAULT_CONFIG.batch_size);
      setRetryAttempts(config.retry_attempts ?? DEFAULT_CONFIG.retry_attempts);
      setTimeout(config.timeout || DEFAULT_CONFIG.timeout);
      setAutoExport(config.auto_export ?? DEFAULT_CONFIG.auto_export);
    }
  }, [config, hasChanges]);

  // Save config mutation
  const saveMutation = useMutation({
    mutationFn: () =>
      configApi.updateConfig({
        quality_threshold: qualityThreshold,
        batch_size: batchSize,
        retry_attempts: retryAttempts,
        timeout,
        auto_export: autoExport,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      setHasChanges(false);
    },
  });

  const handleQualityThresholdChange = (value: number) => {
    setQualityThreshold(value);
    setHasChanges(true);
  };

  const handleBatchSizeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setBatchSize(Number(e.target.value));
    setHasChanges(true);
  };

  const handleRetryAttemptsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setRetryAttempts(Number(e.target.value));
    setHasChanges(true);
  };

  const handleTimeoutChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTimeout(Number(e.target.value));
    setHasChanges(true);
  };

  const handleAutoExportChange = (checked: boolean) => {
    setAutoExport(checked);
    setHasChanges(true);
  };

  const handleReset = () => {
    setQualityThreshold(DEFAULT_CONFIG.quality_threshold);
    setBatchSize(DEFAULT_CONFIG.batch_size);
    setRetryAttempts(DEFAULT_CONFIG.retry_attempts);
    setTimeout(DEFAULT_CONFIG.timeout);
    setAutoExport(DEFAULT_CONFIG.auto_export);
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
      {/* Quality Threshold */}
      <FormSlider
        label="Quality Threshold"
        name="quality_threshold"
        value={qualityThreshold}
        onChange={handleQualityThresholdChange}
        min={0}
        max={100}
        step={5}
        disabled={saveMutation.isPending}
        helperText="Minimum quality score (0-100) for content to be processed"
        valueFormatter={(v) => `${v}%`}
      />

      {/* Batch Size */}
      <FormInput
        label="Batch Size"
        name="batch_size"
        type="number"
        value={batchSize.toString()}
        onChange={handleBatchSizeChange}
        disabled={saveMutation.isPending}
        placeholder="10"
      />
      <p className="text-sm text-gray-500 -mt-4">Number of items to process in each batch</p>

      {/* Retry Attempts */}
      <FormInput
        label="Retry Attempts"
        name="retry_attempts"
        type="number"
        value={retryAttempts.toString()}
        onChange={handleRetryAttemptsChange}
        disabled={saveMutation.isPending}
        placeholder="3"
      />
      <p className="text-sm text-gray-500 -mt-4">Number of times to retry failed operations</p>

      {/* Timeout */}
      <FormInput
        label="Timeout (seconds)"
        name="timeout"
        type="number"
        value={timeout.toString()}
        onChange={handleTimeoutChange}
        disabled={saveMutation.isPending}
        placeholder="300"
      />
      <p className="text-sm text-gray-500 -mt-4">Maximum time to wait for operations to complete</p>

      {/* Auto-export to Notion */}
      <FormToggle
        label="Auto-export to Notion"
        name="auto_export"
        checked={autoExport}
        onChange={handleAutoExportChange}
        disabled={saveMutation.isPending}
        helperText="Automatically export processed content to Notion after AI processing"
      />

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          <strong>Tip:</strong> Lower batch sizes reduce memory usage but may take longer. Higher
          quality thresholds will filter out lower-quality content but may reject valid articles.
        </p>
      </div>

      {/* Save Success */}
      {saveMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <p className="text-sm font-medium text-green-900">Processing parameters saved successfully!</p>
        </div>
      )}

      {/* Save Error */}
      {saveMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <p className="text-sm font-medium text-red-900">Failed to save processing parameters</p>
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
