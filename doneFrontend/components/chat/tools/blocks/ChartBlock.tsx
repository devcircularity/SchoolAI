// components/chat/tools/blocks/ChartBlock.tsx
'use client'
import { ChartBlock as ChartBlockType, isSeriesChartConfig, isPieChartConfig } from '../types'

interface Props {
  block: ChartBlockType
}

export function ChartBlock({ block }: Props) {
  const config = block.config

  // Add null/undefined check
  if (!config) {
    return (
      <div className="card p-6">
        <div className="h-64 flex items-center justify-center bg-neutral-100 dark:bg-neutral-800 rounded-lg">
          <div className="text-neutral-500">Chart configuration missing</div>
        </div>
      </div>
    )
  }

  // This is a placeholder implementation
  // In a real app, you'd use a charting library like Recharts, Chart.js, or D3
  const renderChart = () => {
    if (isSeriesChartConfig(config)) {
      return (
        <div className="h-64 flex items-center justify-center bg-neutral-100 dark:bg-neutral-800 rounded-lg">
          <div className="text-center">
            <div className="text-lg font-medium text-neutral-700 dark:text-neutral-300">
              {config.chartType.toUpperCase()} Chart
            </div>
            <div className="text-sm text-neutral-500 mt-1">
              {config.series.length} series • {config.series[0]?.data.length || 0} data points
            </div>
            <div className="text-xs text-neutral-400 mt-2">
              X: {config.xField} • Y: {config.yField}
            </div>
          </div>
        </div>
      )
    }

    if (isPieChartConfig(config)) {
      return (
        <div className="h-64 flex items-center justify-center bg-neutral-100 dark:bg-neutral-800 rounded-lg">
          <div className="text-center">
            <div className="text-lg font-medium text-neutral-700 dark:text-neutral-300">
              {config.chartType.toUpperCase()} Chart
            </div>
            <div className="text-sm text-neutral-500 mt-1">
              {config.data?.length || 0} segments
            </div>
            <div className="text-xs text-neutral-400 mt-2">
              Label: {config.labelField} • Value: {config.valueField}
            </div>
          </div>
        </div>
      )
    }

    return (
      <div className="h-64 flex items-center justify-center bg-neutral-100 dark:bg-neutral-800 rounded-lg">
        <div className="text-neutral-500">Unknown chart type</div>
      </div>
    )
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
        {config.title || 'Chart'}
      </h3>
      
      {renderChart()}
      
      {/* Chart Legend for Series Charts */}
      {isSeriesChartConfig(config) && config.series.length > 1 && (
        <div className="flex flex-wrap gap-4 mt-4 justify-center">
          {config.series.map((series, index) => (
            <div key={index} className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: `hsl(${index * 60}, 70%, 50%)` }}
              />
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                {series.name}
              </span>
            </div>
          ))}
        </div>
      )}
      
      <div className="text-xs text-neutral-400 mt-4 text-center">
        Chart component placeholder - integrate with your preferred charting library
      </div>
    </div>
  )
}