// app/tester/queue/components/QueueDataTable.tsx - Clean version
import { ProblematicMessage } from "@/services/tester";
import DataTable, { TableColumn, TableAction } from "@/components/ui/DataTable";
import { Eye } from "lucide-react";

interface QueueDataTableProps {
  messages: ProblematicMessage[];
  loading: boolean;
  onViewMessage: (message: ProblematicMessage) => void;
}

export function QueueDataTable({ messages, loading, onViewMessage }: QueueDataTableProps) {
  // Helper functions - Updated for new issue types
  const getPriorityLabel = (priority: number): string => {
    const labels: { [key: number]: string } = { 1: 'High', 2: 'Med', 3: 'Low' };
    return labels[priority] || 'Unknown';
  };

  const getPriorityColor = (priority: number): string => {
    switch (priority) {
      case 1: return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
      case 2: return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200';
      case 3: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
    }
  };

  const getIssueTypeLabel = (issueType: string): string => {
    // Map actual issue types from your backend
    const labels: { [key: string]: string } = {
      // Core issues
      'negative_rating': 'Neg Rating',
      'intent_unhandled': 'Unhandled',
      'intent_unknown': 'Unknown',
      'intent_ollama_fallback': 'Ollama FB',
      'error_intent': 'Error',
      
      // Routing issues
      'fallback_used': 'Fallback',
      'routing_unhandled': 'Route Issue',
      'routing_unknown': 'Route Unknown',
      'routing_ollama_fallback': 'Route FB',
      'no_llm_confidence': 'No LLM Conf',
      
      // Performance
      'slow_response': 'Slow',
      
      // Legacy/fallback
      'fallback': 'Fallback',
      'low_confidence': 'Low Conf',
      'unhandled': 'Unhandled',
      'orphaned_log': 'Orphaned',
      'test_issue_1': 'Test',
      'test_issue_2': 'Test',
      'test_issue_3': 'Test'
    };
    return labels[issueType] || issueType.replace(/_/g, ' ');
  };

  const getIssueTypeColor = (issueType: string): string => {
    switch (issueType) {
      // High priority - Red
      case 'negative_rating':
      case 'error_intent':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
      
      // Unhandled/Unknown - Purple
      case 'intent_unhandled':
      case 'intent_unknown':
      case 'routing_unhandled':
      case 'routing_unknown':
      case 'unhandled':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-200';
      
      // Fallback issues - Orange
      case 'fallback_used':
      case 'intent_ollama_fallback':
      case 'routing_ollama_fallback':
      case 'fallback':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-200';
      
      // Confidence/Performance - Yellow
      case 'no_llm_confidence':
      case 'low_confidence':
      case 'slow_response':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200';
      
      // Test/Debug - Blue
      case 'test_issue_1':
      case 'test_issue_2':
      case 'test_issue_3':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200';
      
      // Orphaned/Other - Gray
      case 'orphaned_log':
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
    }
  };

  const columns: TableColumn<ProblematicMessage>[] = [
    {
      key: 'created_at',
      label: 'Time',
      render: (date: string) => {
        const messageTime = new Date(date);
        const now = new Date();
        const diffMinutes = Math.floor((now.getTime() - messageTime.getTime()) / (1000 * 60));
        
        if (diffMinutes < 1) return <span className="text-xs">Now</span>;
        if (diffMinutes < 60) return <span className="text-xs">{diffMinutes}m</span>;
        if (diffMinutes < 1440) return <span className="text-xs">{Math.floor(diffMinutes / 60)}h</span>;
        return <span className="text-xs">{messageTime.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>;
      },
      width: '70px',
      sortable: true,
    },
    {
      key: 'priority',
      label: 'Priority',
      render: (priority: number) => (
        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${getPriorityColor(priority)}`}>
          {getPriorityLabel(priority)}
        </span>
      ),
      width: '70px',
      sortable: true,
    },
    {
      key: 'issue_type',
      label: 'Issue',
      render: (issueType: string) => (
        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${getIssueTypeColor(issueType)}`}>
          {getIssueTypeLabel(issueType)}
        </span>
      ),
      width: '110px', // Increased width for new issue types
    },
    {
      key: 'user_message',
      label: 'User Message',
      render: (message: string) => (
        <div className="max-w-sm truncate text-xs" title={message}>
          {message}
        </div>
      ),
    },
    {
      key: 'assistant_response',
      label: 'AI Response',
      render: (response: string) => (
        <div className="max-w-sm truncate text-xs" title={response}>
          {response}
        </div>
      ),
    },
    {
      key: 'rating',
      label: 'Score',
      render: (rating: number, row: ProblematicMessage) => (
        <div className="flex flex-col items-center gap-0.5">
          <div>
            {rating === 1 && <span className="text-green-600 text-sm">👍</span>}
            {rating === -1 && <span className="text-red-600 text-sm">👎</span>}
            {!rating && <span className="text-gray-400 text-sm">-</span>}
          </div>
          {row.llm_confidence && (
            <span className={`text-xs ${
              row.llm_confidence >= 0.8 ? 'text-green-600' :
              row.llm_confidence >= 0.6 ? 'text-yellow-600' :
              'text-red-600'
            }`}>
              {(row.llm_confidence * 100).toFixed(0)}%
            </span>
          )}
          {row.fallback_used && (
            <span className="text-xs text-orange-600">FB</span>
          )}
        </div>
      ),
      width: '60px',
    },
  ];

  const actions: TableAction<ProblematicMessage>[] = [
    {
      label: 'View',
      icon: <Eye size={12} />,
      onClick: onViewMessage,
      variant: 'secondary',
    },
  ];

  return (
    <DataTable
      data={messages}
      columns={columns}
      actions={actions}
      loading={loading}
      searchable
      searchPlaceholder="Search messages..."
      emptyMessage="No problematic messages found"
      className="text-xs"
    />
  );
}