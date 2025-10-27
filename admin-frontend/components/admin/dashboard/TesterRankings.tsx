// components/admin/dashboard/TesterRankings.tsx
import { useState, useEffect } from 'react';
import { Trophy, TrendingUp, CheckCircle, XCircle, Clock, Award, Eye } from 'lucide-react';
import { testerRankingsService, TesterRanking } from '@/services/testerRankings';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { TesterDetailedStatsModal } from './TesterDetailedStatsModal';

interface TesterRankingsProps {
  period?: 'all_time' | 'last_30_days' | 'last_90_days';
  limit?: number;
}

export function TesterRankings({ period = 'all_time', limit = 10 }: TesterRankingsProps) {
  const [rankings, setRankings] = useState<TesterRanking[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState(period);
  const [selectedTester, setSelectedTester] = useState<string | null>(null);

  useEffect(() => {
    loadRankings();
  }, [selectedPeriod]);

  const loadRankings = async () => {
    try {
      setLoading(true);
      const response = await testerRankingsService.getRankings(selectedPeriod, limit);
      setRankings(response.rankings);
    } catch (error) {
      console.error('Failed to load tester rankings:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMedalIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="text-yellow-500" size={20} />;
    if (rank === 2) return <Award className="text-gray-400" size={20} />;
    if (rank === 3) return <Award className="text-amber-600" size={20} />;
    return <span className="text-neutral-400 font-semibold">{rank}</span>;
  };

  const getSuccessScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 dark:text-green-400';
    if (score >= 60) return 'text-blue-600 dark:text-blue-400';
    if (score >= 40) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-orange-600 dark:text-orange-400';
  };

  if (loading) {
    return (
      <div className="card p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-neutral-200 dark:bg-neutral-700 rounded w-1/3"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="h-16 bg-neutral-200 dark:bg-neutral-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="card p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 gap-3">
          <h2 className="text-lg sm:text-xl font-semibold flex items-center gap-2">
            <Trophy size={20} className="text-yellow-500" />
            Tester Leaderboard
          </h2>
          <div className="flex gap-2">
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value as any)}
              className="input text-sm"
            >
              <option value="all_time">All Time</option>
              <option value="last_30_days">Last 30 Days</option>
              <option value="last_90_days">Last 90 Days</option>
            </select>
          </div>
        </div>

        {rankings.length === 0 ? (
          <div className="text-center py-8 text-neutral-500">
            <Trophy size={48} className="mx-auto mb-3 opacity-30" />
            <p>No tester activity found for this period</p>
          </div>
        ) : (
          <div className="space-y-2">
            {rankings.map((tester) => (
              <div
                key={tester.user_id}
                className={`p-3 sm:p-4 rounded-lg border transition-colors ${
                  tester.rank <= 3 
                    ? 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20' 
                    : 'border-neutral-200 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
                }`}
              >
                <div className="flex items-center gap-3 sm:gap-4">
                  {/* Rank */}
                  <div className="flex-shrink-0 w-8 flex items-center justify-center">
                    {getMedalIcon(tester.rank)}
                  </div>

                  {/* Tester Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm sm:text-base truncate">{tester.user_name}</h3>
                    <p className="text-xs text-neutral-500 truncate">{tester.email}</p>
                  </div>

                  {/* Stats - Desktop */}
                  <div className="hidden lg:flex items-center gap-6">
                    <div className="text-center">
                      <p className="text-xs text-neutral-500">Total</p>
                      <p className="font-semibold">{tester.total_suggestions}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-neutral-500">Approved</p>
                      <p className="font-semibold text-green-600">{tester.approved_suggestions}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-neutral-500">Implemented</p>
                      <p className="font-semibold text-blue-600">{tester.implemented_suggestions}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-neutral-500">Success Rate</p>
                      <p className={`font-semibold ${getSuccessScoreColor(tester.success_score)}`}>
                        {tester.success_score}%
                      </p>
                    </div>
                  </div>

                  {/* Stats - Mobile */}
                  <div className="lg:hidden flex flex-col items-end gap-1">
                    <span className="text-sm font-semibold">{tester.total_suggestions} total</span>
                    <span className={`text-xs font-medium ${getSuccessScoreColor(tester.success_score)}`}>
                      {tester.success_score}% score
                    </span>
                  </div>

                  {/* View Details Button */}
                  <Button
                    onClick={() => setSelectedTester(tester.user_id)}
                    className="btn-secondary flex-shrink-0 text-xs sm:text-sm"
                  >
                    <Eye size={14} />
                    <span className="hidden sm:inline ml-1">Details</span>
                  </Button>
                </div>

                {/* Mobile Stats Breakdown */}
                <div className="lg:hidden mt-3 pt-3 border-t border-neutral-200 dark:border-neutral-700 grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-xs text-neutral-500">Approved</p>
                    <p className="text-sm font-semibold text-green-600">{tester.approved_suggestions}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500">Implemented</p>
                    <p className="text-sm font-semibold text-blue-600">{tester.implemented_suggestions}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500">Rejected</p>
                    <p className="text-sm font-semibold text-red-600">{tester.rejected_suggestions}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detailed Stats Modal */}
      {selectedTester && (
        <TesterDetailedStatsModal
          userId={selectedTester}
          onClose={() => setSelectedTester(null)}
        />
      )}
    </>
  );
}