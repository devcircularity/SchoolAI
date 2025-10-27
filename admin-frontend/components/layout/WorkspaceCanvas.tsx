//apps/frontend/components/layout/WorkspaceCanvas.tsx
'use client'

import React, { useEffect, useRef, useState } from 'react'

export default function CanvasPanel({
  open,
  width,
  onResize,
  onRequestClose,
}: {
  open: boolean
  width: number
  onResize: (w: number) => void
  onRequestClose: () => void
}) {
  const [dragging, setDragging] = useState(false)
  const startX = useRef(0)
  const startW = useRef(width)

  useEffect(() => { startW.current = width }, [width])

  useEffect(() => {
    function onMove(e: MouseEvent) {
      if (!dragging) return
      const dx = startX.current - e.clientX
      const next = Math.max(320, Math.min(800, startW.current + dx))
      onResize(next)
    }
    function onUp() { setDragging(false) }
    if (dragging) {
      document.addEventListener('mousemove', onMove)
      document.addEventListener('mouseup', onUp)
    }
    return () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
  }, [dragging, onResize])

  if (!open) return <div style={{ width: 0 }} />

  return (
    <>
      {/* Backdrop to swallow clicks in main area (click closes) */}
      <div
        className="absolute inset-0 z-[45]"
        onClick={onRequestClose}
      />

      {/* Panel */}
      <div
        className="relative z-[50] h-[calc(100svh-48px)] border-l border-neutral-200/70 dark:border-white/10 bg-white/80 dark:bg-neutral-900/70 backdrop-blur"
        style={{ width }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drag handle */}
        <div
          onMouseDown={(e) => { setDragging(true); startX.current = e.clientX; }}
          className="absolute left-0 top-0 h-full w-1 cursor-col-resize bg-transparent"
          title="Drag to resize"
        >
          <div className="absolute left-[-2px] top-1/2 -translate-y-1/2 h-10 w-[3px] rounded-full bg-neutral-300/70 dark:bg-neutral-700/70" />
        </div>

        <div className="h-full overflow-auto p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="font-medium">Canvas</div>
            <button
              onClick={onRequestClose}
              className="btn rounded-lg px-3 py-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800"
            >
              Close
            </button>
          </div>

          {/* Canvas content placeholder */}
          <div className="card p-4">
            <p className="text-sm text-neutral-700 dark:text-neutral-300">
              This area can show context, notes, inspector panels, or AI tools.
              Use the shell’s “Show Canvas” button or call the bus:
            </p>
            <pre className="mt-3 rounded-xl bg-neutral-100 dark:bg-neutral-800 p-3 text-xs overflow-auto">
{`import { CanvasBus } from '@/components/layout/WorkspaceShell'

// Open with a custom width
CanvasBus.send({ type: 'open', width: 520 })

// Toggle
CanvasBus.send({ type: 'toggle' })
`}
            </pre>
          </div>
        </div>
      </div>
    </>
  )
}