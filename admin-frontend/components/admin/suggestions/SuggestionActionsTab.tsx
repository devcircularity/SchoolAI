// components/admin/suggestions/SuggestionActionsTab.tsx
import { CheckCircle, Plus } from "lucide-react";
import Button from "@/components/ui/Button";
import { ActionItem } from "@/services/suggestions";
import { ActionItemsList } from "./ActionItemsList";
import { ActionItemForm } from "./ActionItemForm";

interface ActionItemFormData {
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  implementation_type: 'pattern' | 'template' | 'code_fix' | 'documentation' | 'other';
  due_date: string;
}

interface SuggestionActionsTabProps {
  suggestionStatus: string;
  actionItems: ActionItem[];
  showAddAction: boolean;
  newActionItem: ActionItemFormData;
  completionNotes: string;
  onShowAddActionChange: (show: boolean) => void;
  onNewActionItemChange: (data: ActionItemFormData) => void;
  onCompletionNotesChange: (notes: string) => void;
  onAddActionItem: () => void;
  onMarkAddressed: () => void;
  getPriorityColor: (priority: string) => string;
  getTypeColor: (type: string) => string;
}

export function SuggestionActionsTab({
  suggestionStatus,
  actionItems,
  showAddAction,
  newActionItem,
  completionNotes,
  onShowAddActionChange,
  onNewActionItemChange,
  onCompletionNotesChange,
  onAddActionItem,
  onMarkAddressed,
  getPriorityColor,
  getTypeColor
}: SuggestionActionsTabProps) {
  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
        <h3 className="font-semibold text-sm sm:text-base">Action Items</h3>
        {(suggestionStatus === 'pending' || suggestionStatus === 'approved') && (
          <Button
            onClick={() => onShowAddActionChange(true)}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <Plus size={14} />
            Add Action Item
          </Button>
        )}
      </div>

      {/* Action Items List */}
      <ActionItemsList 
        actionItems={actionItems}
        getPriorityColor={getPriorityColor}
        getTypeColor={getTypeColor}
      />

      {/* Add Action Item Form */}
      {showAddAction && (
        <ActionItemForm
          formData={newActionItem}
          onFormDataChange={onNewActionItemChange}
          onSubmit={onAddActionItem}
          onCancel={() => onShowAddActionChange(false)}
        />
      )}

      {/* Mark as Addressed */}
      {suggestionStatus === 'approved' && actionItems.some(item => item.status === 'completed') && (
        <div className="border-t border-neutral-200 dark:border-neutral-700 pt-4">
          <h4 className="font-medium mb-3 text-sm sm:text-base">Mark Suggestion as Addressed</h4>
          <div className="space-y-3">
            <textarea
              value={completionNotes}
              onChange={(e) => onCompletionNotesChange(e.target.value)}
              placeholder="Describe how this suggestion was addressed..."
              className="w-full p-3 border border-neutral-200 dark:border-neutral-700 rounded-lg text-sm bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 dark:placeholder:text-neutral-500"
              rows={3}
            />
            <Button
              onClick={onMarkAddressed}
              disabled={!completionNotes.trim()}
              className="flex items-center gap-2 text-sm"
            >
              <CheckCircle size={16} />
              Mark as Addressed
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}