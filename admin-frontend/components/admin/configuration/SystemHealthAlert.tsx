// app/admin/configuration/components/SystemHealthAlert.tsx
import { AlertCircle } from "lucide-react";

interface SystemHealthAlertProps {
  cacheStatus: string;
}

export default function SystemHealthAlert({ cacheStatus }: SystemHealthAlertProps) {
  return (
    <div className="card p-3 sm:p-4 mb-4 sm:mb-6 border-orange-200 bg-orange-50 dark:bg-orange-900/20">
      <div className="flex items-start gap-2 sm:gap-3 text-orange-800 dark:text-orange-200">
        <AlertCircle size={18} className="mt-0.5 flex-shrink-0" />
        <div className="min-w-0">
          <h3 className="font-semibold text-sm sm:text-base">System Health Warning</h3>
          <p className="text-xs sm:text-sm">
            Configuration cache status: {cacheStatus}. Consider reloading the cache.
          </p>
        </div>
      </div>
    </div>
  );
}