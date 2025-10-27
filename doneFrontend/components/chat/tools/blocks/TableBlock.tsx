// components/chat/tools/blocks/TableBlock.tsx - Mobile-responsive version
'use client'
import { useState } from 'react'
import { TableBlock as TableBlockType, Action, TableRow, BadgeVariant } from '../types'
import { formatValue } from '../utils/formatters'
import { getAlignmentClass, getVariantClasses } from '../utils/styles'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface Props {
  block: TableBlockType
  onAction?: (action: Action) => void
}

export function TableBlock({ block, onAction }: Props) {
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set())
  const [currentPage, setCurrentPage] = useState(1)
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set())
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table')

  // Auto-switch to cards view on mobile
  useState(() => {
    const checkScreenSize = () => {
      setViewMode(window.innerWidth < 768 ? 'cards' : 'table')
    }
    
    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    return () => window.removeEventListener('resize', checkScreenSize)
  })

  const handleRowClick = (row: TableRow, index: number) => {
    if (row._action && onAction) {
      onAction(row._action)
    }
  }

  const handleRowSelection = (index: number) => {
    const newSelected = new Set(selectedRows)
    if (newSelected.has(index)) {
      newSelected.delete(index)
    } else {
      newSelected.add(index)
    }
    setSelectedRows(newSelected)
  }

  const handleActionClick = (action: any) => {
    if (onAction) {
      const actionWithSelection = {
        ...action,
        selectedRows: Array.from(selectedRows)
      }
      onAction(actionWithSelection)
    }
  }

  const toggleRowExpansion = (index: number) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedRows(newExpanded)
  }

  const renderCellValue = (value: any, column: any) => {
    if (column.format) {
      return formatValue(value, column.format)
    }

    if (column.badge && typeof value === 'string') {
      const variant = column.badge.map[value] || 'primary'
      const classes = getVariantClasses(variant as BadgeVariant)
      return (
        <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${classes.badge}`}>
          {value}
        </span>
      )
    }

    return value
  }

  const renderFilterOption = (option: string | Record<string, any>, index: number) => {
    if (typeof option === 'string') {
      return (
        <option key={option} value={option}>
          {option}
        </option>
      )
    } else {
      const value = option.value || option.id || ''
      const label = option.label || option.name || value
      return (
        <option key={`${value}-${index}`} value={value}>
          {label}
        </option>
      )
    }
  }

  const hasSelectionActions = block.config.actions?.some(action => action.selectionRequired)

  // Mobile card view
  const renderCardView = () => (
    <div className="space-y-3">
      {block.config.rows.map((row, rowIndex) => {
        const isExpanded = expandedRows.has(rowIndex)
        const primaryColumns = block.config.columns.slice(0, 2) // Show first 2 columns primarily
        const secondaryColumns = block.config.columns.slice(2) // Rest are collapsible
        
        return (
          <div 
            key={rowIndex}
            className={`
              border border-neutral-200 dark:border-neutral-700 rounded-lg p-3
              ${row._action ? 'cursor-pointer hover:bg-neutral-50 dark:hover:bg-neutral-800/50' : ''}
              ${selectedRows.has(rowIndex) ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' : ''}
            `}
            onClick={() => handleRowClick(row, rowIndex)}
          >
            {/* Card header with selection and primary info */}
            <div className="flex items-start gap-3">
              {hasSelectionActions && (
                <input
                  type="checkbox"
                  checked={selectedRows.has(rowIndex)}
                  onChange={() => handleRowSelection(rowIndex)}
                  onClick={(e) => e.stopPropagation()}
                  className="mt-0.5 rounded border-neutral-300"
                />
              )}
              
              <div className="flex-1 min-w-0">
                {/* Primary columns - always visible */}
                <div className="space-y-1">
                  {primaryColumns.map((column) => (
                    <div key={column.key} className="flex justify-between items-center">
                      <span className="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wide">
                        {column.label}
                      </span>
                      <span className={`text-sm font-medium text-neutral-900 dark:text-neutral-100 ${getAlignmentClass(column.align)}`}>
                        {renderCellValue(row[column.key], column)}
                      </span>
                    </div>
                  ))}
                </div>
                
                {/* Expand/collapse button for secondary columns */}
                {secondaryColumns.length > 0 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleRowExpansion(rowIndex)
                    }}
                    className="flex items-center gap-1 mt-2 text-xs text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
                  >
                    {isExpanded ? (
                      <>
                        <ChevronDown size={14} />
                        Show less
                      </>
                    ) : (
                      <>
                        <ChevronRight size={14} />
                        Show more ({secondaryColumns.length} fields)
                      </>
                    )}
                  </button>
                )}
                
                {/* Secondary columns - collapsible */}
                {isExpanded && secondaryColumns.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-neutral-200 dark:border-neutral-700 space-y-2">
                    {secondaryColumns.map((column) => (
                      <div key={column.key} className="flex justify-between items-center">
                        <span className="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wide">
                          {column.label}
                        </span>
                        <span className={`text-sm text-neutral-700 dark:text-neutral-300 ${getAlignmentClass(column.align)}`}>
                          {renderCellValue(row[column.key], column)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )

  // Desktop table view
  const renderTableView = () => (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-neutral-50 dark:bg-neutral-800/50">
          <tr>
            {hasSelectionActions && (
              <th className="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedRows(new Set(Array.from({ length: block.config.rows.length }, (_, i) => i)))
                    } else {
                      setSelectedRows(new Set())
                    }
                  }}
                  className="rounded border-neutral-300"
                />
              </th>
            )}
            {block.config.columns.map((column) => (
              <th 
                key={column.key}
                className={`px-4 py-3 text-sm font-medium text-neutral-700 dark:text-neutral-300 ${getAlignmentClass(column.align)}`}
                style={{ width: column.width }}
              >
                <div className="flex items-center gap-2">
                  {column.label}
                  {column.sortable && (
                    <svg className="w-4 h-4 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                    </svg>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
          {block.config.rows.map((row, rowIndex) => (
            <tr 
              key={rowIndex}
              className={`
                hover:bg-neutral-50 dark:hover:bg-neutral-800/50
                ${row._action ? 'cursor-pointer' : ''}
                ${selectedRows.has(rowIndex) ? 'bg-blue-50 dark:bg-blue-900/20' : ''}
              `}
              onClick={() => handleRowClick(row, rowIndex)}
            >
              {hasSelectionActions && (
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedRows.has(rowIndex)}
                    onChange={() => handleRowSelection(rowIndex)}
                    onClick={(e) => e.stopPropagation()}
                    className="rounded border-neutral-300"
                  />
                </td>
              )}
              {block.config.columns.map((column) => (
                <td 
                  key={column.key}
                  className={`px-4 py-3 text-sm text-neutral-900 dark:text-neutral-100 ${getAlignmentClass(column.align)}`}
                >
                  {renderCellValue(row[column.key], column)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )

  return (
    <div className="card">
      {/* Header */}
      <div className="p-3 sm:p-4 border-b border-neutral-200 dark:border-neutral-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3 className="text-base sm:text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            {block.config.title}
          </h3>
          
          {/* Actions */}
          {block.config.actions && block.config.actions.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {block.config.actions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => handleActionClick(action)}
                  disabled={action.selectionRequired && selectedRows.size === 0}
                  className="btn-primary disabled:opacity-50 text-xs sm:text-sm px-2 py-1 sm:px-3 sm:py-2"
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
        
        {/* Filters - Mobile responsive */}
        {block.config.filters && block.config.filters.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:flex lg:flex-wrap gap-3 mt-4">
            {block.config.filters.map((filter, index) => (
              <div key={index} className="flex flex-col gap-1">
                <label className="text-xs sm:text-sm font-medium text-neutral-700 dark:text-neutral-300">
                  {filter.label}
                </label>
                {filter.type === 'select' ? (
                  <select className="input text-sm min-w-0 sm:min-w-32">
                    <option value="">All</option>
                    {filter.options?.map((option, optionIndex) => 
                      renderFilterOption(option, optionIndex)
                    )}
                  </select>
                ) : filter.type === 'daterange' ? (
                  <input type="date" className="input text-sm" />
                ) : (
                  <input type="text" className="input text-sm" placeholder={`Filter ${filter.label}`} />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* View toggle for mobile */}
      <div className="sm:hidden px-3 py-2 border-b border-neutral-200 dark:border-neutral-800">
        <div className="flex gap-1 bg-neutral-100 dark:bg-neutral-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('table')}
            className={`flex-1 px-3 py-1 rounded text-sm transition-colors ${
              viewMode === 'table' 
                ? 'bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100 shadow-sm' 
                : 'text-neutral-600 dark:text-neutral-400'
            }`}
          >
            Table
          </button>
          <button
            onClick={() => setViewMode('cards')}
            className={`flex-1 px-3 py-1 rounded text-sm transition-colors ${
              viewMode === 'cards' 
                ? 'bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100 shadow-sm' 
                : 'text-neutral-600 dark:text-neutral-400'
            }`}
          >
            Cards
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="sm:hidden">
        {viewMode === 'cards' ? (
          <div className="p-3">
            {renderCardView()}
          </div>
        ) : (
          renderTableView()
        )}
      </div>
      
      {/* Desktop always shows table */}
      <div className="hidden sm:block">
        {renderTableView()}
      </div>

      {/* Pagination */}
      {block.config.pagination && (
        <div className="px-3 sm:px-4 py-3 border-t border-neutral-200 dark:border-neutral-800">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-xs sm:text-sm text-neutral-700 dark:text-neutral-300 text-center sm:text-left">
              Showing {((currentPage - 1) * block.config.pagination.pageSize) + 1} to{' '}
              {Math.min(currentPage * block.config.pagination.pageSize, block.config.pagination.total || 0)} of{' '}
              {block.config.pagination.total || 0} results
            </div>
            
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="px-2 sm:px-3 py-1 text-xs sm:text-sm border rounded disabled:opacity-50"
              >
                Previous
              </button>
              
              <span className="px-2 sm:px-3 py-1 text-xs sm:text-sm">
                Page {currentPage} of {Math.ceil((block.config.pagination.total || 0) / block.config.pagination.pageSize)}
              </span>
              
              <button 
                onClick={() => setCurrentPage(prev => prev + 1)}
                disabled={currentPage >= Math.ceil((block.config.pagination.total || 0) / block.config.pagination.pageSize)}
                className="px-2 sm:px-3 py-1 text-xs sm:text-sm border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}