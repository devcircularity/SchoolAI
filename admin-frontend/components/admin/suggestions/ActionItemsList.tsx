// components/admin/suggestions/ActionItemsList.tsx
import { AlertCircle, Calendar, Clock } from "lucide-react";
import { ActionItem } from "@/services/suggestions";

interface ActionItemsListProps {
  actionItems: ActionItem[];
  getPriorityColor: (priority: string) => string;
  getTypeColor: (type: string) => string;
}

export function ActionItemsList({ 
  actionItems, 
  getPriorityColor, 
  getTypeColor 
}: ActionItemsListProps) {
  if (actionItems.length === 0) {
    return (
      <div className="text-center py-6 sm:py-8 text-neutral-500">
        <AlertCircle size={24} className="mx-auto mb-2 opacity-50" />
        <p className="text-sm">No action items created yet</p>
        <p className="text-xs mt-1">Create action items to track implementation progress</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {actionItems.map((item) => (
        <div key={item.id} className="border border-neutral-200 rounded-lg p-3 sm:p-4">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-2 gap-2">
            <h4 className="font-medium text-sm sm:text-base">{item.title}</h4>
            <div className="flex flex-wrap gap-2">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(item.priority)}`}>
                {item.priority}
              </span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(item.implementation_type)}`}>
                {item.implementation_type.replace('_', ' ')}
              </span>
            </div>
          </div>
          <p className="text-xs sm:text-sm text-neutral-600 mb-2">{item.description}</p>
          <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-xs text-neutral-500">
            <span className="flex items-center gap-1">
              <Clock size={12} />
              Created {new Date(item.created_at).toLocaleDateString()}
            </span>
            {item.due_date && (
              <span className="flex items-center gap-1">
                <Calendar size={12} />
                Due {new Date(item.due_date).toLocaleDateString()}
              </span>
            )}
            <span className={`px-2 py-1 rounded-full ${
              item.status === 'completed' ? 'bg-green-100 text-green-800' :
              item.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {item.status.replace('_', ' ')}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}