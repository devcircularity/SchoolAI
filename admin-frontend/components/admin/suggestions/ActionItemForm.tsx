// components/admin/suggestions/ActionItemForm.tsx
import Button from "@/components/ui/Button";

interface ActionItemFormData {
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  implementation_type: 'pattern' | 'template' | 'code_fix' | 'documentation' | 'other';
  due_date: string;
}

interface ActionItemFormProps {
  formData: ActionItemFormData;
  onFormDataChange: (data: ActionItemFormData) => void;
  onSubmit: () => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export function ActionItemForm({
  formData,
  onFormDataChange,
  onSubmit,
  onCancel,
  isSubmitting = false
}: ActionItemFormProps) {
  const updateField = (field: keyof ActionItemFormData, value: string) => {
    onFormDataChange({
      ...formData,
      [field]: value
    });
  };

  return (
    <div className="border border-neutral-200 dark:border-neutral-700 rounded-lg p-3 sm:p-4 bg-neutral-50 dark:bg-neutral-800/50">
      <h4 className="font-medium mb-3 sm:mb-4 text-sm sm:text-base">Create Action Item</h4>
      <div className="space-y-3 sm:space-y-4">
        <div>
          <label className="block text-xs sm:text-sm font-medium mb-1">Title</label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => updateField('title', e.target.value)}
            placeholder="e.g., Create pattern for class count queries"
            className="w-full p-2 border border-neutral-200 dark:border-neutral-700 rounded text-sm bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 dark:placeholder:text-neutral-500"
          />
        </div>
        
        <div>
          <label className="block text-xs sm:text-sm font-medium mb-1">Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => updateField('description', e.target.value)}
            placeholder="Detailed description of what needs to be done..."
            className="w-full p-2 border border-neutral-200 dark:border-neutral-700 rounded text-sm bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 dark:placeholder:text-neutral-500"
            rows={3}
          />
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1">Priority</label>
            <select
              value={formData.priority}
              onChange={(e) => updateField('priority', e.target.value)}
              className="w-full p-2 border border-neutral-200 dark:border-neutral-700 rounded text-sm bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1">Type</label>
            <select
              value={formData.implementation_type}
              onChange={(e) => updateField('implementation_type', e.target.value)}
              className="w-full p-2 border border-neutral-200 dark:border-neutral-700 rounded text-sm bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100"
            >
              <option value="pattern">Create Pattern</option>
              <option value="template">Create Template</option>
              <option value="code_fix">Code Fix</option>
              <option value="documentation">Documentation</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
        
        <div>
          <label className="block text-xs sm:text-sm font-medium mb-1">Due Date (Optional)</label>
          <input
            type="date"
            value={formData.due_date}
            onChange={(e) => updateField('due_date', e.target.value)}
            className="w-full p-2 border border-neutral-200 dark:border-neutral-700 rounded text-sm bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100"
          />
        </div>
        
        <div className="flex flex-col sm:flex-row gap-2">
          <Button 
            onClick={onSubmit} 
            disabled={!formData.title.trim() || isSubmitting}
            className="flex-1 text-sm"
          >
            {isSubmitting ? 'Creating...' : 'Create Action Item'}
          </Button>
          <Button 
            onClick={onCancel} 
            className="btn-secondary flex-1 text-sm"
            disabled={isSubmitting}
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
}