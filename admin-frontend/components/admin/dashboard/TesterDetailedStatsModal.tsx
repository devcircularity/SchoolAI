// components/admin/dashboard/TesterDetailedStatsModal.tsx
import { useState, useEffect } from 'react';
import { X, TrendingUp, BarChart3 } from 'lucide-react';
import Modal from '@/components/ui/Modal';
import { testerRankingsService, TesterDetailedStats } from '@/services/testerRankings';
import Button from '@/components/ui/Button';

interface TesterDetailedStatsModalProps {
  userId: string;
  onClose: () => void;
}

export function TesterDetailedStatsModal({ userId, onClose }: TesterDetailedStatsModalProps) {
  const [stats, setStats] = useState<TesterDetailedStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, [userId]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await testerRankingsService.getTesterDetailedStats(userId);
      setStats(data);
    } catch (error) {
      console.error('Failed to load tester stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Modal isOpen={true} onClose={onClose} title="Loading..." size="xl">
        <div className="animate-pulse space-y-4 p-6">
          <div className="h-8 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
          <div className="h-32 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
        </div>
      </Modal>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <Modal isOpen={true} onClose={onClose} title="" size="xl">
      <div className="p-4 sm:p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold">{stats.user_name}</h2>
            <p className="text-sm text-neutral-500">{stats.email}</p>
            <p className="text-lg font-semibold mt-2">{stats.total_suggestions} Total Suggestions</p>
          </div>
          <Button onClick={onClose} className="btn-secondary">
            <X size={16} />
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="card p-4">
            <p className="text-xs text-neutral-500 mb-1">By Status</p>
            <div className="space-y-1">
              {Object.entries(stats.by_status).map(([status, count]) => (
                <div key={status} className="flex justify-between text-sm">
                  <span className="capitalize">{status.replace('_', ' ')}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-4">
            <p className="text-xs text-neutral-500 mb-1">By Type</p>
            <div className="space-y-1">
              {Object.entries(stats.by_type).map(([type, count]) => (
                <div key={type} className="flex justify-between text-sm">
                  <span className="capitalize">{type.replace('_', ' ')}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-4">
            <p className="text-xs text-neutral-500 mb-1">By Priority</p>
            <div className="space-y-1">
              {Object.entries(stats.by_priority).map(([priority, count]) => (
                <div key={priority} className="flex justify-between text-sm">
                  <span className="capitalize">{priority}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-4">
            <p className="text-xs text-neutral-500 mb-1">Success Rates</p>
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>Approval</span>
                <span className="font-semibold text-green-600">
                  {((stats.by_status.approved || 0) / stats.total_suggestions * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Implementation</span>
                <span className="font-semibold text-blue-600">
                  {((stats.by_status.implemented || 0) / stats.total_suggestions * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Monthly Trend */}
        <div className="card p-4 mb-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <TrendingUp size={16} />
            Monthly Trend
          </h3>
          <div className="space-y-2">
            {stats.monthly_trend.map((month, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <span className="text-sm w-20 text-neutral-600">{month.month}</span>
                <div className="flex-1 flex items-center gap-2">
                  <div className="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-6 overflow-hidden">
                    <div 
                      className="bg-blue-500 h-full flex items-center justify-end pr-2"
                      style={{ width: `${(month.total / Math.max(...stats.monthly_trend.map(m => m.total))) * 100}%` }}
                    >
                      <span className="text-xs text-white font-medium">{month.total}</span>
                    </div>
                  </div>
                  <span className="text-xs text-green-600 w-12">✓ {month.implemented}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Suggestions */}
        <div className="card p-4">
          <h3 className="font-semibold mb-4">Recent Suggestions</h3>
          <div className="space-y-2">
            {stats.recent_suggestions.map((suggestion) => (
              <div key={suggestion.id} className="flex justify-between items-center p-2 hover:bg-neutral-50 dark:hover:bg-neutral-800 rounded">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{suggestion.title}</p>
                  <p className="text-xs text-neutral-500">
                    {new Date(suggestion.created_at).toLocaleDateString()}
                  </p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  suggestion.status === 'implemented' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-200' :
                  suggestion.status === 'approved' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200' :
                  suggestion.status === 'rejected' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200' :
                  'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200'
                }`}>
                  {suggestion.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}