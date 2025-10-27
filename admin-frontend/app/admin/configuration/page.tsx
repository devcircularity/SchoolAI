// app/admin/configuration/page.tsx - Complete configuration page
"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { HeaderTitleBus } from "@/components/layout/HeaderBar";
import { intentConfigService, IntentConfigVersion } from "@/services/intentConfig";
import { RefreshCw, Plus, Play, Archive } from "lucide-react";
import Button from "@/components/ui/Button";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ConfigurationOverview from "@/components/admin/configuration/ConfigurationOverview";
import ConfigurationTabs from "@/components/admin/configuration/ConfigurationTabs";
import SystemHealthAlert from "@/components/admin/configuration/SystemHealthAlert";
import ImplementationTab from "@/components/admin/configuration/ImplementationTab";
import DataTable, { TableColumn, TableAction } from "@/components/ui/DataTable";

interface ConfigOverview {
  activeVersion: IntentConfigVersion | null;
  candidateVersion: IntentConfigVersion | null;
  totalPatterns: number;
  totalTemplates: number;
  enabledPatterns: number;
  enabledTemplates: number;
  systemHealth: 'healthy' | 'warning' | 'error';
  cacheStatus: 'loaded' | 'loading' | 'error';
}

export default function ConfigurationPage() {
  const { user } = useAuth();
  const [overview, setOverview] = useState<ConfigOverview | null>(null);
  const [versions, setVersions] = useState<IntentConfigVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'versions' | 'patterns' | 'templates' | 'analytics' | 'test' | 'implementation'>('overview');
  const [showCreateVersion, setShowCreateVersion] = useState(false);

  useEffect(() => {
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'Configuration Management',
      subtitle: 'Manage AI intent patterns, templates, and system configuration' 
    });
    
    return () => HeaderTitleBus.send({ type: 'clear' });
  }, []);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    
    if (tabParam && ['overview', 'versions', 'patterns', 'templates', 'analytics', 'test', 'implementation'].includes(tabParam)) {
      setActiveTab(tabParam as any);
    }
  }, []);

  useEffect(() => {
    loadConfigurationData();
  }, []);

  const loadConfigurationData = async () => {
    try {
      setLoading(true);
      const [versionsData, stats, health] = await Promise.all([
        intentConfigService.getVersions(),
        intentConfigService.getStats(),
        intentConfigService.getCacheStats().catch(() => ({ status: 'error' }))
      ]);

      setVersions(versionsData);
      const activeVersion = versionsData.find(v => v.status === 'active') || null;
      const candidateVersion = versionsData.find(v => v.status === 'candidate') || null;

      setOverview({
        activeVersion,
        candidateVersion,
        totalPatterns: stats.patterns?.total || 0,
        totalTemplates: stats.templates?.total || 0,
        enabledPatterns: stats.patterns?.enabled || 0,
        enabledTemplates: stats.templates?.enabled || 0,
        systemHealth: health.status === 'loaded' ? 'healthy' : 'warning',
        cacheStatus: health.status || 'error'
      });
    } catch (error) {
      console.error('Failed to load configuration data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tab: string) => {
    setActiveTab(tab as any);
    
    const newUrl = new URL(window.location.href);
    newUrl.searchParams.set('tab', tab);
    window.history.pushState({}, '', newUrl.toString());
  };

  const handleReloadCache = async () => {
    try {
      await intentConfigService.reloadConfig();
      alert('Configuration cache reloaded successfully');
      loadConfigurationData();
    } catch (error) {
      console.error('Failed to reload cache:', error);
      alert('Failed to reload configuration');
    }
  };

  const handlePromoteVersion = async (version: IntentConfigVersion) => {
    if (confirm(`Are you sure you want to promote "${version.name}" to active?`)) {
      try {
        await intentConfigService.promoteVersion(version.id);
        loadConfigurationData();
      } catch (error) {
        console.error('Failed to promote version:', error);
        alert('Failed to promote version');
      }
    }
  };

  const handleArchiveVersion = async (version: IntentConfigVersion) => {
    if (confirm(`Are you sure you want to archive "${version.name}"?`)) {
      try {
        await intentConfigService.archiveVersion(version.id);
        loadConfigurationData();
      } catch (error) {
        console.error('Failed to archive version:', error);
        alert('Failed to archive version');
      }
    }
  };

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

  if (loading) {
    return <LoadingSpinner size="lg" text="Loading configuration..." />;
  }

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

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Fixed Header */}
      <div className="flex-shrink-0 p-4 sm:p-6 border-b border-neutral-200 dark:border-neutral-700">
        <div className="flex justify-end items-center mb-4 gap-2">
          <Button 
            onClick={handleReloadCache}
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

        {overview && overview.systemHealth !== 'healthy' && (
          <div className="mb-4">
            <SystemHealthAlert cacheStatus={overview.cacheStatus} />
          </div>
        )}

        <div className="border-b border-neutral-200 dark:border-neutral-700">
          <nav className="flex space-x-4 sm:space-x-8 overflow-x-auto">
            {['overview', 'versions', 'patterns', 'templates', 'implementation', 'test', 'analytics'].map((tab) => (
              <button
                key={tab}
                onClick={() => handleTabChange(tab)}
                className={`py-2 px-1 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap ${
                  activeTab === tab
                    ? 'border-[--color-brand] text-[--color-brand]'
                    : 'border-transparent text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300'
                }`}
              >
                {tab === 'implementation' ? 'Implementation' : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {activeTab === 'overview' && overview && (
          <div className="p-4 sm:p-6 h-full overflow-auto">
            <ConfigurationOverview overview={overview} />
          </div>
        )}

        {activeTab === 'versions' && (
          <div className="p-4 sm:p-6 h-full flex flex-col overflow-hidden">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 gap-3 flex-shrink-0">
              <h3 className="text-base sm:text-lg font-semibold">Configuration Versions</h3>
              <Button 
                onClick={() => setShowCreateVersion(true)}
                className="flex items-center gap-2 text-sm"
              >
                <Plus size={16} />
                New Version
              </Button>
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">
              <DataTable
                data={versions}
                columns={versionColumns}
                actions={versionActions}
                loading={loading}
                searchable
                searchPlaceholder="Search versions..."
                emptyMessage="No configuration versions found"
                className="h-full"
              />
            </div>
          </div>
        )}

        {activeTab === 'implementation' && (
          <div className="h-full overflow-hidden">
            <ImplementationTab />
          </div>
        )}

        {(activeTab === 'patterns' || activeTab === 'templates' || activeTab === 'analytics' || activeTab === 'test') && (
          <div className="h-full overflow-hidden">
            <ConfigurationTabs 
              activeTab={activeTab}
              overview={overview}
              onOverviewRefresh={loadConfigurationData}
            />
          </div>
        )}
      </div>

      {/* Create Version Modal */}
      {showCreateVersion && (
        <CreateVersionModal
          onSave={async (versionData) => {
            try {
              await intentConfigService.createVersion(versionData);
              setShowCreateVersion(false);
              loadConfigurationData();
            } catch (error) {
              console.error('Failed to create version:', error);
              alert('Failed to create version');
            }
          }}
          onClose={() => setShowCreateVersion(false)}
        />
      )}
    </div>
  );
}

function CreateVersionModal({ 
  onSave, 
  onClose 
}: { 
  onSave: (versionData: any) => void; 
  onClose: () => void; 
}) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: 'candidate'
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full">
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">Create New Version</h2>
          
          <div className="space-y-4">
            <div>
              <label className="label text-sm">Version Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., v2.1.0"
                className="input text-sm"
                required
              />
            </div>
            
            <div>
              <label className="label text-sm">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe the changes in this version..."
                className="input text-sm"
                rows={3}
              />
            </div>
            
            <div>
              <label className="label text-sm">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                className="input text-sm"
              >
                <option value="candidate">Candidate</option>
                <option value="active">Active</option>
              </select>
            </div>
          </div>
          
          <div className="flex gap-3 mt-6">
            <Button 
              onClick={() => onSave(formData)}
              className="flex-1 text-sm"
              disabled={!formData.name}
            >
              Create Version
            </Button>
            <Button 
              onClick={onClose}
              className="btn-secondary flex-1 text-sm"
            >
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}