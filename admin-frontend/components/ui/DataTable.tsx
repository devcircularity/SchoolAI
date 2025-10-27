// components/ui/DataTable.tsx - Fixed invisible header issue
"use client";
import { useState } from "react";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import Button from "./Button";

export interface TableColumn<T> {
  key: keyof T | string;
  label: string;
  render?: (value: any, row: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}

export interface TableAction<T> {
  label: string;
  onClick: (row: T) => void;
  variant?: 'primary' | 'secondary' | 'danger';
  icon?: React.ReactNode;
  disabled?: (row: T) => boolean;
}

interface DataTableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  actions?: TableAction<T>[];
  loading?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  pagination?: {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
  };
  emptyMessage?: string;
  className?: string;
}

export default function DataTable<T extends Record<string, any>>({
  data,
  columns,
  actions,
  loading = false,
  searchable = false,
  searchPlaceholder = "Search...",
  pagination,
  emptyMessage = "No data available",
  className = ""
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'asc' | 'desc';
  } | null>(null);

  const filteredData = searchable
    ? data.filter(row =>
        Object.values(row).some(value =>
          String(value).toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
    : data;

  const sortedData = sortConfig
    ? [...filteredData].sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];
        
        if (aValue < bValue) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      })
    : filteredData;

  const handleSort = (key: string) => {
    setSortConfig(current => {
      if (current?.key === key) {
        return {
          key,
          direction: current.direction === 'asc' ? 'desc' : 'asc'
        };
      }
      return { key, direction: 'asc' };
    });
  };

  const getCellValue = (row: T, column: TableColumn<T>) => {
    const value = row[column.key as keyof T];
    return column.render ? column.render(value, row) : value;
  };

  if (loading) {
    return (
      <div className={`h-full flex items-center justify-center bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-700 shadow-sm ${className}`}>
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-[--color-brand]"></div>
          <p className="mt-2 text-neutral-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`h-full flex flex-col bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-700 shadow-sm ${className}`}>
      {searchable && (
        <div className="flex-shrink-0 p-4 border-b border-neutral-200 dark:border-neutral-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400" size={16} />
            <input
              type="text"
              placeholder={searchPlaceholder}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg 
                         bg-white dark:bg-neutral-800 focus:ring-2 focus:ring-[--color-brand] focus:border-transparent text-sm"
            />
          </div>
        </div>
      )}

      <div className="flex-1 min-h-0 flex flex-col">
        {/* Fixed Table Header */}
        <div className="flex-shrink-0 bg-neutral-50 dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700">
          <table className="w-full">
            <thead>
              <tr>
                {columns.map((column, index) => (
                  <th
                    key={index}
                    className={`px-4 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider
                      ${column.sortable ? 'cursor-pointer hover:bg-neutral-100 dark:hover:bg-neutral-700' : ''}
                      ${column.width ? '' : 'min-w-0'}`}
                    style={column.width ? { width: column.width, minWidth: column.width } : {}}
                    onClick={column.sortable ? () => handleSort(String(column.key)) : undefined}
                  >
                    <div className="flex items-center gap-1">
                      <span className="truncate">{column.label}</span>
                      {column.sortable && sortConfig?.key === column.key && (
                        <span className="text-[--color-brand] flex-shrink-0">
                          {sortConfig.direction === 'asc' ? '↑' : '↓'}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
                {actions && actions.length > 0 && (
                  <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider w-32">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
          </table>
        </div>

        {/* Scrollable Table Body - FIXED: removed invisible header, using colgroup for alignment */}
        <div className="flex-1 overflow-auto pb-4">
          <table className="w-full">
            <colgroup>
              {columns.map((column, index) => (
                <col
                  key={index}
                  style={column.width ? { width: column.width, minWidth: column.width } : {}}
                />
              ))}
              {actions && actions.length > 0 && (
                <col style={{ width: '128px', minWidth: '128px' }} />
              )}
            </colgroup>
            <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700">
              {sortedData.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length + (actions ? 1 : 0)}
                    className="px-4 py-8 text-center text-neutral-500 dark:text-neutral-400"
                  >
                    {emptyMessage}
                  </td>
                </tr>
              ) : (
                sortedData.map((row, rowIndex) => (
                  <tr key={rowIndex} className="hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                    {columns.map((column, colIndex) => (
                      <td 
                        key={colIndex} 
                        className="px-4 py-3 text-sm text-neutral-900 dark:text-neutral-100"
                      >
                        <div className="min-w-0">
                          {getCellValue(row, column)}
                        </div>
                      </td>
                    ))}
                    {actions && actions.length > 0 && (
                      <td className="px-4 py-3 text-sm">
                        <div className="flex gap-1 flex-wrap">
                          {actions.map((action, actionIndex) => (
                            <Button
                              key={actionIndex}
                              onClick={() => action.onClick(row)}
                              className={`btn-sm whitespace-nowrap ${
                                action.variant === 'danger' ? 'btn-danger' :
                                action.variant === 'secondary' ? 'btn-secondary' :
                                'btn-primary'
                              }`}
                              disabled={action.disabled?.(row)}
                              title={action.label}
                            >
                              {action.icon && <span className="mr-1">{action.icon}</span>}
                              <span className="hidden sm:inline">{action.label}</span>
                              <span className="sm:hidden">{action.icon}</span>
                            </Button>
                          ))}
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {pagination && (
        <div className="flex-shrink-0 px-4 py-3 border-t border-neutral-200 dark:border-neutral-700 flex items-center justify-between bg-neutral-50 dark:bg-neutral-800">
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            Page {pagination.currentPage} of {pagination.totalPages}
          </p>
          <div className="flex gap-2">
            <Button
              onClick={() => pagination.onPageChange(pagination.currentPage - 1)}
              disabled={pagination.currentPage <= 1}
              className="btn-sm btn-secondary"
            >
              <ChevronLeft size={16} />
              <span className="hidden sm:inline ml-1">Previous</span>
            </Button>
            <Button
              onClick={() => pagination.onPageChange(pagination.currentPage + 1)}
              disabled={pagination.currentPage >= pagination.totalPages}
              className="btn-sm btn-secondary"
            >
              <span className="hidden sm:inline mr-1">Next</span>
              <ChevronRight size={16} />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}