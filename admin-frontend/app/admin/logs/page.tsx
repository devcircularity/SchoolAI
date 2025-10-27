// app/admin/logs/page.tsx - System logs with dynamic header
"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { HeaderTitleBus } from "@/components/layout/HeaderBar";
import DataTable, { TableColumn } from "@/components/ui/DataTable";
import { Filter, Download } from "lucide-react";
import Button from "@/components/ui/Button";

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  message: string;
  user_id?: string;
  user_email?: string;
  school_id?: string;
  endpoint?: string;
  ip_address?: string;
  user_agent?: string;
}

export default function LogsPage() {
  const { user } = useAuth();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLevel, setSelectedLevel] = useState<string>('ALL');
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Yesterday
    end: new Date().toISOString().split('T')[0] // Today
  });

  // Set page title in header
  useEffect(() => {
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'System Logs',
      subtitle: 'Monitor system activity and troubleshoot issues' 
    });
    
    return () => HeaderTitleBus.send({ type: 'clear' });
  }, []);

  // Mock data for now - replace with actual API call
  useEffect(() => {
    // Simulate loading logs
    setTimeout(() => {
      const mockLogs: LogEntry[] = [
        {
          id: '1',
          timestamp: new Date().toISOString(),
          level: 'INFO',
          message: 'User login successful',
          user_email: 'john@example.com',
          endpoint: '/api/auth/login',
          ip_address: '192.168.1.1'
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          level: 'WARN',
          message: 'Failed login attempt',
          endpoint: '/api/auth/login',
          ip_address: '192.168.1.5'
        },
        {
          id: '3',
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          level: 'ERROR',
          message: 'Database connection timeout',
          endpoint: '/api/users',
          ip_address: '10.0.0.1'
        }
      ];
      setLogs(mockLogs);
      setLoading(false);
    }, 1000);
  }, [dateRange, selectedLevel]);

  const columns: TableColumn<LogEntry>[] = [
    {
      key: 'timestamp',
      label: 'Time',
      render: (timestamp: string) => (
        <span className="text-xs sm:text-sm">
          {new Date(timestamp).toLocaleString()}
        </span>
      ),
      width: '180px',
    },
    {
      key: 'level',
      label: 'Level',
      render: (level: string) => (
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            level === 'ERROR' ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200' :
            level === 'WARN' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200' :
            level === 'INFO' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200' :
            'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200'
          }`}
        >
          {level}
        </span>
      ),
      width: '80px',
    },
    {
      key: 'message',
      label: 'Message',
      render: (message: string) => (
        <span className="font-mono text-xs sm:text-sm break-words">{message}</span>
      ),
    },
    {
      key: 'user_email',
      label: 'User',
      render: (email: string) => (
        <span className="text-xs sm:text-sm">{email || '-'}</span>
      ),
      width: '150px',
    },
    {
      key: 'endpoint',
      label: 'Endpoint',
      render: (endpoint: string) => (
        <code className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded break-all">
          {endpoint || '-'}
        </code>
      ),
      width: '120px',
    },
    {
      key: 'ip_address',
      label: 'IP Address',
      render: (ip: string) => (
        <code className="text-xs">{ip || '-'}</code>
      ),
      width: '120px',
    },
  ];

  const filteredLogs = selectedLevel === 'ALL' 
    ? logs 
    : logs.filter(log => log.level === selectedLevel);

  const hasViewLogsPermission = user?.permissions?.is_admin || 
                               user?.permissions?.is_super_admin;

  if (!hasViewLogsPermission) {
    return (
      <div className="p-4 sm:p-6">
        <div className="text-center">
          <h1 className="text-xl sm:text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-neutral-600">You don't have permission to view system logs.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6">
      {/* Action button aligned to right - title is now in HeaderBar */}
      <div className="flex justify-end items-center mb-4 sm:mb-6">
        <Button className="btn-secondary flex items-center gap-2 text-sm">
          <Download size={16} />
          <span className="hidden sm:inline">Export Logs</span>
          <span className="sm:hidden">Export</span>
        </Button>
      </div>

      {/* Filters - Mobile responsive */}
      <div className="card p-3 sm:p-4 mb-4 sm:mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-3 sm:gap-4 items-end">
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1">Log Level</label>
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="input w-full text-sm"
            >
              <option value="ALL">All Levels</option>
              <option value="ERROR">Error</option>
              <option value="WARN">Warning</option>
              <option value="INFO">Info</option>
              <option value="DEBUG">Debug</option>
            </select>
          </div>
          
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1">Start Date</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
              className="input w-full text-sm"
            />
          </div>
          
          <div>
            <label className="block text-xs sm:text-sm font-medium mb-1">End Date</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
              className="input w-full text-sm"
            />
          </div>
          
          <div className="sm:col-span-2 lg:col-span-1">
            <Button className="btn-secondary flex items-center gap-2 w-full sm:w-auto text-sm">
              <Filter size={16} />
              Apply Filters
            </Button>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="overflow-x-auto">
        <DataTable
          data={filteredLogs}
          columns={columns}
          loading={loading}
          searchable
          searchPlaceholder="Search logs..."
          emptyMessage="No logs found for the selected criteria"
          className="font-mono text-xs sm:text-sm"
        />
      </div>
    </div>
  );
}