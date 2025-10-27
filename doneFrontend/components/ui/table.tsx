// src/ui/table.tsx
import React from 'react';

export interface TableData {
  type: 'table';
  title?: string;
  headers: string[];
  rows: string[][];
  context?: string;
  actions?: Array<{
    type: 'example' | 'action';
    text: string;
  }>;
}

interface ChatTableProps {
  table: TableData;
}

export default function ChatTable({ table }: ChatTableProps) {
  if (!table || table.type !== 'table') {
    return null;
  }

  const renderCellContent = (cell: string, columnIndex: number) => {
    // Special styling for specific cell values
    if (cell === "Not Set") {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200">
          Not Set
        </span>
      );
    }
    
    if (cell === "Required") {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200">
          Required
        </span>
      );
    }
    
    if (cell === "Optional") {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
          Optional
        </span>
      );
    }

    // Format amounts (if cell contains numbers and currency context)
    if (table.context === 'fee_summary' && columnIndex === 1 && /^\d+$/.test(cell)) {
      return `₹${parseInt(cell).toLocaleString()}`;
    }

    return cell;
  };

  return (
    <div className="my-4 rounded-lg border border-neutral-200 dark:border-neutral-700 overflow-hidden bg-white dark:bg-neutral-800 shadow-sm">
      {/* Table Title */}
      {table.title && (
        <div className="px-4 py-3 bg-neutral-50 dark:bg-neutral-700/50 border-b border-neutral-200 dark:border-neutral-600">
          <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
            {table.title}
          </h3>
        </div>
      )}
      
      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="min-w-full">
          {/* Headers */}
          <thead className="bg-neutral-50 dark:bg-neutral-700/30">
            <tr>
              {table.headers?.map((header, index) => (
                <th
                  key={index}
                  className="px-4 py-3 text-left text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider border-b border-neutral-200 dark:border-neutral-600"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          
          {/* Rows */}
          <tbody className="divide-y divide-neutral-200 dark:divide-neutral-600">
            {table.rows?.map((row, rowIndex) => (
              <tr 
                key={rowIndex} 
                className="hover:bg-neutral-50 dark:hover:bg-neutral-700/30 transition-colors"
              >
                {row.map((cell, cellIndex) => (
                  <td
                    key={cellIndex}
                    className={`px-4 py-3 text-sm ${
                      cellIndex === 0 
                        ? 'font-medium text-neutral-900 dark:text-neutral-100' 
                        : 'text-neutral-600 dark:text-neutral-300'
                    }`}
                  >
                    {renderCellContent(cell, cellIndex)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Action Examples */}
      {table.actions && table.actions.length > 0 && (
        <div className="px-4 py-3 bg-neutral-50 dark:bg-neutral-700/50 border-t border-neutral-200 dark:border-neutral-600">
          <p className="text-xs text-neutral-600 dark:text-neutral-400 mb-2 font-medium">
            Examples:
          </p>
          <div className="space-y-1.5">
            {table.actions.map((action, index) => (
              <div key={index} className="text-xs">
                <code className="bg-neutral-100 dark:bg-neutral-700 px-2.5 py-1.5 rounded text-neutral-800 dark:text-neutral-200 font-mono text-xs">
                  {action.text}
                </code>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}