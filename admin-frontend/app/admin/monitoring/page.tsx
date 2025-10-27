// app/admin/monitoring/page.tsx - Chat monitoring with chat-bubble style context
"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { HeaderTitleBus } from "@/components/layout/HeaderBar";
import { chatMonitoringService, ChatMessage } from "@/services/chatMonitoring";
import DataTable, { TableColumn, TableAction } from "@/components/ui/DataTable";
import { Eye, X, RefreshCw, User, Bot } from "lucide-react";
import Button from "@/components/ui/Button";

// Extended interface to include school_name and conversation details
interface ExtendedChatMessage extends ChatMessage {
  school_name?: string;
  userFullName?: string;
  conversationTitle?: string;
}

interface ConversationContext {
  userMessage: string | null;
  assistantMessage: string;
  messageDetails: ExtendedChatMessage;
}

export default function ChatMonitoringPage() {
  const { user } = useAuth();
  const [recentMessages, setRecentMessages] = useState<ExtendedChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedContext, setSelectedContext] = useState<ConversationContext | null>(null);
  const [timeRange, setTimeRange] = useState<number>(720);

  // Set page title in header
  useEffect(() => {
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'Chat Monitoring',
      subtitle: 'Real-time monitoring of all chat interactions' 
    });
    
    return () => HeaderTitleBus.send({ type: 'clear' });
  }, []);

  useEffect(() => {
    loadData();
  }, [timeRange]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(loadData, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, timeRange]);

  const loadData = async () => {
    try {
      setLoading(true);
      const messages = await chatMonitoringService.getRecentMessages({
        limit: 50,
        hours_back: timeRange
      });
      setRecentMessages(messages as ExtendedChatMessage[]);
    } catch (error) {
      console.error('Failed to load monitoring data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewConversation = async (message: ExtendedChatMessage) => {
    try {
      const conversation = await chatMonitoringService.getConversationDetails(message.conversation_id);
      
      let userMessage = null;
      const messages = conversation.messages;
      const currentIndex = messages.findIndex(m => m.id === message.id);
      
      if (currentIndex > 0 && messages[currentIndex - 1].message_type === 'user') {
        userMessage = messages[currentIndex - 1].content;
      }
      
      setSelectedContext({
        userMessage,
        assistantMessage: message.content,
        messageDetails: message
      });
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const getTimeRangeLabel = (hours: number) => {
    if (hours <= 24) return 'Last 24 hours';
    if (hours <= 168) return 'Last week';
    if (hours <= 720) return 'Last month';
    if (hours <= 2160) return 'Last 3 months';
    return 'Last year';
  };

  const columns: TableColumn<ExtendedChatMessage>[] = [
    {
      key: 'created_at',
      label: 'Time',
      render: (date: string) => {
        const messageTime = new Date(date);
        const now = new Date();
        const diffMinutes = Math.floor((now.getTime() - messageTime.getTime()) / (1000 * 60));
        
        if (diffMinutes < 1) return <span className="text-xs sm:text-sm">Just now</span>;
        if (diffMinutes < 60) return <span className="text-xs sm:text-sm">{diffMinutes}m ago</span>;
        if (diffMinutes < 1440) return <span className="text-xs sm:text-sm">{Math.floor(diffMinutes / 60)}h ago</span>;
        if (diffMinutes < 10080) return <span className="text-xs sm:text-sm">{Math.floor(diffMinutes / 1440)}d ago</span>;
        return <span className="text-xs sm:text-sm">{messageTime.toLocaleDateString()}</span>;
      },
      width: '100px',
      sortable: true,
    },
    {
      key: 'message_type',
      label: 'Type',
      render: (type: string) => (
        <span
          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
            type === 'user' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200' :
            'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
          }`}
        >
          {type === 'user' ? 'User' : 'Assistant'}
        </span>
      ),
      width: '80px',
    },
    {
      key: 'content',
      label: 'Message',
      render: (content: string) => (
        <div className="max-w-xs sm:max-w-md truncate text-xs sm:text-sm break-words" title={content}>
          {content}
        </div>
      ),
    },
    {
      key: 'intent',
      label: 'Intent',
      render: (intent: string) => intent ? (
        <code className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded break-all">
          {intent}
        </code>
      ) : '-',
      width: '120px',
    },
    {
      key: 'rating',
      label: 'Rating',
      render: (rating: number, message: ExtendedChatMessage) => {
        if (message.message_type === 'user') return <span className="text-xs sm:text-sm">-</span>;
        if (rating === 1) return <span className="text-green-600 text-sm">👍</span>;
        if (rating === -1) return <span className="text-red-600 text-sm">👎</span>;
        return <span className="text-gray-400 text-xs">-</span>;
      },
      width: '60px',
    },
    {
      key: 'processing_time_ms',
      label: 'Response Time',
      render: (time: number) => (
        <span className="text-xs sm:text-sm">
          {time ? `${time}ms` : '-'}
        </span>
      ),
      width: '100px',
    },
    {
      key: 'school_name',
      label: 'School',
      render: (schoolName: string, message: ExtendedChatMessage) => {
        if (schoolName) {
          return (
            <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
              {schoolName}
            </span>
          );
        }
        if (message.school_id) {
          return (
            <code className="text-xs bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">
              {message.school_id.substring(0, 8)}...
            </code>
          );
        }
        return <span className="text-xs text-gray-400">No School</span>;
      },
      width: '120px',
    },
  ];

  const actions: TableAction<ExtendedChatMessage>[] = [
    {
      label: 'View Context',
      icon: <Eye size={14} />,
      onClick: handleViewConversation,
      variant: 'secondary',
    },
  ];

  const hasMonitoringPermission = user?.permissions?.is_admin || 
                                  user?.permissions?.is_super_admin;

  if (!hasMonitoringPermission) {
    return (
      <div className="p-4 sm:p-6">
        <div className="text-center">
          <h1 className="text-xl sm:text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-neutral-600">You don't have permission to view chat monitoring.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 sm:mb-6 gap-4">
        <div className="text-sm text-neutral-600">
          {getTimeRangeLabel(timeRange)} • {recentMessages.length} messages
        </div>
        
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="input text-sm"
          >
            <option value={24}>Last 24 hours</option>
            <option value={168}>Last week</option>
            <option value={720}>Last month</option>
            <option value={2160}>Last 3 months</option>
            <option value={8760}>Last year</option>
          </select>
          
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span className="text-xs sm:text-sm">Auto-refresh</span>
          </label>
          
          <Button onClick={loadData} className="btn-secondary text-sm flex items-center gap-2">
            <RefreshCw size={14} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Messages Table */}
      <div className="h-[800px]">
        <DataTable
          data={recentMessages}
          columns={columns}
          actions={actions}
          loading={loading}
          searchable
          searchPlaceholder="Search messages..."
          emptyMessage="No messages found for the selected time period"
          className="text-xs sm:text-sm"
        />
      </div>

      {/* Chat-Style Context Modal */}
      {selectedContext && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setSelectedContext(null)} />
          <div className="relative bg-neutral-900 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-4 sm:p-6">
              {/* Header */}
              <div className="flex justify-between items-start mb-6">
                <h2 className="text-lg sm:text-xl font-bold text-white">Problem Context</h2>
                <Button 
                  onClick={() => setSelectedContext(null)}
                  className="p-2 hover:bg-neutral-800 rounded-lg transition-colors text-neutral-400 hover:text-white"
                >
                  <X size={16} />
                </Button>
              </div>

              {/* Chat Messages */}
              <div className="space-y-4 mb-6">
                {/* User Message */}
                {selectedContext.userMessage && (
                  <div className="flex justify-end">
                    <div className="flex items-start gap-3 max-w-[80%]">
                      <div className="bg-blue-600 rounded-2xl rounded-tr-sm px-4 py-3">
                        <p className="text-sm text-white whitespace-pre-wrap break-words">
                          {selectedContext.userMessage}
                        </p>
                      </div>
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-green-500 flex items-center justify-center">
                        <User size={20} className="text-white" />
                      </div>
                    </div>
                  </div>
                )}

                {/* Assistant Response */}
                <div className="flex justify-start">
                  <div className="flex items-start gap-3 max-w-[80%]">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-500 flex items-center justify-center">
                      <Bot size={20} className="text-white" />
                    </div>
                    <div className="bg-neutral-800 border border-red-900 rounded-2xl rounded-tl-sm px-4 py-3">
                      <p className="text-sm text-neutral-200 whitespace-pre-wrap break-words">
                        {selectedContext.assistantMessage}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tester's Analysis Section */}
              <div className="border-t border-neutral-700 pt-6">
                <h3 className="text-base font-semibold text-white mb-4">Tester's Analysis</h3>
                <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-neutral-400">Intent:</span>
                      <span className="ml-2 text-white">
                        {selectedContext.messageDetails.intent || 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-neutral-400">School:</span>
                      <span className="ml-2 text-white">
                        {selectedContext.messageDetails.school_name || selectedContext.messageDetails.school_id || 'No School'}
                      </span>
                    </div>
                    <div>
                      <span className="text-neutral-400">Processing Time:</span>
                      <span className="ml-2 text-white">
                        {selectedContext.messageDetails.processing_time_ms ? `${selectedContext.messageDetails.processing_time_ms}ms` : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-neutral-400">Rating:</span>
                      <span className={`ml-2 ${
                        selectedContext.messageDetails.rating === 1 ? 'text-green-400' :
                        selectedContext.messageDetails.rating === -1 ? 'text-red-400' : 'text-neutral-400'
                      }`}>
                        {selectedContext.messageDetails.rating === 1 ? '👍 Positive' :
                         selectedContext.messageDetails.rating === -1 ? '👎 Negative' : 'No rating'}
                      </span>
                    </div>
                    <div>
                      <span className="text-neutral-400">Created:</span>
                      <span className="ml-2 text-white">
                        {new Date(selectedContext.messageDetails.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-neutral-400">Conversation ID:</span>
                      <code className="ml-2 text-xs bg-neutral-700 text-neutral-300 px-2 py-0.5 rounded">
                        {selectedContext.messageDetails.conversation_id.substring(0, 8)}...
                      </code>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}