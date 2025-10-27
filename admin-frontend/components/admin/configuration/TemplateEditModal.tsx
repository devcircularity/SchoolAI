// app/admin/configuration/components/TemplateEditModal.tsx
import { useState, useEffect } from "react";
import { Save, X } from "lucide-react";
import { intentConfigService, PromptTemplate } from "@/services/intentConfig";
import Button from "@/components/ui/Button";

interface EditingItem {
  type: 'pattern' | 'template';
  item: PromptTemplate;
  isNew?: boolean;
}

interface TemplateEditModalProps {
  item: EditingItem;
  availableHandlers: string[];
  availableIntents: string[];
  onSave: () => void;
  onClose: () => void;
  onChange: (item: EditingItem) => void;
}

export default function TemplateEditModal({
  item,
  availableHandlers,
  availableIntents,
  onSave,
  onClose,
  onChange
}: TemplateEditModalProps) {
  const [loadingIntents, setLoadingIntents] = useState(false);
  const [filteredIntents, setFilteredIntents] = useState<string[]>(availableIntents);

  // Filter intents when handler changes
  useEffect(() => {
    const loadIntentsForHandler = async () => {
      if (item.item.handler) {
        setLoadingIntents(true);
        try {
          const response = await intentConfigService.getAvailableIntents(item.item.handler);
          setFilteredIntents(response.intents);
        } catch (error) {
          console.error('Failed to load intents for handler:', error);
          setFilteredIntents(availableIntents);
        } finally {
          setLoadingIntents(false);
        }
      } else {
        setFilteredIntents(availableIntents);
      }
    };

    loadIntentsForHandler();
  }, [item.item.handler, availableIntents]);

  const updateItem = (field: string, value: any) => {
    onChange({
      ...item,
      item: { ...item.item, [field]: value }
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6">
          <div className="flex justify-between items-start mb-4 sm:mb-6">
            <h2 className="text-lg sm:text-xl font-bold">
              {item.isNew ? 'Add' : 'Edit'} Template
            </h2>
            <Button onClick={onClose} className="text-sm btn-secondary">
              <X size={16} />
            </Button>
          </div>

          <div className="space-y-4 sm:space-y-6">
            {/* Common Fields - Mobile responsive */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="label text-sm">Handler</label>
                <select
                  value={item.item.handler}
                  onChange={(e) => updateItem('handler', e.target.value)}
                  className="input text-sm"
                >
                  <option value="">Select handler...</option>
                  {availableHandlers.map(handler => (
                    <option key={handler} value={handler}>{handler}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="label text-sm">Intent</label>
                <div className="relative">
                  <select
                    value={item.item.intent || ''}
                    onChange={(e) => updateItem('intent', e.target.value)}
                    className="input text-sm"
                    disabled={loadingIntents}
                  >
                    <option value="">
                      {loadingIntents ? 'Loading intents...' : 
                       !item.item.handler ? 'Select handler first...' : 
                       'Select intent...'}
                    </option>
                    {filteredIntents.map(intent => (
                      <option key={intent} value={intent}>{intent}</option>
                    ))}
                  </select>
                  {loadingIntents && (
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    </div>
                  )}
                </div>
                {item.item.handler && filteredIntents.length === 0 && !loadingIntents && (
                  <p className="text-xs text-amber-600 mt-1">
                    No intents found for "{item.item.handler}" handler
                  </p>
                )}
              </div>
            </div>

            {/* Template-specific fields */}
            <div>
              <label className="label text-sm">Template Type</label>
              <select
                value={item.item.template_type}
                onChange={(e) => updateItem('template_type', e.target.value)}
                className="input text-sm"
              >
                <option value="system">System</option>
                <option value="user">User</option>
                <option value="fallback_context">Fallback Context</option>
              </select>
            </div>
            
            <div>
              <label className="label text-sm">Template Text</label>
              <textarea
                value={item.item.template_text}
                onChange={(e) => updateItem('template_text', e.target.value)}
                placeholder="Enter template text..."
                className="input min-h-[200px] text-sm"
                rows={8}
              />
              <p className="text-xs text-neutral-500 mt-1">
                You can use variables like {'{user_message}'}, {'{context}'}, etc.
              </p>
            </div>

            {/* Common enabled checkbox */}
            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={item.item.enabled}
                  onChange={(e) => updateItem('enabled', e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">Enabled</span>
              </label>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3 mt-4 sm:mt-6 pt-4 border-t">
            <Button onClick={onSave} className="flex-1 text-sm">
              <Save size={16} className="mr-2" />
              {item.isNew ? 'Create' : 'Save Changes'}
            </Button>
            <Button onClick={onClose} className="flex-1 text-sm btn-secondary">
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}