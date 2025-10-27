// app/admin/intent-config/page.tsx
"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { intentConfigService, IntentConfigVersion, IntentPattern, PromptTemplate } from "@/services/intentConfig";
import DataTable, { TableColumn, TableAction } from "@/components/ui/DataTable";
import { Edit, Plus, Save, X, Play, Archive, RefreshCw, TestTube } from "lucide-react";
import Button from "@/components/ui/Button";

export default function IntentConfigPage() {
  const { user } = useAuth();
  const [versions, setVersions] = useState<IntentConfigVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<IntentConfigVersion | null>(null);
  const [patterns, setPatterns] = useState<IntentPattern[]>([]);
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'versions' | 'patterns' | 'templates' | 'logs' | 'test'>('versions');
  const [editingPattern, setEditingPattern] = useState<IntentPattern | null>(null);
  const [editingTemplate, setEditingTemplate] = useState<PromptTemplate | null>(null);
  const [showCreateVersion, setShowCreateVersion] = useState(false);
  const [showCreatePattern, setShowCreatePattern] = useState(false);
  const [showCreateTemplate, setShowCreateTemplate] = useState(false);

  // Load initial data
  useEffect(() => {
    loadVersions();
  }, []);

  // Load patterns and templates when version is selected
  useEffect(() => {
    if (selectedVersion && activeTab === 'patterns') {
      loadPatterns(selectedVersion.id);
    }
    if (selectedVersion && activeTab === 'templates') {
      loadTemplates(selectedVersion.id);
    }
  }, [selectedVersion, activeTab]);

  const loadVersions = async () => {
    try {
      setLoading(true);
      const data = await intentConfigService.getVersions();
      setVersions(data);
      
      // Auto-select active version
      const activeVersion = data.find(v => v.status === 'active');
      if (activeVersion) {
        setSelectedVersion(activeVersion);
      }
    } catch (error) {
      console.error('Failed to load versions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPatterns = async (versionId: string) => {
    try {
      const data = await intentConfigService.getPatterns(versionId);
      setPatterns(data);
    } catch (error) {
      console.error('Failed to load patterns:', error);
    }
  };

  const loadTemplates = async (versionId: string) => {
    try {
      const data = await intentConfigService.getTemplates(versionId);
      setTemplates(data);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const handlePromoteVersion = async (version: IntentConfigVersion) => {
    if (confirm(`Are you sure you want to promote "${version.name}" to active?`)) {
      try {
        await intentConfigService.promoteVersion(version.id);
        loadVersions();
      } catch (error) {
        console.error('Failed to promote version:', error);
      }
    }
  };

  const handleArchiveVersion = async (version: IntentConfigVersion) => {
    if (confirm(`Are you sure you want to archive "${version.name}"?`)) {
      try {
        await intentConfigService.archiveVersion(version.id);
        loadVersions();
      } catch (error) {
        console.error('Failed to archive version:', error);
      }
    }
  };

  const handleReloadConfig = async () => {
    try {
      await intentConfigService.reloadConfig();
      alert('Configuration cache reloaded successfully');
    } catch (error) {
      console.error('Failed to reload config:', error);
      alert('Failed to reload configuration');
    }
  };

  const versionColumns: TableColumn<IntentConfigVersion>[] = [
    {
      key: 'name',
      label: 'Name',
      sortable: true,
    },
    {
      key: 'status',
      label: 'Status',
      render: (status: string) => (
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            status === 'active' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200' :
            status === 'candidate' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200' :
            'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200'
          }`}
        >
          {status.toUpperCase()}
        </span>
      ),
    },
    {
      key: 'pattern_count',
      label: 'Patterns',
      render: (count: number) => count.toString(),
    },
    {
      key: 'template_count',
      label: 'Templates',
      render: (count: number) => count.toString(),
    },
    {
      key: 'created_at',
      label: 'Created',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
  ];

  const versionActions: TableAction<IntentConfigVersion>[] = [
    {
      label: 'Select',
      icon: <Edit size={14} />,
      onClick: (version) => setSelectedVersion(version),
      variant: 'secondary',
    },
    {
      label: 'Promote',
      icon: <Play size={14} />,
      onClick: handlePromoteVersion,
      variant: 'primary',
      disabled: (version) => version.status === 'active',
    },
    {
      label: 'Archive',
      icon: <Archive size={14} />,
      onClick: handleArchiveVersion,
      variant: 'danger',
      disabled: (version) => version.status === 'active',
    },
  ];

  const patternColumns: TableColumn<IntentPattern>[] = [
    {
      key: 'handler',
      label: 'Handler',
      render: (handler: string) => (
        <code className="text-xs sm:text-sm bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
          {handler}
        </code>
      ),
    },
    {
      key: 'intent',
      label: 'Intent',
    },
    {
      key: 'kind',
      label: 'Kind',
      render: (kind: string) => (
        <span
          className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
            kind === 'positive' ? 'bg-green-100 text-green-800' :
            kind === 'negative' ? 'bg-red-100 text-red-800' :
            'bg-blue-100 text-blue-800'
          }`}
        >
          {kind}
        </span>
      ),
    },
    {
      key: 'pattern',
      label: 'Pattern',
      render: (pattern: string) => (
        <code className="text-xs max-w-xs truncate block">{pattern}</code>
      ),
    },
    {
      key: 'priority',
      label: 'Priority',
    },
    {
      key: 'enabled',
      label: 'Enabled',
      render: (enabled: boolean) => enabled ? '✅' : '❌',
    },
  ];

  const patternActions: TableAction<IntentPattern>[] = [
    {
      label: 'Edit',
      icon: <Edit size={14} />,
      onClick: (pattern) => setEditingPattern(pattern),
      variant: 'secondary',
    },
    {
      label: 'Delete',
      icon: <X size={14} />,
      onClick: async (pattern) => {
        if (confirm('Are you sure you want to delete this pattern?')) {
          try {
            await intentConfigService.deletePattern(pattern.id);
            if (selectedVersion) loadPatterns(selectedVersion.id);
          } catch (error) {
            console.error('Failed to delete pattern:', error);
          }
        }
      },
      variant: 'danger',
    },
  ];

  // Check permissions directly instead of using canManageIntentConfig to avoid type issues
  const hasIntentConfigPermission = user?.permissions?.can_manage_intent_config || 
                                   user?.permissions?.is_admin || 
                                   user?.permissions?.is_super_admin;

  if (!hasIntentConfigPermission) {
    return (
      <div className="p-4 sm:p-6">
        <div className="text-center">
          <h1 className="text-xl sm:text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-neutral-600">You don't have permission to manage intent configuration.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6">
      {/* Header - Mobile responsive */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 sm:mb-6 gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold mb-2">Intent Configuration</h1>
          <p className="text-sm sm:text-base text-neutral-600">
            Manage AI intent patterns and response templates
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={handleReloadConfig}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <RefreshCw size={16} />
            <span className="hidden sm:inline">Reload Cache</span>
            <span className="sm:hidden">Reload</span>
          </Button>
          <Button 
            onClick={() => setShowCreateVersion(true)}
            className="flex items-center gap-2 text-sm"
          >
            <Plus size={16} />
            <span className="hidden sm:inline">New Version</span>
            <span className="sm:hidden">New</span>
          </Button>
        </div>
      </div>

      {/* Tabs - Mobile responsive */}
      <div className="border-b border-neutral-200 dark:border-neutral-700 mb-4 sm:mb-6">
        <nav className="flex space-x-4 sm:space-x-8 overflow-x-auto">
          {['versions', 'patterns', 'templates', 'logs', 'test'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`py-2 px-1 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap ${
                activeTab === tab
                  ? 'border-[--color-brand] text-[--color-brand]'
                  : 'border-transparent text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Selected Version Info */}
      {selectedVersion && activeTab !== 'versions' && (
        <div className="card p-3 sm:p-4 mb-4 sm:mb-6">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div>
              <h3 className="font-semibold text-sm sm:text-base">Working with: {selectedVersion.name}</h3>
              <p className="text-xs sm:text-sm text-neutral-600">
                Status: {selectedVersion.status} | 
                {selectedVersion.pattern_count} patterns, {selectedVersion.template_count} templates
              </p>
            </div>
            <Button 
              onClick={() => setActiveTab('versions')} 
              className="btn-secondary text-sm"
            >
              Change Version
            </Button>
          </div>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'versions' && (
        <DataTable
          data={versions}
          columns={versionColumns}
          actions={versionActions}
          loading={loading}
          searchable
          searchPlaceholder="Search versions..."
          emptyMessage="No configuration versions found"
        />
      )}

      {activeTab === 'patterns' && selectedVersion && (
        <div>
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 gap-3">
            <h3 className="text-base sm:text-lg font-semibold">Patterns</h3>
            <Button 
              onClick={() => setShowCreatePattern(true)}
              className="flex items-center gap-2 text-sm"
            >
              <Plus size={16} />
              Add Pattern
            </Button>
          </div>
          <DataTable
            data={patterns}
            columns={patternColumns}
            actions={patternActions}
            loading={loading}
            searchable
            searchPlaceholder="Search patterns..."
            emptyMessage="No patterns found"
          />
        </div>
      )}

      {activeTab === 'templates' && selectedVersion && (
        <div>
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 gap-3">
            <h3 className="text-base sm:text-lg font-semibold">Templates</h3>
            <Button 
              onClick={() => setShowCreateTemplate(true)}
              className="flex items-center gap-2 text-sm"
            >
              <Plus size={16} />
              Add Template
            </Button>
          </div>
          <DataTable
            data={templates}
            columns={[
              {
                key: 'handler',
                label: 'Handler',
                render: (handler: string) => (
                  <code className="text-xs sm:text-sm bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                    {handler}
                  </code>
                ),
              },
              {
                key: 'intent',
                label: 'Intent',
                render: (intent: string) => intent || '-',
              },
              {
                key: 'template_type',
                label: 'Type',
                render: (type: string) => (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-800">
                    {type}
                  </span>
                ),
              },
              {
                key: 'template_text',
                label: 'Template',
                render: (text: string) => (
                  <div className="max-w-xs sm:max-w-md truncate text-xs sm:text-sm">{text}</div>
                ),
              },
              {
                key: 'enabled',
                label: 'Enabled',
                render: (enabled: boolean) => enabled ? '✅' : '❌',
              },
            ]}
            actions={[
              {
                label: 'Edit',
                icon: <Edit size={14} />,
                onClick: (template) => setEditingTemplate(template),
                variant: 'secondary',
              },
              {
                label: 'Delete',
                icon: <X size={14} />,
                onClick: async (template) => {
                  if (confirm('Are you sure you want to delete this template?')) {
                    try {
                      await intentConfigService.deleteTemplate(template.id);
                      if (selectedVersion) loadTemplates(selectedVersion.id);
                    } catch (error) {
                      console.error('Failed to delete template:', error);
                    }
                  }
                },
                variant: 'danger',
              },
            ]}
            loading={loading}
            searchable
            searchPlaceholder="Search templates..."
            emptyMessage="No templates found"
          />
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="card p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">Routing Logs</h3>
          <p className="text-sm sm:text-base text-neutral-600 mb-3 sm:mb-4">
            View routing logs and analytics in the Logs section.
          </p>
          <Button 
            onClick={() => window.location.href = '/admin/logs'}
            className="text-sm"
          >
            View Logs
          </Button>
        </div>
      )}

      {activeTab === 'test' && (
        <div>
          <h3 className="text-base sm:text-lg font-semibold mb-4">Test Classification</h3>
          <TestClassificationPanel />
        </div>
      )}

      {/* Modals would go here - Create Version, Create Pattern, Create Template, Edit forms */}
    </div>
  );
}

// Test Classification Component
function TestClassificationPanel() {
  const [testMessage, setTestMessage] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const handleTest = async () => {
    if (!testMessage.trim()) return;
    
    try {
      setTesting(true);
      const result = await intentConfigService.testClassify({
        message: testMessage,
      });
      setTestResult(result);
    } catch (error) {
      console.error('Test failed:', error);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="label text-sm">Test Message</label>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="Enter a message to test classification..."
            className="input flex-1 text-sm"
          />
          <Button 
            onClick={handleTest}
            disabled={testing || !testMessage.trim()}
            className="flex items-center gap-2 text-sm"
          >
            <TestTube size={16} />
            {testing ? 'Testing...' : 'Test'}
          </Button>
        </div>
      </div>

      {testResult && (
        <div className="card p-3 sm:p-4">
          <h4 className="font-semibold mb-3 text-sm sm:text-base">Classification Result</h4>
          <div className="space-y-3">
            <div>
              <strong className="text-sm">Final Decision:</strong>
              <pre className="mt-1 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs sm:text-sm overflow-auto">
                {JSON.stringify(testResult.final_decision, null, 2)}
              </pre>
            </div>
            
            {testResult.config_router_result && (
              <div>
                <strong className="text-sm">Config Router:</strong>
                <pre className="mt-1 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-xs sm:text-sm overflow-auto">
                  {JSON.stringify(testResult.config_router_result, null, 2)}
                </pre>
              </div>
            )}
            
            {testResult.llm_classifier_result && (
              <div>
                <strong className="text-sm">LLM Classifier:</strong>
                <pre className="mt-1 p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs sm:text-sm overflow-auto">
                  {JSON.stringify(testResult.llm_classifier_result, null, 2)}
                </pre>
              </div>
            )}
            
            <div>
              <strong className="text-sm">Processing Steps:</strong>
              <ul className="mt-1 space-y-1">
                {testResult.processing_steps.map((step: string, index: number) => (
                  <li key={index} className="text-xs sm:text-sm text-neutral-600">
                    {index + 1}. {step}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}