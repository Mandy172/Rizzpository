'use client'

import { Inbox } from 'lucide-react'
import { useState } from 'react'
import type { Ticket, TicketStatus } from '@/lib/types'
import { cn } from '@/lib/utils'
import { DuplicateGroups } from './duplicate-groups'
import { TicketRow } from './ticket-row'

type Tab = 'queue' | 'groups'
type StatusView = 'open' | 'dispatched' | 'resolved' | 'all'

interface MainFeedProps {
  tickets: Ticket[]
  statuses: Record<string, TicketStatus>
  onStatusChange: (key: string, status: TicketStatus) => void
}

const STATUS_VIEWS: { value: StatusView; label: string }[] = [
  { value: 'open', label: 'Open' },
  { value: 'dispatched', label: 'Dispatched' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'all', label: 'All' },
]

export function MainFeed({ tickets, statuses, onStatusChange }: MainFeedProps) {
  const [tab, setTab] = useState<Tab>('queue')
  const [view, setView] = useState<StatusView>('open')

  const statusOf = (t: Ticket) => statuses[t.key] ?? 'open'
  const groups = tickets.filter((t) => t.clusterId !== null)
  const visible = view === 'all' ? tickets : tickets.filter((t) => statusOf(t) === view)
  const counts = {
    open: tickets.filter((t) => statusOf(t) === 'open').length,
    dispatched: tickets.filter((t) => statusOf(t) === 'dispatched').length,
    resolved: tickets.filter((t) => statusOf(t) === 'resolved').length,
    all: tickets.length,
  }

  const tabs: { value: Tab; label: string; count: number }[] = [
    { value: 'queue', label: 'Priority queue', count: counts.open },
    { value: 'groups', label: 'Duplicate groups', count: groups.length },
  ]

  return (
    <section aria-label="Complaint feed" className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="flex flex-col gap-3 border-b border-border px-4 pt-3 sm:flex-row sm:items-end sm:justify-between sm:px-5">
        <div role="tablist" aria-label="Feed view" className="-mb-px flex items-center gap-5">
          {tabs.map((t) => (
            <button
              key={t.value}
              type="button"
              role="tab"
              id={`tab-${t.value}`}
              aria-selected={tab === t.value}
              aria-controls={`panel-${t.value}`}
              onClick={() => setTab(t.value)}
              className={cn(
                'flex items-center gap-2 border-b-[1.5px] pb-3 pt-1 text-[13px] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60',
                tab === t.value
                  ? 'border-foreground text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground',
              )}
            >
              {t.label}
              <span
                className={cn(
                  'rounded-[5px] px-1.5 py-px font-mono text-[11px] tabular-nums',
                  tab === t.value ? 'bg-foreground/[0.08] text-foreground' : 'bg-muted text-muted-foreground',
                )}
              >
                {t.count}
              </span>
            </button>
          ))}
        </div>

        {tab === 'queue' && (
          <div
            role="radiogroup"
            aria-label="Ticket status"
            className="mb-2.5 flex w-fit items-center rounded-lg border border-border bg-subtle p-0.5"
          >
            {STATUS_VIEWS.map((s) => (
              <button
                key={s.value}
                type="button"
                role="radio"
                aria-checked={view === s.value}
                onClick={() => setView(s.value)}
                className={cn(
                  'flex h-6 items-center gap-1.5 rounded-md px-2 text-[12px] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60',
                  view === s.value
                    ? 'bg-card font-medium text-foreground shadow-[0_0_0_1px_var(--border),0_1px_2px_rgb(0_0_0/0.06)]'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {s.label}
                <span className="font-mono text-[10px] text-tertiary tabular-nums">{counts[s.value]}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
        {tab === 'queue' ? (
          visible.length > 0 ? (
            <ul className="divide-y divide-border">
              {visible.map((t) => (
                <TicketRow
                  key={t.key}
                  ticket={t}
                  status={statusOf(t)}
                  onStatusChange={(s) => onStatusChange(t.key, s)}
                />
              ))}
            </ul>
          ) : (
            <div className="flex flex-col items-center justify-center gap-2 px-6 py-16 text-center">
              <Inbox className="size-5 text-tertiary" strokeWidth={1.5} aria-hidden="true" />
              <p className="text-[13px] font-medium">Nothing here</p>
              <p className="text-[12px] text-muted-foreground">No tickets match this search, status and filter combination.</p>
            </div>
          )
        ) : (
          <DuplicateGroups groups={groups} statuses={statuses} onStatusChange={onStatusChange} />
        )}
      </div>
    </section>
  )
}
