// app/admin/suggestions/page.tsx - Fixed with proper table height and header
"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { HeaderTitleBus } from "@/components/layout/HeaderBar";
import { suggestionsService, Suggestion, SuggestionStats, ActionItem } from "@/services/suggestions";
import { SuggestionsStatsCards } from "@/components/admin/suggestions/SuggestionsStatsCards";
import { SuggestionsFilterBar } from "@/components/admin/suggestions/SuggestionsFilterBar";
import { SuggestionsDataTable } from "@/components/admin/suggestions/SuggestionsDataTable";
import { SuggestionReviewModal } from "@/components/admin/suggestions/SuggestionReviewModal";

interface EnhancedSuggestion extends Suggestion {
  action_items?: ActionItem[];
  admin_analysis?: string;
  implementation_notes?: string;
  original_message?: string;
  assistant_response?: string;
}

export default function AdminSuggestionsPage() {
  const { user } = useAuth();
  const [suggestions, setSuggestions] = useState<EnhancedSuggestion[]>([]);
  const [stats, setStats] = useState<SuggestionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>('pending');
  const [selectedSuggestion, setSelectedSuggestion] = useState<EnhancedSuggestion | null>(null);
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    total: 0,
    hasNext: false
  });

  // Set header title on mount
  useEffect(() => {
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'Tester Suggestions', 
      subtitle: 'Review and manage tester suggestions' 
    });
    
    return () => {
      HeaderTitleBus.send({ type: 'clear' });
    };
  }, []);

  useEffect(() => {
    loadSuggestions();
    loadStats();
  }, [selectedStatus]);

  // Update subtitle with count
  useEffect(() => {
    const statusText = selectedStatus === 'all' ? 'All suggestions' : 
                       selectedStatus === 'pending' ? 'Pending review' :
                       selectedStatus.replace('_', ' ');
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'Tester Suggestions', 
      subtitle: `${statusText} (${suggestions.length} items)` 
    });
  }, [suggestions.length, selectedStatus]);

  const loadSuggestions = async (page = 1) => {
    try {
      setLoading(true);
      const response = await suggestionsService.getSuggestions({
        page,
        limit: 20,
        status: selectedStatus === 'all' ? undefined : selectedStatus,
        pending_only: selectedStatus === 'pending'
      });
      
      setSuggestions(response.suggestions);
      setPagination({
        currentPage: response.page,
        totalPages: Math.ceil(response.total / 20),
        total: response.total,
        hasNext: response.has_next
      });
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await suggestionsService.getSuggestionStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleEnhancedReview = async (suggestionId: string, reviewData: any) => {
    try {
      await suggestionsService.reviewSuggestionEnhanced(suggestionId, reviewData);
      loadSuggestions(pagination.currentPage);
      loadStats();
    } catch (error) {
      console.error('Failed to review suggestion:', error);
      throw error;
    }
  };

  const handleCreateActionItem = async (suggestionId: string, actionItemData: any) => {
    try {
      await suggestionsService.createActionItem(suggestionId, actionItemData);
      loadSuggestions(pagination.currentPage);
      loadStats();
    } catch (error) {
      console.error('Failed to create action item:', error);
      throw error;
    }
  };

  const handleMarkAddressed = async (suggestionId: string, completionNotes: string) => {
    try {
      await suggestionsService.markSuggestionAddressed(suggestionId, completionNotes);
      loadSuggestions(pagination.currentPage);
      loadStats();
    } catch (error) {
      console.error('Failed to mark as addressed:', error);
      throw error;
    }
  };

  // Check permissions
  const hasReviewPermission = user?.permissions?.is_admin || user?.permissions?.is_super_admin;

  if (!hasReviewPermission) {
    return (
      <div className="p-4 sm:p-6">
        <div className="text-center">
          <h1 className="text-xl sm:text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-neutral-600">You don't have permission to review suggestions.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6">
      {/* Stats Cards */}
      <SuggestionsStatsCards stats={stats} loading={loading} />

      {/* Filter Bar */}
      <SuggestionsFilterBar 
        selectedStatus={selectedStatus}
        onStatusChange={setSelectedStatus}
      />

      {/* Data Table - Increased height for better visibility */}
      <div className="h-[calc(100vh-300px)] min-h-[700px]">
        <SuggestionsDataTable
          suggestions={suggestions}
          loading={loading}
          pagination={{
            currentPage: pagination.currentPage,
            totalPages: pagination.totalPages,
            onPageChange: loadSuggestions,
          }}
          onViewSuggestion={setSelectedSuggestion}
        />
      </div>

      {/* Review Modal */}
      {selectedSuggestion && (
        <SuggestionReviewModal
          suggestion={selectedSuggestion}
          onClose={() => setSelectedSuggestion(null)}
          onReview={handleEnhancedReview}
          onCreateActionItem={handleCreateActionItem}
          onMarkAddressed={handleMarkAddressed}
        />
      )}
    </div>
  );
}