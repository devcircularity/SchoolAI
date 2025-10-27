// components/chat/tools/blocks/TextBlock.tsx
'use client'
import { TextBlock as TextBlockType } from '../types'

interface Props {
  block: TextBlockType
}

function formatText(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g)
  
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      const innerText = part.slice(2, -2)
      return <strong key={index}>{innerText}</strong>
    }
    
    if (part.startsWith('*') && part.endsWith('*') && !part.startsWith('**')) {
      const innerText = part.slice(1, -1)
      return <em key={index}>{innerText}</em>
    }
    
    if (part.startsWith('`') && part.endsWith('`')) {
      const innerText = part.slice(1, -1)
      return (
        <code 
          key={index} 
          className="bg-neutral-100 dark:bg-neutral-800 px-1 py-0.5 rounded text-sm font-mono"
        >
          {innerText}
        </code>
      )
    }
    
    return <span key={index}>{part}</span>
  })
}

export function TextBlock({ block }: Props) {
  const lines = block.text.split('\n')

  return (
    <div className="text-neutral-900 dark:text-neutral-100">
      {lines.map((line, lineIndex) => (
        <div key={lineIndex} className={lineIndex > 0 ? 'mt-4' : ''}>
          {line.trim() === '' ? (
            <div className="h-4" />
          ) : (
            <div className="leading-relaxed">
              {formatText(line)}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}