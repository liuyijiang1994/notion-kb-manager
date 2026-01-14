import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Loader, Upload, FileText, X } from 'lucide-react';
import { importsApi } from '../../api/imports';
import { FormToggle } from '../common/FormToggle';
import { parseBookmarkHtml, isValidBookmarkFile, isValidFileSize } from '../../utils/validation';

export const FileImportForm = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [autoStart, setAutoStart] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [preview, setPreview] = useState<{ url: string; title: string }[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const importMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('No file selected');

      const task = await importsApi.uploadBookmarkFile(file);

      if (autoStart) {
        await importsApi.startWorkflow(task.id, {
          parse: true,
          ai_process: true,
          export_notion: true,
        });
      }

      return task;
    },
    onSuccess: () => {
      setSuccess(true);
      setFile(null);
      setPreview([]);

      // Navigate to tasks page after 2 seconds
      setTimeout(() => {
        navigate('/tasks');
      }, 2000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.error?.message || 'Failed to upload bookmark file');
    },
  });

  const handleFileSelect = async (selectedFile: File) => {
    setError('');
    setSuccess(false);
    setPreview([]);

    // Validate file type
    if (!isValidBookmarkFile(selectedFile)) {
      setError('Invalid file type. Please upload an HTML bookmark file.');
      return;
    }

    // Validate file size
    if (!isValidFileSize(selectedFile)) {
      setError('File is too large. Maximum size is 10MB.');
      return;
    }

    setFile(selectedFile);

    // Parse and preview bookmarks
    try {
      const text = await selectedFile.text();
      const bookmarks = parseBookmarkHtml(text);
      setPreview(bookmarks.slice(0, 10)); // Show first 10 for preview
    } catch (err) {
      setError('Failed to parse bookmark file');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    importMutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-3xl">
      {/* File Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : file
            ? 'border-green-500 bg-green-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${importMutation.isPending ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      >
        {!file ? (
          <>
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-sm font-medium text-gray-700 mb-2">
              Drop your bookmark file here, or click to browse
            </p>
            <p className="text-xs text-gray-500">Supports Chrome and Firefox HTML bookmarks (Max 10MB)</p>
            <input
              type="file"
              accept=".html"
              onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              disabled={importMutation.isPending}
              className="hidden"
              id="file-input"
            />
            <label
              htmlFor="file-input"
              className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 cursor-pointer transition-colors"
            >
              Select File
            </label>
          </>
        ) : (
          <div className="flex items-center justify-center gap-3">
            <FileText className="h-8 w-8 text-green-600" />
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900">{file.name}</p>
              <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(2)} KB</p>
            </div>
            <button
              type="button"
              onClick={() => {
                setFile(null);
                setPreview([]);
                setError('');
              }}
              disabled={importMutation.isPending}
              className="ml-4 p-1 text-gray-400 hover:text-red-600 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Preview */}
      {preview.length > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-sm font-medium text-gray-700 mb-2">
            Preview ({preview.length} of {preview.length}+ bookmarks):
          </p>
          <ul className="text-xs text-gray-600 space-y-1 max-h-40 overflow-y-auto">
            {preview.map((bookmark, idx) => (
              <li key={idx} className="truncate">
                <span className="font-medium">{bookmark.title || 'Untitled'}:</span>{' '}
                <span className="text-blue-600">{bookmark.url}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <FormToggle
        label="Auto-start Processing Workflow"
        name="autoStart"
        checked={autoStart}
        onChange={setAutoStart}
        disabled={importMutation.isPending}
        helperText="Automatically start parsing, AI processing, and Notion export for all bookmarks"
      />

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <div>
            <p className="text-sm font-medium text-green-900">File uploaded successfully!</p>
            <p className="text-sm text-green-700">Redirecting to Tasks page...</p>
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={importMutation.isPending || success || !file}
          className="px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {importMutation.isPending && <Loader className="h-5 w-5 animate-spin" />}
          {importMutation.isPending ? 'Uploading...' : 'Upload & Import'}
        </button>

        {!success && file && (
          <button
            type="button"
            onClick={() => {
              setFile(null);
              setPreview([]);
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
