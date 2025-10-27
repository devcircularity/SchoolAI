// app/tester/page.tsx - Updated with header title management
"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { RouteProtection } from "@/components/auth/RouteProtection";
import { HeaderTitleBus } from "@/components/layout/HeaderBar";
import { testerService, TesterStats } from "@/services/tester";
import { Clock, CheckCircle, XCircle, AlertTriangle, Zap, TrendingUp, Activity, Users, RefreshCw, Info } from "lucide-react";

export default function TesterPage() {
  return (
    <RouteProtection 
      requiredPermissions={["is_tester"]} 
      requiredRoles={["TESTER"]}
      fallbackRoute="/dashboard"
    >
      <TesterDashboard />
    </RouteProtection>
  );
}

function TesterDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState<TesterStats | null>(null);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [queueMessages, setQueueMessages] = useState<any[]>([]);
  const [totalSuggestions, setTotalSuggestions] = useState<number>(0);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingSuggestions, setLoadingSuggestions] = useState(true);
  const [loadingQueue, setLoadingQueue] = useState(true);
  const [suggestionLoadError, setSuggestionLoadError] = useState<string | null>(null);

  // Set header title on mount
  useEffect(() => {
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'Tester Dashboard', 
      subtitle: 'Monitor system performance and track your contributions' 
    });
    
    return () => {
      HeaderTitleBus.send({ type: 'clear' });
    };
  }, []);

  // Update subtitle with suggestion count when data loads
  useEffect(() => {
    if (!loadingSuggestions && totalSuggestions > 0) {
      HeaderTitleBus.send({ 
        type: 'set', 
        title: 'Tester Dashboard', 
        subtitle: `Monitor system performance and track your contributions (${totalSuggestions} suggestions)` 
      });
    }
  }, [loadingSuggestions, totalSuggestions]);

  useEffect(() => {
    loadStats();
    loadSuggestions();
    loadQueue();
  }, []);

  const loadStats = async () => {
    try {
      setLoadingStats(true);
      const data = await testerService.getStats({ days_back: 30 });
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoadingStats(false);
    }
  };

  const loadSuggestions = async () => {
    try {
      setLoadingSuggestions(true);
      setSuggestionLoadError(null);

      // Use the new getAllMySuggestions method to get all suggestions
      console.log('Loading all suggestions for tester dashboard...');
      const data = await testerService.getAllMySuggestions();
      setSuggestions(data);
      setTotalSuggestions(data.length);
      
      console.log(`✓ Successfully loaded ${data.length} suggestions for tester dashboard`);
      
      // Log detailed breakdown for debugging
      const statusBreakdown = data.reduce((acc, s) => {
        acc[s.status] = (acc[s.status] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
      console.log('Suggestion status breakdown:', statusBreakdown);

    } catch (error) {
      console.error('Failed to load suggestions:', error);
      setSuggestionLoadError(error instanceof Error ? error.message : 'Unknown error');
      
      // Fallback: try the old method with higher limit
      try {
        console.log('Falling back to getMySuggestions with high limit...');
        const fallbackData = await testerService.getMySuggestions({ limit: 500 });
        setSuggestions(fallbackData);
        setTotalSuggestions(fallbackData.length);
        console.log(`Fallback successful: loaded ${fallbackData.length} suggestions`);
        setSuggestionLoadError(null);
      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError);
        setSuggestionLoadError('Unable to load suggestions');
      }
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const loadQueue = async () => {
    try {
      setLoadingQueue(true);
      
      const params = {
        days_back: 30,
        limit: 100,
        show_suggested: false
      };
      
      const data = await testerService.getQueue(params);
      
      if (Array.isArray(data)) {
        setQueueMessages(data);
      } else {
        setQueueMessages([]);
      }
    } catch (error) {
      console.error('Failed to load queue:', error);
      setQueueMessages([]);
    } finally {
      setLoadingQueue(false);
    }
  };

  const refreshAll = async () => {
    await Promise.all([loadStats(), loadSuggestions(), loadQueue()]);
  };

  const getSuggestionStatusCounts = () => {
    return {
      total: suggestions.length,
      pending: suggestions.filter(s => s.status === 'pending').length,
      approved: suggestions.filter(s => s.status === 'approved').length,
      rejected: suggestions.filter(s => s.status === 'rejected').length,
      implemented: suggestions.filter(s => s.status === 'implemented').length,
    };
  };

  const getQueueStatsCounts = () => {
    const highPriorityCount = queueMessages.filter(m => m.priority === 1).length;
    
    const negativeRatingCount = queueMessages.filter(m => 
      m.issue_type === 'negative_rating' || m.rating === -1
    ).length;
    
    const fallbackCount = queueMessages.filter(m => 
      m.issue_type === 'fallback_used' || 
      m.issue_type === 'intent_ollama_fallback' ||
      m.issue_type === 'routing_ollama_fallback' ||
      m.fallback_used === true
    ).length;
    
    const lowConfidenceCount = queueMessages.filter(m => 
      m.issue_type === 'no_llm_confidence' ||
      m.issue_type === 'low_confidence' ||
      (m.llm_confidence && m.llm_confidence < 0.6)
    ).length;

    return {
      total: queueMessages.length,
      highPriority: highPriorityCount,
      negativeRating: negativeRatingCount,
      fallback: fallbackCount,
      lowConfidence: lowConfidenceCount
    };
  };

  const suggestionCounts = getSuggestionStatusCounts();
  const queueStats = getQueueStatsCounts();

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 sm:p-6">
        {/* Header with Refresh - Simplified since title is now in HeaderBar */}
        <div className="flex justify-end mb-6">
          <button
            onClick={refreshAll}
            className="btn btn-secondary flex items-center gap-2"
            disabled={loadingStats || loadingSuggestions || loadingQueue}
          >
            <RefreshCw size={16} className={loadingStats || loadingSuggestions || loadingQueue ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>

        {/* Problem Queue Stats */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-2">
            <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              Problem Queue Overview
            </h2>
            <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
              <Info size={14} />
              <span>Total: {queueStats.total} messages in queue</span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6">
            <div className="card p-3 sm:p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="text-red-600 flex-shrink-0" size={16} />
                <h3 className="text-xs sm:text-sm font-medium text-neutral-600">High Priority</h3>
              </div>
              <p className="text-xl sm:text-2xl font-bold text-red-600">
                {loadingQueue ? '...' : queueStats.highPriority}
              </p>
              <p className="text-xs text-neutral-500">Urgent Issues</p>
            </div>

            <div className="card p-3 sm:p-4">
              <div className="flex items-center gap-2 mb-2">
                <XCircle className="text-orange-600 flex-shrink-0" size={16} />
                <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Negative Ratings</h3>
              </div>
              <p className="text-xl sm:text-2xl font-bold text-orange-600">
                {loadingQueue ? '...' : queueStats.negativeRating}
              </p>
              <p className="text-xs text-neutral-500">User Feedback</p>
            </div>

            <div className="card p-3 sm:p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="text-yellow-600 flex-shrink-0" size={16} />
                <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Fallback Used</h3>
              </div>
              <p className="text-xl sm:text-2xl font-bold text-yellow-600">
                {loadingQueue ? '...' : queueStats.fallback}
              </p>
              <p className="text-xs text-neutral-500">System Fallbacks</p>
            </div>

            <div className="card p-3 sm:p-4">
              <div className="flex items-center gap-2 mb-2">
                <Users className="text-purple-600 flex-shrink-0" size={16} />
                <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Low Confidence</h3>
              </div>
              <p className="text-xl sm:text-2xl font-bold text-purple-600">
                {loadingQueue ? '...' : queueStats.lowConfidence}
              </p>
              <p className="text-xs text-neutral-500">AI Uncertainty</p>
            </div>
          </div>
        </div>

        {/* Your Suggestions Stats */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-2">
            <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              Your Suggestions
            </h2>
            <div className="flex items-center gap-2 text-sm">
              {suggestionLoadError ? (
                <div className="flex items-center gap-2 text-red-600">
                  <AlertTriangle size={14} />
                  <span>Error loading: {suggestionLoadError}</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-neutral-600 dark:text-neutral-400">
                  <Info size={14} />
                  <span>Total: {totalSuggestions} suggestions loaded</span>
                </div>
              )}
            </div>
          </div>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
            <div className="card p-3 sm:p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="text-gray-600 flex-shrink-0" size={16} />
                <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Pending</h3>
              </div>
              <p className="text-xl sm:text-2xl font-bold text-gray-600">
                {loadingSuggestions ? '...' : suggestionCounts.pending}
              </p>
              <p className="text-xs text-neutral-500">Under Review</p>
            </div>

            <div className="card p-3 sm:p-4">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="text-green-600 flex-shrink-0" size={16} />
                <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Approved</h3>
              </div>
              <p className="text-xl sm:text-2xl font-bold text-green-600">
                {loadingSuggestions ? '...' : suggestionCounts.approved}
              </p>
              <p className="text-xs text-neutral-500">Ready to Deploy</p>
            </div>

            <div className="card p-3 sm:p-4">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="text-purple-600 flex-shrink-0" size={16} />
                <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Implemented</h3>
              </div>
              <p className="text-xl sm:text-2xl font-bold text-purple-600">
                {loadingSuggestions ? '...' : suggestionCounts.implemented}
              </p>
              <p className="text-xs text-neutral-500">Live in System</p>
            </div>

            <div className="card p-3 sm:p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="text-blue-600 flex-shrink-0" size={16} />
                <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Success Rate</h3>
              </div>
              <p className="text-xl sm:text-2xl font-bold text-blue-600">
                {loadingSuggestions ? '...' : 
                  suggestionCounts.total > 0 ? 
                    `${Math.round(((suggestionCounts.approved + suggestionCounts.implemented) / suggestionCounts.total) * 100)}%` : 
                    '0%'
                }
              </p>
              <p className="text-xs text-neutral-500">Acceptance</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}