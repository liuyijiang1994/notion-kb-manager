import { useState } from 'react';
import { Link, FileText, Upload } from 'lucide-react';
import { ManualImportForm } from '../components/import/ManualImportForm';
import { BatchImportForm } from '../components/import/BatchImportForm';
import { FileImportForm } from '../components/import/FileImportForm';

export const ImportPage = () => {
  const [activeTab, setActiveTab] = useState<'manual' | 'batch' | 'file'>('manual');

  const tabs = [
    { id: 'manual' as const, label: 'Single URL', icon: Link },
    { id: 'batch' as const, label: 'Batch Import', icon: FileText },
    { id: 'file' as const, label: 'Upload File', icon: Upload },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Import URLs</h1>
      </div>

      <div className="bg-white rounded-lg shadow-md">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'manual' && <ManualImportForm />}
          {activeTab === 'batch' && <BatchImportForm />}
          {activeTab === 'file' && <FileImportForm />}
        </div>
      </div>

      {/* Help text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">Import Methods:</h3>
        <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
          <li>
            <strong>Single URL:</strong> Import one URL at a time with optional metadata
          </li>
          <li>
            <strong>Batch Import:</strong> Import multiple URLs at once (one per line)
          </li>
          <li>
            <strong>Upload File:</strong> Import bookmarks from Chrome or Firefox HTML export
          </li>
        </ul>
      </div>
    </div>
  );
};
