// app/tester/stats/page.tsx
"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { testerService, TesterStats } from "@/services/tester";
import { TrendingUp, TrendingDown, AlertTriangle, Activity, BarChart3, MessageSquare } from "lucide-react";
import Button from "@/components/ui/Button";

export default function TesterStatsPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<TesterStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState<number>(7);
  const [historicalData, setHistoricalData] = useState<any[]>([]);

  useEffect(() => {
    loadStats();
    loadHistoricalData();
  }, [selectedTimeframe]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await testerService.getStats({ days_back: selectedTimeframe });
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadHistoricalData = async () => {
    // This would typically load trend data over time
    // For now, we'll simulate some data
    const data = [];
    for (let i = selectedTimeframe; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      data.push({
        date: date.toLocaleDateString(),
        negative_ratings: Math.floor(Math.random() * 10) + 1,
        fallback_used: Math.floor(Math.random() * 15) + 2,
        low_confidence: Math.floor(Math.random() * 20) + 5,
        total_messages: Math.floor(Math.random() * 100) + 50
      });
    }
    setHistoricalData(data);
  };

  const getPercentage = (value: number, total: number) => {
    return total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
  };

  const getStatusColor = (percentage: number, isGood: boolean = false) => {
    if (isGood) {
      // For good metrics (lower is better)
      if (percentage < 5) return 'text-green-600';
      if (percentage < 10) return 'text-yellow-600';
      return 'text-red-600';
    } else {
      // For neutral metrics
      if (percentage < 5) return 'text-green-600';
      if (percentage < 15) return 'text-yellow-600';
      return 'text-red-600';
    }
  };

  // Check permissions directly instead of using canAccessTesterQueue to avoid type issues
  const hasTesterQueuePermission = user?.permissions?.is_tester || 
                                   user?.permissions?.is_admin || 
                                   user?.permissions?.is_super_admin;

  if (!hasTesterQueuePermission) {
    return (
      <div className="p-4 sm:p-6">
        <div className="text-center">
          <h1 className="text-xl sm:text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-neutral-600">You don't have permission to view tester analytics.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6">
      {/* Header - Mobile responsive */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 sm:mb-6 gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold mb-2">Tester Analytics</h1>
          <p className="text-sm sm:text-base text-neutral-600">
            Detailed analytics and trends for AI response quality
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-4">
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(Number(e.target.value))}
            className="input w-full sm:w-32 text-sm"
          >
            <option value={1}>Last 24h</option>
            <option value={3}>Last 3 days</option>
            <option value={7}>Last week</option>
            <option value={14}>Last 2 weeks</option>
            <option value={30}>Last month</option>
          </select>
          <Button onClick={loadStats} className="btn-secondary text-sm">
            Refresh
          </Button>
        </div>
      </div>

      {stats && (
        <>
          {/* Key Metrics - Mobile responsive grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6 sm:mb-8">
            <div className="card p-4 sm:p-6">
              <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                <MessageSquare className="text-blue-600 flex-shrink-0" size={20} />
                <div className="min-w-0">
                  <h3 className="text-base sm:text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                    Total Messages
                  </h3>
                  <p className="text-xs sm:text-sm text-neutral-500">In {selectedTimeframe} days</p>
                </div>
              </div>
              <p className="text-2xl sm:text-3xl font-bold text-blue-600 mb-2">{stats.total_messages}</p>
              <div className="text-xs sm:text-sm text-neutral-600">
                <span className={getStatusColor(100, false)}>
                  {(stats.total_messages / selectedTimeframe).toFixed(1)} per day avg
                </span>
              </div>
            </div>

            <div className="card p-4 sm:p-6">
              <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                <TrendingDown className="text-red-600 flex-shrink-0" size={20} />
                <div className="min-w-0">
                  <h3 className="text-base sm:text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                    Negative Feedback
                  </h3>
                  <p className="text-xs sm:text-sm text-neutral-500">User thumbs down</p>
                </div>
              </div>
              <p className="text-2xl sm:text-3xl font-bold text-red-600 mb-2">{stats.negative_ratings}</p>
              <div className="text-xs sm:text-sm">
                <span className={getStatusColor(parseFloat(getPercentage(stats.negative_ratings, stats.total_messages)), true)}>
                  {getPercentage(stats.negative_ratings, stats.total_messages)}% of messages
                </span>
              </div>
            </div>

            <div className="card p-4 sm:p-6">
              <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                <Activity className="text-orange-600 flex-shrink-0" size={20} />
                <div className="min-w-0">
                  <h3 className="text-base sm:text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                    Fallback Rate
                  </h3>
                  <p className="text-xs sm:text-sm text-neutral-500">Default responses</p>
                </div>
              </div>
              <p className="text-2xl sm:text-3xl font-bold text-orange-600 mb-2">{stats.fallback_used}</p>
              <div className="text-xs sm:text-sm">
                <span className={getStatusColor(parseFloat(getPercentage(stats.fallback_used, stats.total_messages)), true)}>
                  {getPercentage(stats.fallback_used, stats.total_messages)}% of messages
                </span>
              </div>
            </div>

            <div className="card p-4 sm:p-6">
              <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                <AlertTriangle className="text-yellow-600 flex-shrink-0" size={20} />
                <div className="min-w-0">
                  <h3 className="text-base sm:text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                    Low Confidence
                  </h3>
                  <p className="text-xs sm:text-sm text-neutral-500">Classification issues</p>
                </div>
              </div>
              <p className="text-2xl sm:text-3xl font-bold text-yellow-600 mb-2">{stats.low_confidence}</p>
              <div className="text-xs sm:text-sm">
                <span className={getStatusColor(parseFloat(getPercentage(stats.low_confidence, stats.total_messages)), true)}>
                  {getPercentage(stats.low_confidence, stats.total_messages)}% of messages
                </span>
              </div>
            </div>
          </div>

          {/* Issue Breakdown - Mobile responsive */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
            <div className="card p-4 sm:p-6">
              <h2 className="text-base sm:text-lg font-semibold mb-4 sm:mb-6 text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
                <BarChart3 size={18} />
                Issues by Type
              </h2>
              <div className="space-y-3 sm:space-y-4">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg gap-2">
                  <div className="min-w-0">
                    <span className="font-medium text-red-800 dark:text-red-200 text-sm sm:text-base">Negative Ratings</span>
                    <p className="text-xs sm:text-sm text-red-600 dark:text-red-300">Users gave thumbs down</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xl sm:text-2xl font-bold text-red-600">{stats.by_issue_type.negative_rating}</span>
                    <p className="text-xs sm:text-sm text-red-600">
                      {getPercentage(stats.by_issue_type.negative_rating, stats.needs_attention)}% of issues
                    </p>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg gap-2">
                  <div className="min-w-0">
                    <span className="font-medium text-orange-800 dark:text-orange-200 text-sm sm:text-base">Fallback Used</span>
                    <p className="text-xs sm:text-sm text-orange-600 dark:text-orange-300">Default response triggered</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xl sm:text-2xl font-bold text-orange-600">{stats.by_issue_type.fallback}</span>
                    <p className="text-xs sm:text-sm text-orange-600">
                      {getPercentage(stats.by_issue_type.fallback, stats.needs_attention)}% of issues
                    </p>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg gap-2">
                  <div className="min-w-0">
                    <span className="font-medium text-yellow-800 dark:text-yellow-200 text-sm sm:text-base">Low Confidence</span>
                    <p className="text-xs sm:text-sm text-yellow-600 dark:text-yellow-300">Intent classification unclear</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xl sm:text-2xl font-bold text-yellow-600">{stats.by_issue_type.low_confidence}</span>
                    <p className="text-xs sm:text-sm text-yellow-600">
                      {getPercentage(stats.by_issue_type.low_confidence, stats.needs_attention)}% of issues
                    </p>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg gap-2">
                  <div className="min-w-0">
                    <span className="font-medium text-purple-800 dark:text-purple-200 text-sm sm:text-base">Unhandled</span>
                    <p className="text-xs sm:text-sm text-purple-600 dark:text-purple-300">No appropriate handler found</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xl sm:text-2xl font-bold text-purple-600">{stats.by_issue_type.unhandled}</span>
                    <p className="text-xs sm:text-sm text-purple-600">
                      {getPercentage(stats.by_issue_type.unhandled, stats.needs_attention)}% of issues
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="card p-4 sm:p-6">
              <h2 className="text-base sm:text-lg font-semibold mb-4 sm:mb-6 text-neutral-900 dark:text-neutral-100 flex items-center gap-2">
                <TrendingUp size={18} />
                Priority Distribution
              </h2>
              <div className="space-y-3 sm:space-y-4">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg gap-2">
                  <div className="min-w-0">
                    <span className="font-medium text-red-800 dark:text-red-200 text-sm sm:text-base">High Priority</span>
                    <p className="text-xs sm:text-sm text-red-600 dark:text-red-300">Needs immediate attention</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xl sm:text-2xl font-bold text-red-600">{stats.by_priority.high}</span>
                    <p className="text-xs sm:text-sm text-red-600">
                      {getPercentage(stats.by_priority.high, stats.needs_attention)}% of queue
                    </p>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg gap-2">
                  <div className="min-w-0">
                    <span className="font-medium text-yellow-800 dark:text-yellow-200 text-sm sm:text-base">Medium Priority</span>
                    <p className="text-xs sm:text-sm text-yellow-600 dark:text-yellow-300">Should be addressed soon</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xl sm:text-2xl font-bold text-yellow-600">{stats.by_priority.medium}</span>
                    <p className="text-xs sm:text-sm text-yellow-600">
                      {getPercentage(stats.by_priority.medium, stats.needs_attention)}% of queue
                    </p>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-3 bg-gray-50 dark:bg-gray-900/20 rounded-lg gap-2">
                  <div className="min-w-0">
                    <span className="font-medium text-gray-800 dark:text-gray-200 text-sm sm:text-base">Low Priority</span>
                    <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300">Minor improvements</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xl sm:text-2xl font-bold text-gray-600">{stats.by_priority.low}</span>
                    <p className="text-xs sm:text-sm text-gray-600">
                      {getPercentage(stats.by_priority.low, stats.needs_attention)}% of queue
                    </p>
                  </div>
                </div>
              </div>

              {/* Overall Health Score */}
              <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-2 text-sm sm:text-base">System Health Score</h3>
                <div className="flex items-center gap-2">
                  {(() => {
                    const problemRate = (stats.needs_attention / stats.total_messages) * 100;
                    const score = Math.max(0, 100 - problemRate * 2);
                    const color = score >= 80 ? 'text-green-600' : score >= 60 ? 'text-yellow-600' : 'text-red-600';
                    return (
                      <>
                        <span className={`text-2xl sm:text-3xl font-bold ${color}`}>{score.toFixed(0)}</span>
                        <span className="text-blue-700 dark:text-blue-300 text-sm sm:text-base">/ 100</span>
                      </>
                    );
                  })()}
                </div>
                <p className="text-xs sm:text-sm text-blue-700 dark:text-blue-300 mt-1">
                  Based on error rates and user feedback
                </p>
              </div>
            </div>
          </div>

          {/* Trends - Mobile responsive table */}
          <div className="card p-4 sm:p-6 mb-6 sm:mb-8">
            <h2 className="text-base sm:text-lg font-semibold mb-4 sm:mb-6 text-neutral-900 dark:text-neutral-100">
              Trends Over Time
            </h2>
            <div className="overflow-x-auto">
              <div className="min-w-full">
                <div className="flex justify-between text-xs sm:text-sm font-medium text-neutral-600 dark:text-neutral-400 pb-2 border-b border-neutral-200 dark:border-neutral-700">
                  <span className="min-w-0 flex-1">Date</span>
                  <span className="min-w-0 flex-1 text-center">Messages</span>
                  <span className="min-w-0 flex-1 text-center">Issues</span>
                  <span className="min-w-0 flex-1 text-right">Issue Rate</span>
                </div>
                {historicalData.slice(-7).map((day, index) => {
                  const issues = day.negative_ratings + day.fallback_used + day.low_confidence;
                  const issueRate = (issues / day.total_messages) * 100;
                  return (
                    <div key={index} className="flex justify-between items-center py-2 border-b border-neutral-200 dark:border-neutral-700">
                      <span className="text-xs sm:text-sm font-medium min-w-0 flex-1">{day.date}</span>
                      <span className="text-xs sm:text-sm min-w-0 flex-1 text-center">{day.total_messages}</span>
                      <span className="text-xs sm:text-sm min-w-0 flex-1 text-center">{issues}</span>
                      <span className={`text-xs sm:text-sm font-medium min-w-0 flex-1 text-right ${getStatusColor(issueRate, true)}`}>
                        {issueRate.toFixed(1)}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Action Items - Mobile responsive */}
          <div className="card p-4 sm:p-6">
            <h2 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 text-neutral-900 dark:text-neutral-100">
              Recommended Actions
            </h2>
            <div className="space-y-3">
              {stats.by_priority.high > 0 && (
                <div className="flex items-start gap-2 sm:gap-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <AlertTriangle className="text-red-600 mt-0.5 flex-shrink-0" size={16} />
                  <div className="min-w-0">
                    <p className="font-medium text-red-800 dark:text-red-200 text-sm sm:text-base">
                      {stats.by_priority.high} high priority issues need attention
                    </p>
                    <p className="text-xs sm:text-sm text-red-600 dark:text-red-300">
                      Review the problem queue and create suggestions for the most critical issues.
                    </p>
                  </div>
                </div>
              )}
              
              {(stats.by_issue_type.negative_rating / stats.total_messages) > 0.05 && (
                <div className="flex items-start gap-2 sm:gap-3 p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                  <TrendingDown className="text-orange-600 mt-0.5 flex-shrink-0" size={16} />
                  <div className="min-w-0">
                    <p className="font-medium text-orange-800 dark:text-orange-200 text-sm sm:text-base">
                      High negative feedback rate ({getPercentage(stats.by_issue_type.negative_rating, stats.total_messages)}%)
                    </p>
                    <p className="text-xs sm:text-sm text-orange-600 dark:text-orange-300">
                      Focus on improving response quality through better prompt templates.
                    </p>
                  </div>
                </div>
              )}
              
              {(stats.by_issue_type.fallback / stats.total_messages) > 0.1 && (
                <div className="flex items-start gap-2 sm:gap-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                  <Activity className="text-yellow-600 mt-0.5 flex-shrink-0" size={16} />
                  <div className="min-w-0">
                    <p className="font-medium text-yellow-800 dark:text-yellow-200 text-sm sm:text-base">
                      High fallback usage ({getPercentage(stats.by_issue_type.fallback, stats.total_messages)}%)
                    </p>
                    <p className="text-xs sm:text-sm text-yellow-600 dark:text-yellow-300">
                      Consider adding more regex patterns and intent mappings.
                    </p>
                  </div>
                </div>
              )}
              
              {stats.by_priority.high === 0 && stats.negative_ratings < 5 && (
                <div className="flex items-start gap-2 sm:gap-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <TrendingUp className="text-green-600 mt-0.5 flex-shrink-0" size={16} />
                  <div className="min-w-0">
                    <p className="font-medium text-green-800 dark:text-green-200 text-sm sm:text-base">
                      System is performing well
                    </p>
                    <p className="text-xs sm:text-sm text-green-600 dark:text-green-300">
                      Continue monitoring for new issues and opportunities for improvement.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}