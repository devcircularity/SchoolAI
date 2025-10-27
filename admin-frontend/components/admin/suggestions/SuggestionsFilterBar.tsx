// components/admin/suggestions/SuggestionsFilterBar.tsx
interface SuggestionsFilterBarProps {
  selectedStatus: string;
  onStatusChange: (status: string) => void;
}

export function SuggestionsFilterBar({ 
  selectedStatus, 
  onStatusChange 
}: SuggestionsFilterBarProps) {
  return (
    <div className="card p-3 sm:p-4 mb-4 sm:mb-6">
      <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 sm:items-center">
        <label className="text-xs sm:text-sm font-medium">Filter by Status:</label>
        <select
          value={selectedStatus}
          onChange={(e) => onStatusChange(e.target.value)}
          className="input w-full sm:w-48 text-sm"
        >
          <option value="pending">Pending Review</option>
          <option value="needs_analysis">Needs Analysis</option>
          <option value="approved">Approved (Ready for Action Items)</option>
          <option value="rejected">Rejected</option>
          <option value="implemented">Addressed</option>
          <option value="all">All</option>
        </select>
      </div>
    </div>
  );
}