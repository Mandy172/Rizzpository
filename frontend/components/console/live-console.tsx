'use client'

import { useCallback, useEffect, useState } from 'react'
import { ConsoleShell } from '@/components/console/console-shell'
import { fetchComplaints, submitComplaint } from '@/lib/api'
import type { RawComplaint } from '@/lib/types'

export function LiveConsole({ initial }: { initial: RawComplaint[] }) {
  const [complaints, setComplaints] = useState<RawComplaint[]>(initial)
  const [online, setOnline] = useState(false)
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [last, setLast] = useState<RawComplaint | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      setComplaints(await fetchComplaints())
      setOnline(true)
    } catch {
      setOnline(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const timer = setInterval(refresh, 5000)
    return () => clearInterval(timer)
  }, [refresh])

  async function onSubmit() {
    if (!text.trim() || busy) return
    setBusy(true)
    setError(null)
    setLast(null)
    try {
      const record = await submitComplaint(text.trim())
      setLast(record)
      setText('')
      await refresh()
    } catch {
      setError('Could not reach the triage API.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <ConsoleShell complaints={complaints} />
      <div className="fixed bottom-4 right-4 z-50 flex w-[min(380px,calc(100vw-2rem))] flex-col items-end gap-2">
        {open && (
          <div className="w-full rounded-xl border border-border bg-card p-4 text-sm shadow-lg">
            <div className="mb-2 flex items-center justify-between">
              <span className="font-medium">Report a complaint</span>
              <span className={online ? 'text-xs text-emerald-500' : 'text-xs text-amber-500'}>
                {online ? 'Live: triage API connected' : 'Offline: showing snapshot'}
              </span>
            </div>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={3}
              placeholder="Type in English, Hindi, Marathi or Hinglish"
              className="w-full resize-none rounded-lg border border-border bg-background p-2 outline-none"
            />
            <button
              onClick={onSubmit}
              disabled={!online || busy || !text.trim()}
              className="mt-2 w-full rounded-lg bg-primary px-3 py-2 font-medium text-primary-foreground disabled:opacity-40"
            >
              {busy ? 'Triaging...' : 'Submit for triage'}
            </button>
            {!online && (
              <p className="mt-2 text-xs text-muted-foreground">
                Start the API: uvicorn backend.api:app --host 0.0.0.0 --port 8000
              </p>
            )}
            {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
            {last && (
              <div className="mt-3 rounded-lg border border-border p-2 text-xs">
                <div className="font-medium">
                  {last.category} · {last.department} · severity {last.severity}
                </div>
                <div className="mt-1 text-muted-foreground">{last.severity_reason}</div>
                <div className="mt-1 text-muted-foreground">Decided by: {(last as RawComplaint & { source?: string }).source ?? "unknown"}</div>
                <div className="mt-1 text-muted-foreground">
                  {last.needs_human_review ? 'Flagged for human review' : 'Routed automatically'}
                  {last.cluster_id >= 0 ? ` · linked to group ${last.cluster_id}` : ''}
                </div>
              </div>
            )}
          </div>
        )}
        <button
          onClick={() => setOpen((v) => !v)}
          className="rounded-full border border-border bg-card px-4 py-2 text-sm font-medium shadow-lg"
        >
          {open ? 'Close' : 'Report a complaint'}
        </button>
      </div>
    </>
  )
}
