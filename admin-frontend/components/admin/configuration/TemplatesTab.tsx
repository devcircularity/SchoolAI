// app/admin/configuration/components/TemplatesTab.tsx
import { useState } from "react";
import { Plus, Search, Edit, Trash2, Eye } from "lucide-react";
import { intentConfigService, PromptTemplate, IntentConfigVersion } from "@/services/intentConfig";
import Button from "@/components/ui/Button";
import DataTable, { TableColumn, TableAction } from "@/components/ui/DataTable";
import TemplateEditModal from "./TemplateEditModal";

interface EditingItem {
  type: 'pattern' | 'template';
  item: any;
  isNew?: boolean;
}

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

interface TemplatesTabProps {
  templates: PromptTemplate[];
  loading: boolean;
  selectedVersion: string;
  setSelectedVersion: (version: string) => void;
  overview: ConfigOverview | null;
  availableHandlers: string[];
  availableIntents: string[];
  editingItem: EditingItem | null;
  setEditingItem: (item: EditingItem | null) => void;
  onSaveItem: () => void;
  onDataChange: () => void;
}

export default function TemplatesTab({
  templates,
  loading,
  selectedVersion,
  setSelectedVersion,
  overview,
  availableHandlers,
  availableIntents,
  editingItem,
  setEditingItem,
  onSaveItem,
  onDataChange
}: TemplatesTabProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterHandler, setFilterHandler] = useState<string>('');
  const [filterIntent, setFilterIntent] = useState<string>('');

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = !searchTerm || 
      template.template_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.handler.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (template.intent && template.intent.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesHandler = !filterHandler || template.handler === filterHandler;
    const matchesIntent = !filterIntent || template.intent === filterIntent;
    
    return matchesSearch && matchesHandler && matchesIntent;
  });

  const handleAddTemplate = () => {
    setEditingItem({
      type: 'template',
      item: {
        id: '',
        handler: '',
        intent: '',
        template_type: 'user',
        template_text: '',
        enabled: true,
        created_at: '',
        updated_at: ''
      } as PromptTemplate,
      isNew: true
    });
  };

  const handleDeleteTemplate = async (template: PromptTemplate) => {
    if (confirm('Are you sure you want to delete this template?')) {
      try {
        await intentConfigService.deleteTemplate(template.id);
        onDataChange();
      } catch (error) {
        console.error('Failed to delete template:', error);
        alert('Failed to delete template');
      }
    }
  };

  const templateColumns: TableColumn<PromptTemplate>[] = [
    {
      key: 'handler',
      label: 'Handler',
      render: (handler: string) => (
        <code className="text-xs sm:text-sm bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
          {handler}
        </code>
      ),
      width: '150px',
    },
    {
      key: 'intent',
      label: 'Intent',
      render: (intent: string) => (
        <span className="text-xs sm:text-sm">{intent || '-'}</span>
      ),
      width: '120px',
    },
    {
      key: 'template_type',
      label: 'Type',
      render: (type: string) => (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-800">
          {type}
        </span>
      ),
      width: '100px',
    },
    {
      key: 'template_text',
      label: 'Template',
      render: (text: string) => (
        <div className="max-w-xs sm:max-w-md text-xs sm:text-sm">
          <div className="truncate" title={text}>{text}</div>
        </div>
      ),
    },
    {
      key: 'enabled',
      label: 'Status',
      render: (enabled: boolean) => (
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
          enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {enabled ? 'Enabled' : 'Disabled'}
        </span>
      ),
      width: '80px',
    },
  ];

  const templateActions: TableAction<PromptTemplate>[] = [
    {
      label: 'View',
      icon: <Eye size={14} />,
      onClick: (item) => setEditingItem({ type: 'template', item, isNew: false }),
      variant: 'secondary',
    },
    {
      label: 'Edit',
      icon: <Edit size={14} />,
      onClick: (item) => setEditingItem({ type: 'template', item, isNew: false }),
      variant: 'primary',
    },
    {
      label: 'Delete',
      icon: <Trash2 size={14} />,
      onClick: handleDeleteTemplate,
      variant: 'danger',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Version Selector and Filters - Mobile responsive */}
      <div className="card p-3 sm:p-4">
        <div className="flex flex-col lg:flex-row lg:flex-wrap gap-3 lg:gap-4 lg:items-center">
          <div className="min-w-0">
            <label className="block text-xs sm:text-sm font-medium mb-1">Configuration Version</label>
            <select
              value={selectedVersion}
              onChange={(e) => setSelectedVersion(e.target.value)}
              className="input w-full sm:w-48 text-sm"
            >
              {overview?.activeVersion && (
                <option value={overview.activeVersion.id}>
                  {overview.activeVersion.name} (Active)
                </option>
              )}
              {overview?.candidateVersion && (
                <option value={overview.candidateVersion.id}>
                  {overview.candidateVersion.name} (Candidate)
                </option>
              )}
            </select>
          </div>
          
          <div className="min-w-0">
            <label className="block text-xs sm:text-sm font-medium mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400" size={16} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search templates..."
                className="input pl-10 w-full sm:w-64 text-sm"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-3 lg:flex lg:gap-4">
            <div className="min-w-0">
              <label className="block text-xs sm:text-sm font-medium mb-1">Handler</label>
              <select
                value={filterHandler}
                onChange={(e) => setFilterHandler(e.target.value)}
                className="input w-full sm:w-40 text-sm"
              >
                <option value="">All Handlers</option>
                {availableHandlers.map(handler => (
                  <option key={handler} value={handler}>{handler}</option>
                ))}
              </select>
            </div>
            
            <div className="min-w-0">
              <label className="block text-xs sm:text-sm font-medium mb-1">Intent</label>
              <select
                value={filterIntent}
                onChange={(e) => setFilterIntent(e.target.value)}
                className="input w-full sm:w-40 text-sm"
              >
                <option value="">All Intents</option>
                {availableIntents.map(intent => (
                  <option key={intent} value={intent}>{intent}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="lg:ml-auto">
            <Button 
              onClick={handleAddTemplate}
              className="flex items-center gap-2 w-full sm:w-auto text-sm"
            >
              <Plus size={16} />
              Add Template
            </Button>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <DataTable
        data={filteredTemplates}
        columns={templateColumns}
        actions={templateActions}
        loading={loading}
        emptyMessage="No templates found"
        className="overflow-x-auto"
      />

      {/* Edit Modal */}
      {editingItem && editingItem.type === 'template' && (
        <TemplateEditModal
          item={editingItem}
          availableHandlers={availableHandlers}
          availableIntents={availableIntents}
          onSave={onSaveItem}
          onClose={() => setEditingItem(null)}
          onChange={setEditingItem}
        />
      )}
    </div>
  );
}