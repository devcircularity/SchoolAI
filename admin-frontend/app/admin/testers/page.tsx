// app/admin/testers/page.tsx - Comprehensive tester performance management
"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { HeaderTitleBus } from "@/components/layout/HeaderBar";
import { testerService } from "@/services/tester";
import { testerRankingsService, TesterRanking } from "@/services/testerRankings";
import DataTable, { TableColumn, TableAction } from "@/components/ui/DataTable";
import { Eye, TrendingUp, MessageSquare, CheckCircle, XCircle, Clock, Zap, RefreshCw, Award, Target, Calendar } from "lucide-react";
import Button from "@/components/ui/Button";

interface TesterPerformance extends TesterRanking {
  full_name: string; // Mapped from user_name
  success_rate: number; // Mapped from success_score
  last_activity: string; // Mapped from last_suggestion_date
  average_response_time?: number;
  join_date?: string;
  total_points: number;
  is_active: boolean;
}

export default function TestersPage() {
  const { user } = useAuth();
  const [testers, setTesters] = useState<TesterPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('last_30_days');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedTester, setSelectedTester] = useState<TesterPerformance | null>(null);
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
      title: 'Tester Performance',
      subtitle: 'Comprehensive tester analytics and rankings' 
    });
    
    return () => HeaderTitleBus.send({ type: 'clear' });
  }, []);

  // Update subtitle with filters and count
  useEffect(() => {
    let subtitle = `${testers.length} testers`;
    
    const filters = [];
    if (selectedPeriod !== 'last_30_days') {
      const periodLabels = {
        'last_7_days': '7 days',
        'last_30_days': '30 days', 
        'last_90_days': '90 days',
        'all_time': 'All time'
      };
      filters.push((periodLabels as any)[selectedPeriod]);
    }
    
    if (selectedStatus !== 'all') {
      filters.push(selectedStatus === 'active' ? 'Active only' : 'Inactive only');
    }
    
    if (filters.length > 0) {
      subtitle += ` • ${filters.join(', ')}`;
    }

    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'Tester Performance', 
      subtitle 
    });
  }, [testers.length, selectedPeriod, selectedStatus]);

  useEffect(() => {
    loadTesters();
  }, [selectedPeriod, selectedStatus]);

  const loadTesters = async (page = 1) => {
    try {
      setLoading(true);
      
      // Use the same service as the admin dashboard
      const response = await testerRankingsService.getRankings(
        selectedPeriod as 'all_time' | 'last_30_days' | 'last_90_days', 
        50 // Higher limit for full page
      );
      
      // Transform the data to match our interface
      const transformedTesters: TesterPerformance[] = response.rankings.map(ranking => ({
        ...ranking,
        full_name: ranking.user_name, // Map user_name to full_name for compatibility
        success_rate: ranking.success_score, // Map success_score to success_rate
        last_activity: ranking.last_suggestion_date || '',
        total_points: Math.floor(ranking.success_score * 10), // Calculate points based on success score
        is_active: true // Default to active, or add logic based on last activity
      }));
      
      setTesters(transformedTesters);
      setPagination({
        currentPage: page,
        totalPages: Math.ceil(response.total_testers / 50),
        total: response.total_testers,
        hasNext: page < Math.ceil(response.total_testers / 50)
      });
    } catch (error) {
      console.error('Failed to load testers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewTesterDetails = (tester: TesterPerformance) => {
    setSelectedTester(tester);
  };

  const handleRefresh = () => {
    loadTesters(pagination.currentPage);
  };

  const columns: TableColumn<TesterPerformance>[] = [
    {
      key: 'rank',
      label: '#',
      render: (rank: number) => (
        <div className="flex items-center gap-2">
          {rank <= 3 && (
            <Award 
              size={16} 
              className={
                rank === 1 ? 'text-yellow-500' :
                rank === 2 ? 'text-gray-400' :
                'text-amber-600'
              } 
            />
          )}
          <span className="font-semibold">{rank}</span>
        </div>
      ),
      width: '60px',
      sortable: true,
    },
    {
      key: 'full_name',
      label: 'Tester',
      render: (name: string, tester: TesterPerformance) => (
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm truncate">{name}</span>
            {!tester.is_active && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200">
                Inactive
              </span>
            )}
          </div>
          <div className="text-xs text-neutral-500 truncate">{tester.email}</div>
        </div>
      ),
      width: '200px',
      sortable: true,
    },
    {
      key: 'total_suggestions',
      label: 'Total',
      render: (total: number) => (
        <div className="text-center">
          <span className="text-lg font-bold text-neutral-900 dark:text-neutral-100">{total}</span>
          <div className="text-xs text-neutral-500">suggestions</div>
        </div>
      ),
      width: '80px',
      sortable: true,
    },
    {
      key: 'success_rate',
      label: 'Success Rate',
      render: (rate: number, tester: TesterPerformance) => (
        <div className="text-center">
          <div className={`text-lg font-bold ${
            rate >= 80 ? 'text-green-600' :
            rate >= 60 ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            {rate.toFixed(1)}%
          </div>
          <div className="text-xs text-neutral-500">
            {tester.approved_suggestions + tester.implemented_suggestions}/{tester.total_suggestions} approved
          </div>
        </div>
      ),
      width: '120px',
      sortable: true,
    },
    {
      key: 'breakdown',
      label: 'Breakdown',
      render: (_, tester: TesterPerformance) => (
        <div className="flex gap-1">
          <div className="text-center">
            <div className="text-sm font-semibold text-green-600">{tester.approved_suggestions}</div>
            <div className="text-xs text-neutral-500">Approved</div>
          </div>
          <div className="text-center">
            <div className="text-sm font-semibold text-purple-600">{tester.implemented_suggestions}</div>
            <div className="text-xs text-neutral-500">Live</div>
          </div>
          <div className="text-center">
            <div className="text-sm font-semibold text-gray-600">{tester.pending_suggestions}</div>
            <div className="text-xs text-neutral-500">Pending</div>
          </div>
          <div className="text-center">
            <div className="text-sm font-semibold text-red-600">{tester.rejected_suggestions}</div>
            <div className="text-xs text-neutral-500">Rejected</div>
          </div>
        </div>
      ),
      width: '240px',
    },
    {
      key: 'total_points',
      label: 'Points',
      render: (points: number) => (
        <div className="text-center">
          <span className="text-lg font-bold text-blue-600">{points}</span>
          <div className="text-xs text-neutral-500">total points</div>
        </div>
      ),
      width: '80px',
      sortable: true,
    },
    {
      key: 'last_activity',
      label: 'Last Active',
      render: (date: string) => (
        <div className="text-center">
          <span className="text-sm">
            {date ? new Date(date).toLocaleDateString() : 'Never'}
          </span>
          <div className="text-xs text-neutral-500">
            {date && getTimeAgo(date)}
          </div>
        </div>
      ),
      width: '120px',
      sortable: true,
    },
  ];

  const actions: TableAction<TesterPerformance>[] = [
    {
      label: 'View Details',
      icon: <Eye size={12} />,
      onClick: handleViewTesterDetails,
      variant: 'secondary',
    },
  ];

  // Check permissions
  const hasAccess = user?.permissions?.is_admin || user?.permissions?.is_super_admin;

  if (!hasAccess) {
    return (
      <div className="p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-neutral-600">You don't have permission to view tester performance data.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Fixed Header with Filters */}
      <div className="flex-none p-6 border-b border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900">
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center gap-4">
            <Button 
              onClick={handleRefresh}
              className="btn-secondary flex items-center gap-2"
              disabled={loading}
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="card p-4">
          <div className="flex flex-col lg:flex-row gap-4 lg:items-center">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium whitespace-nowrap">Time Period:</label>
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="input w-40 text-sm"
              >
                <option value="last_7_days">Last 7 days</option>
                <option value="last_30_days">Last 30 days</option>
                <option value="last_90_days">Last 90 days</option>
                <option value="all_time">All time</option>
              </select>
            </div>

            <div className="flex items-center gap-4">
              <label className="text-sm font-medium whitespace-nowrap">Status:</label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="input w-32 text-sm"
              >
                <option value="all">All Testers</option>
                <option value="active">Active Only</option>
                <option value="inactive">Inactive Only</option>
              </select>
            </div>

            <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400 ml-auto">
              <TrendingUp size={14} />
              <span>{pagination.total} total testers</span>
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Table Area */}
      <div className="flex-1 min-h-0 p-6">
        <div className="h-full">
          <DataTable
            data={testers}
            columns={columns}
            actions={actions}
            loading={loading}
            searchable
            searchPlaceholder="Search testers..."
            pagination={{
              currentPage: pagination.currentPage,
              totalPages: pagination.totalPages,
              onPageChange: loadTesters,
            }}
            emptyMessage="No testers found"
            className="h-full"
          />
        </div>
      </div>

      {/* Tester Details Modal */}
      {selectedTester && (
        <TesterDetailsModal
          tester={selectedTester}
          onClose={() => setSelectedTester(null)}
        />
      )}
    </div>
  );
}

// Helper function for time ago
function getTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
  
  if (diffInDays === 0) return 'Today';
  if (diffInDays === 1) return 'Yesterday';
  if (diffInDays < 7) return `${diffInDays} days ago`;
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
  if (diffInDays < 365) return `${Math.floor(diffInDays / 30)} months ago`;
  return `${Math.floor(diffInDays / 365)} years ago`;
}

// Tester Details Modal Component
function TesterDetailsModal({ 
  tester, 
  onClose 
}: { 
  tester: TesterPerformance; 
  onClose: () => void; 
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-xl font-bold">{tester.full_name}</h2>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">{tester.email}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-sm font-medium">Rank #{tester.rank}</span>
                {tester.rank <= 3 && (
                  <Award 
                    size={16} 
                    className={
                      tester.rank === 1 ? 'text-yellow-500' :
                      tester.rank === 2 ? 'text-gray-400' :
                      'text-amber-600'
                    } 
                  />
                )}
              </div>
            </div>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
            >
              <XCircle size={20} />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Performance Overview */}
            <div className="space-y-4">
              <h3 className="font-semibold text-lg">Performance Overview</h3>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <MessageSquare size={16} className="text-blue-600" />
                    <span className="text-sm font-medium">Total Suggestions</span>
                  </div>
                  <span className="text-lg font-bold">{tester.total_suggestions}</span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600" />
                    <span className="text-sm font-medium">Success Rate</span>
                  </div>
                  <span className="text-lg font-bold text-green-600">{tester.success_rate.toFixed(1)}%</span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Target size={16} className="text-purple-600" />
                    <span className="text-sm font-medium">Total Points</span>
                  </div>
                  <span className="text-lg font-bold text-purple-600">{tester.total_points}</span>
                </div>
              </div>
            </div>

            {/* Suggestion Breakdown */}
            <div className="space-y-4">
              <h3 className="font-semibold text-lg">Suggestion Breakdown</h3>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600" />
                    <span className="text-sm font-medium">Approved</span>
                  </div>
                  <span className="text-lg font-bold text-green-600">{tester.approved_suggestions}</span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Zap size={16} className="text-purple-600" />
                    <span className="text-sm font-medium">Implemented</span>
                  </div>
                  <span className="text-lg font-bold text-purple-600">{tester.implemented_suggestions}</span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Clock size={16} className="text-gray-600" />
                    <span className="text-sm font-medium">Pending</span>
                  </div>
                  <span className="text-lg font-bold text-gray-600">{tester.pending_suggestions}</span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <XCircle size={16} className="text-red-600" />
                    <span className="text-sm font-medium">Rejected</span>
                  </div>
                  <span className="text-lg font-bold text-red-600">{tester.rejected_suggestions}</span>
                </div>
              </div>
            </div>

            {/* Activity Information */}
            <div className="md:col-span-2 space-y-4">
              <h3 className="font-semibold text-lg">Activity Information</h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {tester.join_date && (
                  <div className="p-3 bg-neutral-50 dark:bg-neutral-700 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <Calendar size={16} className="text-neutral-600" />
                      <span className="text-sm font-medium">Join Date</span>
                    </div>
                    <span className="text-sm">{new Date(tester.join_date).toLocaleDateString()}</span>
                  </div>
                )}
                
                <div className="p-3 bg-neutral-50 dark:bg-neutral-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock size={16} className="text-neutral-600" />
                    <span className="text-sm font-medium">Last Activity</span>
                  </div>
                  <span className="text-sm">
                    {tester.last_activity ? new Date(tester.last_activity).toLocaleDateString() : 'Never'}
                  </span>
                  {tester.last_activity && (
                    <div className="text-xs text-neutral-500 mt-1">
                      {getTimeAgo(tester.last_activity)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}