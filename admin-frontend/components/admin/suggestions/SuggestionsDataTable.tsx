// components/admin/suggestions/SuggestionsDataTable.tsx - FIXED
import { TableColumn, TableAction } from "@/components/ui/DataTable";
import DataTable from "@/components/ui/DataTable";
import { CheckCircle, Clock, Eye, Lightbulb, Plus, X } from "lucide-react";
import { ActionItem, Suggestion } from "@/services/suggestions";

interface EnhancedSuggestion extends Suggestion {
  action_items?: ActionItem[];
  admin_analysis?: string;
  implementation_notes?: string;
  original_message?: string;
  assistant_response?: string;
}

interface SuggestionsDataTableProps {
  suggestions: EnhancedSuggestion[];
  loading: boolean;
  pagination: {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
  };
  onViewSuggestion: (suggestion: EnhancedSuggestion) => void;
}

export function SuggestionsDataTable({
  suggestions,
  loading,
  pagination,
  onViewSuggestion
}: SuggestionsDataTableProps) {
  const columns: TableColumn<EnhancedSuggestion>[] = [
    {
      key: 'created_at',
      label: 'Submitted',
      render: (date: string) => (
        <span className="text-xs sm:text-sm">
          {new Date(date).toLocaleDateString()}
        </span>
      ),
      width: '100px',
    },
    {
      key: 'created_by_name',
      label: 'Submitted By',
      render: (name: string) => (
        <span className="text-xs sm:text-sm truncate">{name}</span>
      ),
      width: '150px',
    },
    {
      key: 'suggestion_type',
      label: 'Type',
      render: (type: string) => (
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            type === 'regex_pattern' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200' :
            type === 'prompt_template' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200' :
            type === 'intent_mapping' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200' :
            'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200'
          }`}
        >
          {type.replace('_', ' ')}
        </span>
      ),
      width: '140px',
    },
    {
      key: 'title',
      label: 'Title',
      render: (title: string, suggestion: EnhancedSuggestion) => (
        <div className="max-w-xs">
          <div className="truncate font-medium text-xs sm:text-sm" title={title}>
            {title}
          </div>
          {suggestion.action_items && suggestion.action_items.length > 0 && (
            <div className="flex items-center gap-1 mt-1">
              <Clock size={12} className="text-blue-500" />
              <span className="text-xs text-blue-600">
                {suggestion.action_items.length} action item{suggestion.action_items.length > 1 ? 's' : ''}
              </span>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'priority',
      label: 'Priority',
      render: (priority: string) => (
        <span
          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
            priority === 'critical' ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200' :
            priority === 'high' ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200' :
            priority === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200' :
            'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200'
          }`}
        >
          {priority}
        </span>
      ),
      width: '100px',
    },
    {
      key: 'status',
      label: 'Status',
      render: (status: string) => {
        let statusIcon = null;
        let statusClass = '';
        
        switch (status) {
          case 'approved':
            statusIcon = <CheckCircle size={12} />;
            statusClass = 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200';
            break;
          case 'rejected':
            statusIcon = <X size={12} />;
            statusClass = 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200';
            break;
          case 'implemented':
            statusIcon = <CheckCircle size={12} />;
            statusClass = 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200';
            break;
          case 'needs_analysis':
            statusIcon = <Lightbulb size={12} />;
            statusClass = 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200';
            break;
          default:
            statusIcon = <Clock size={12} />;
            statusClass = 'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200';
        }
        
        return (
          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClass}`}>
            {statusIcon}
            {status.replace('_', ' ')}
          </span>
        );
      },
      width: '120px',
    },
  ];

  const actions: TableAction<EnhancedSuggestion>[] = [
    {
      label: 'Review',
      icon: <Eye size={14} />,
      onClick: onViewSuggestion,
      variant: 'primary',
    },
    {
      label: 'Actions',
      icon: <Plus size={14} />,
      onClick: onViewSuggestion,
      variant: 'secondary',
      disabled: (suggestion) => suggestion.status !== 'approved',
    },
  ];

  return (
    <DataTable
      data={suggestions}
      columns={columns}
      actions={actions}
      loading={loading}
      searchable
      searchPlaceholder="Search suggestions..."
      pagination={pagination}
      emptyMessage="No suggestions found"
      className="text-xs sm:text-sm"
    />
  );
}