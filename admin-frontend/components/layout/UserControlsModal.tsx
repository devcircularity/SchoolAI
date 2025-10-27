'use client'
import { useEffect } from 'react'
import Link from 'next/link'

export default function UserControlsModal({
  open,
  onClose,
  onLogout,
  userLabel,
  email,
  schoolId,
}: {
  open: boolean
  onClose: () => void
  onLogout: () => void
  userLabel?: string
  email?: string
  schoolId?: string | number | null
}) {
  // Close on ESC
  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose() }
    if (open) document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  const initial = (userLabel || email || 'U').slice(0,1).toUpperCase()

  return (
    <>
      {/* Backdrop – click anywhere to close */}
      <div
        className="fixed inset-0 z-[90] bg-black/40 backdrop-blur-[2px]"
        onClick={onClose}
      />

      {/* Panel pinned to top-right (Google-like) */}
      <div
        className="fixed right-4 top-16 z-[100] w-[360px] sm:w-[380px]
                   rounded-[1.25rem] card border border-neutral-200/60
                   overflow-hidden shadow-[var(--shadow-soft)]"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="relative px-4 py-3 bg-neutral-900/5 dark:bg-white/5">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[--color-brand] text-white font-semibold">
              {initial}
            </span>
            <div className="min-w-0">
              {email && <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">{email}</div>}
              <div className="text-sm font-medium truncate">{userLabel || 'User'}</div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="absolute right-3 top-3 text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Greeting + primary CTA */}
        <div className="px-5 pt-4 pb-3">
          <div className="text-lg font-semibold">Hi{userLabel ? `, ${userLabel.split(' ')[0]}!` : '!'}</div>
          <button
            className="mt-3 btn-primary w-full rounded-xl py-2.5"
            onClick={() => alert('Manage account (stub)')}
          >
            Manage your Account
          </button>
        </div>

        {/* Optional tip card (stub, like Google’s) */}
        <div className="mx-4 mb-3 rounded-2xl bg-neutral-100 dark:bg-neutral-800 p-4">
          <div className="flex items-start gap-3">
            <div className="text-xl leading-none">🏠</div>
            <div className="text-sm">
              <div className="font-medium">Set your school & year</div>
              <div className="text-neutral-600 dark:text-neutral-400">
                Pick active school and academic year for better results.
              </div>
              <div className="mt-2 flex gap-3">
                <button className="btn rounded-lg px-3 py-1.5 hover:bg-neutral-200 dark:hover:bg-neutral-700">Dismiss</button>
                <button className="link-subtle">Open settings</button>
              </div>
            </div>
          </div>
        </div>

        {/* Row: Add account | Sign out */}
        <div className="px-4">
          <div className="grid grid-cols-2 gap-2">
            <button
              className="btn rounded-xl px-3 py-2 bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700"
              onClick={() => alert('Add account (stub)')}
            >
              + Add account
            </button>
            <button
              className="btn rounded-xl px-3 py-2 bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700"
              onClick={() => { onClose(); onLogout(); }}
            >
              Sign out
            </button>
          </div>
        </div>

        {/* List items */}
        <div className="mt-3 px-2 pb-2">
          <ul className="grid gap-2">
            <li>
              <button className="w-full text-left rounded-xl px-3 py-2 hover:bg-neutral-100 dark:hover:bg-neutral-800">
                🔎 <span className="ml-2">Search history</span>
                <span className="float-right text-xs text-neutral-500">Not saving</span>
              </button>
            </li>
            <li>
              <button className="w-full text-left rounded-xl px-3 py-2 hover:bg-neutral-100 dark:hover:bg-neutral-800">
                📁 <span className="ml-2">Saves & Collections</span>
              </button>
            </li>
            <li>
              <button className="w-full text-left rounded-xl px-3 py-2 hover:bg-neutral-100 dark:hover:bg-neutral-800">
                ✨ <span className="ml-2">Search personalization</span>
              </button>
            </li>
            <li className="grid grid-cols-2 gap-2">
              <button className="rounded-xl px-3 py-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-left">
                🛡️ <span className="ml-2">SafeSearch</span>
                <div className="text-xs text-neutral-500 ml-7 -mt-1">Blurring on</div>
              </button>
              <button className="rounded-xl px-3 py-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-left">
                🌐 <span className="ml-2">Language</span>
                <div className="text-xs text-neutral-500 ml-7 -mt-1">English</div>
              </button>
            </li>
            <li className="grid grid-cols-2 gap-2">
              <button className="rounded-xl px-3 py-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-left">
                ⚙️ <span className="ml-2">More settings</span>
              </button>
              <button className="rounded-xl px-3 py-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-left">
                ❔ <span className="ml-2">Help</span>
              </button>
            </li>
          </ul>
        </div>

        {/* Footer */}
        <div className="px-4 py-3 flex items-center justify-between text-xs text-neutral-600 dark:text-neutral-400 border-t border-neutral-200/70 dark:border-white/10">
          <div>Privacy Policy</div>
          <div>Terms of Service</div>
        </div>
      </div>
    </>
  )
}