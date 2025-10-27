// app/tester/queue/page.tsx - Simplified without stats cards
"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { testerService, ProblematicMessage } from "@/services/tester";
import { HeaderTitleBus } from "@/components/layout/HeaderBar";
import { apiClient } from "@/services/api";
import { EyeOff } from "lucide-react";

// Import components
import { QueueFilters } from "@/components/tester/queue/QueueFilters";
import { QueueDataTable } from "@/components/tester/queue/QueueDataTable";
import { ConversationModal } from "@/components/tester/queue/ConversationModal";
import { SuggestionModal } from "@/components/tester/queue/SuggestionModal";

export default function TesterQueuePage() {
  const { user } = useAuth();
  
  // Data state
  const [messages, setMessages] = useState<ProblematicMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [queueHidden, setQueueHidden] = useState<boolean>(false);
  
  // Filter state
  const [selectedPriority, setSelectedPriority] = useState<string>('');
  const [selectedIssueType, setSelectedIssueType] = useState<string>('');
  const [selectedTimeframe, setSelectedTimeframe] = useState<number>(30);
  const [showSuggested, setShowSuggested] = useState<boolean>(false);
  
  // Modal state
  const [selectedMessage, setSelectedMessage] = useState<ProblematicMessage | null>(null);
  const [showSuggestionModal, setShowSuggestionModal] = useState(false);

  // Set header title on mount
  useEffect(() => {
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'Problem Queue', 
      subtitle: 'Messages that need tester attention' 
    });
    
    return () => {
      HeaderTitleBus.send({ type: 'clear' });
    };
  }, []);

  // Check queue visibility on mount
  useEffect(() => {
    checkQueueVisibility();
  }, []);

  // Load data when filters change
  useEffect(() => {
    if (!queueHidden) {
      loadQueue();
    }
  }, [selectedPriority, selectedIssueType, selectedTimeframe, showSuggested, queueHidden]);

  // Update subtitle with message count
  useEffect(() => {
    const subtitle = showSuggested 
      ? `All messages (${messages.length} items)` 
      : `Unhandled messages (${messages.length} items)`;
    
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'Problem Queue', 
      subtitle: subtitle
    });
  }, [messages.length, showSuggested]);

  const checkQueueVisibility = async () => {
    try {
      const response = await apiClient.get('/api/admin/configuration/settings/hide-tester-queue');
      setQueueHidden(response.data.hidden);
    } catch (error) {
      console.error('Failed to check queue visibility:', error);
    }
  };

  const loadQueue = async () => {
    try {
      setLoading(true);
      
      const params = {
        days_back: selectedTimeframe,
        limit: 100,
        show_suggested: showSuggested,
        ...(selectedPriority && { priority: parseInt(selectedPriority) }),
        ...(selectedIssueType && { issue_type: selectedIssueType })
      };
      
      const data = await testerService.getQueue(params);
      
      if (Array.isArray(data)) {
        setMessages(data);
      } else {
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to load queue:', error);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewMessage = (message: ProblematicMessage) => {
    setSelectedMessage(message);
  };

  const handleCreateSuggestion = () => {
    setShowSuggestionModal(true);
  };

  const handleSuggestionSubmitted = () => {
    loadQueue();
  };

  const handleSuggestionModalClose = () => {
    setShowSuggestionModal(false);
    setSelectedMessage(null);
  };

  const handleRefresh = () => {
    checkQueueVisibility();
    loadQueue();
  };

  const handleClearFilters = () => {
    setSelectedPriority('');
    setSelectedIssueType('');
    setSelectedTimeframe(30);
    setShowSuggested(false);
  };

  // Check permissions
  const hasTesterQueuePermission = user?.permissions?.is_tester || 
                                   user?.permissions?.is_admin || 
                                   user?.permissions?.is_super_admin;

  const isAdmin = user?.permissions?.is_admin || user?.permissions?.is_super_admin;

  if (!hasTesterQueuePermission) {
    return (
      <div className="p-4 sm:p-6">
        <div className="text-center">
          <h1 className="text-xl sm:text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-neutral-600">You don't have permission to access the tester queue.</p>
        </div>
      </div>
    );
  }

  // Show queue hidden message for non-admin testers
  if (queueHidden && !isAdmin) {
    return (
      <div className="p-4 sm:p-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 text-center max-w-2xl mx-auto mt-12">
          <div className="flex justify-center mb-4">
            <EyeOff size={48} className="text-blue-600" />
          </div>
          <h2 className="text-xl font-semibold mb-2 text-neutral-900 dark:text-neutral-100">
            Queue Temporarily Unavailable
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            The problem queue has been temporarily hidden by an administrator.
            Please check back later or contact an admin for more information.
          </p>
          <button 
            onClick={handleRefresh}
            className="btn btn-primary"
          >
            Check Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6">
      {/* Show notice for admins when queue is hidden */}
      {queueHidden && isAdmin && (
        <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-2">
            <EyeOff size={20} className="text-orange-600" />
            <div>
              <p className="font-medium text-orange-900 dark:text-orange-100">
                Queue Hidden from Testers
              </p>
              <p className="text-sm text-orange-700 dark:text-orange-300">
                You can see this queue because you're an admin. Regular testers cannot access it right now.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filters and Actions */}
      <QueueFilters
        selectedPriority={selectedPriority}
        selectedIssueType={selectedIssueType}
        selectedTimeframe={selectedTimeframe}
        showSuggested={showSuggested}
        onPriorityChange={setSelectedPriority}
        onIssueTypeChange={setSelectedIssueType}
        onTimeframeChange={setSelectedTimeframe}
        onShowSuggestedChange={setShowSuggested}
        onClearFilters={handleClearFilters}
        onRefresh={handleRefresh}
      />

      {/* Data Table - Increased height since stats are removed */}
      <div className="h-[calc(100vh-280px)] min-h-[600px]">
        <QueueDataTable
          messages={messages}
          loading={loading}
          onViewMessage={handleViewMessage}
        />
      </div>

      {/* Conversation Modal */}
      {selectedMessage && !showSuggestionModal && (
        <ConversationModal
          message={selectedMessage}
          onClose={() => setSelectedMessage(null)}
          onCreateSuggestion={handleCreateSuggestion}
        />
      )}

      {/* Suggestion Modal */}
      {showSuggestionModal && selectedMessage && (
        <SuggestionModal
          message={selectedMessage}
          suggestionType="ai_response"
          onClose={handleSuggestionModalClose}
          onSubmit={handleSuggestionSubmitted}
        />
      )}
    </div>
  );
}