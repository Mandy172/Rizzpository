import { Combine } from 'lucide-react'
import { LANGUAGE_META, asLanguage, ticketTitle } from '@/lib/triage'
import type { Ticket, TicketStatus } from '@/lib/types'
import { cn } from '@/lib/utils'
import { CategoryPill, DepartmentPill, LanguageTag, SeverityBadge, StatusPill } from './badges'
import { TicketActions } from './ticket-actions'

interface DuplicateGroupsProps {
  groups: Ticket[]
  statuses: Record<string, TicketStatus>
  onStatusChange: (key: string, status: TicketStatus) => void
}

export function DuplicateGroups({ groups, statuses, onStatusChange }: DuplicateGroupsProps) {
  if (groups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 px-6 py-16 text-center">
        <Combine className="size-5 text-tertiary" strokeWidth={1.5} aria-hidden="true" />
        <p className="text-[13px] font-medium">No duplicate groups in this view</p>
        <p className="text-[12px] text-muted-foreground">Adjust filters to see clustered reports.</p>
      </div>
    )
  }

  return (
    <ul className="grid grid-cols-1 gap-3 p-4 sm:p-5 lg:grid-cols-2">
      {groups.map((g) => {
        const status = statuses[g.key] ?? 'open'
        const title = ticketTitle(g)
        return (
          <li
            key={g.key}
            className={cn('flex flex-col rounded-xl border border-border bg-subtle', status === 'resolved' && 'opacity-60')}
          >
            <div className="flex items-start justify-between gap-3 px-4 pt-4">
              <div className="min-w-0">
                <p className="font-mono text-[11px] text-tertiary">{g.key}</p>
                <h3 className="mt-1 truncate text-[14px] font-semibold tracking-[-0.005em]">{title}</h3>
              </div>
              <div className="flex shrink-0 flex-col items-end">
                <span className="font-mono text-[22px] font-semibold leading-none tabular-nums">{g.reports.length}</span>
                <span className="mt-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-tertiary">reports</span>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-1.5 px-4">
              <SeverityBadge level={g.severity} />
              <CategoryPill category={g.primary.category} />
              <DepartmentPill department={g.primary.department} />
              <StatusPill status={status} />
            </div>

            <ul className="mx-4 mt-4 divide-y divide-border overflow-hidden rounded-lg border border-border bg-card">
              {g.reports.map((r) => (
                <li key={r.id} className="flex items-start gap-2.5 px-3 py-2.5">
                  <LanguageTag language={r.language} compact />
                  <p
                    lang={LANGUAGE_META[asLanguage(r.language)].htmlLang}
                    className="min-w-0 flex-1 text-[13px] leading-relaxed text-foreground/90"
                  >
                    {r.text}
                  </p>
                  <span className="mt-0.5 shrink-0 font-mono text-[10px] text-tertiary">{r.id}</span>
                </li>
              ))}
            </ul>

            <div className="mt-auto flex flex-wrap items-center justify-between gap-x-3 gap-y-2 px-4 py-3.5">
              <p className="whitespace-nowrap text-[12px] text-muted-foreground">
                Priority <span className="font-mono font-medium text-foreground/80">{g.priority}</span>
                <span className="mx-1.5 text-tertiary">·</span>
                {g.languages.length} {g.languages.length === 1 ? 'language' : 'languages'}
              </p>
              <TicketActions status={status} onStatusChange={(s) => onStatusChange(g.key, s)} label={title} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}
