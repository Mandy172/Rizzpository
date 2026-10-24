'use client'

import { ChevronDown, Layers, MapPin, ScanEye } from 'lucide-react'
import { useState } from 'react'
import { LANGUAGE_META, asLanguage, ticketTitle } from '@/lib/triage'
import type { Ticket, TicketStatus } from '@/lib/types'
import { cn } from '@/lib/utils'
import { CategoryPill, DepartmentPill, LanguageTag, SeverityBadge, StatusPill } from './badges'
import { TicketActions } from './ticket-actions'

interface TicketRowProps {
  ticket: Ticket
  status: TicketStatus
  onStatusChange: (status: TicketStatus) => void
}

export function TicketRow({ ticket, status, onStatusChange }: TicketRowProps) {
  const [expanded, setExpanded] = useState(false)
  const { primary } = ticket
  const linked = ticket.reports.length
  const title = ticketTitle(ticket)
  const resolved = status === 'resolved'
  const urgent = ticket.priority >= 80 && !resolved

  return (
    <li className={cn('group relative transition-colors hover:bg-subtle', resolved && 'opacity-60')}>
      <div className="flex flex-col gap-4 px-4 py-4 sm:px-5 lg:flex-row lg:items-start">
        <div className="flex shrink-0 items-center gap-3 lg:w-14 lg:flex-col lg:items-start lg:gap-1.5">
          <span
            className={cn(
              'font-mono text-[22px] font-semibold leading-none tracking-tight tabular-nums',
              urgent ? 'text-foreground' : 'text-foreground/70',
            )}
            aria-label={`Priority score ${ticket.priority}`}
          >
            {ticket.priority}
          </span>
          <span className="h-[3px] w-12 overflow-hidden rounded-full bg-muted" aria-hidden="true">
            <span
              className={cn('block h-full rounded-full', urgent ? 'bg-danger' : 'bg-foreground/40')}
              style={{ width: `${ticket.priority}%` }}
            />
          </span>
          <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-tertiary lg:hidden">
            Priority
          </span>
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1 font-mono text-[11px] text-tertiary">{ticket.clusterId !== null ? ticket.key : primary.id}</span>
            <SeverityBadge level={ticket.severity} />
            <CategoryPill category={primary.category} />
            <DepartmentPill department={primary.department} />
            <LanguageTag language={primary.language} />
            {ticket.needsReview && (
              <span className="inline-flex h-[22px] items-center gap-1 rounded-md bg-warning/10 px-2 text-[12px] font-medium text-warning">
                <ScanEye className="size-3" strokeWidth={2} aria-hidden="true" />
                Needs review
              </span>
            )}
            <StatusPill status={status} />
          </div>

          <p
            lang={LANGUAGE_META[asLanguage(primary.language)].htmlLang}
            className={cn('mt-2.5 text-pretty text-[14px] leading-relaxed text-foreground', resolved && 'line-through decoration-foreground/30')}
          >
            {primary.text}
          </p>

          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[12px] text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <MapPin className="size-3" strokeWidth={1.75} aria-hidden="true" />
              {title}
            </span>
            <span className="hidden text-tertiary sm:inline" aria-hidden="true">
              ·
            </span>
            <span className="text-pretty">{primary.severity_reason}</span>
          </div>

          {linked > 1 && (
            <div className="mt-3">
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                aria-expanded={expanded}
                className="inline-flex h-7 items-center gap-1.5 rounded-md border border-border bg-card px-2 text-[12px] font-medium text-foreground/80 transition-colors hover:bg-muted"
              >
                <Layers className="size-3.5 text-muted-foreground" strokeWidth={1.75} aria-hidden="true" />
                {linked} citizen reports linked
                <span className="font-mono text-[10px] font-normal text-tertiary">
                  {ticket.languages.map((l) => LANGUAGE_META[l].short).join(' ')}
                </span>
                <ChevronDown
                  className={cn('size-3.5 text-tertiary transition-transform', expanded && 'rotate-180')}
                  strokeWidth={1.75}
                  aria-hidden="true"
                />
              </button>

              {expanded && (
                <ul className="mt-2 flex flex-col gap-px overflow-hidden rounded-lg border border-border">
                  {ticket.reports.slice(1).map((r) => (
                    <li key={r.id} className="flex items-start gap-3 bg-subtle px-3 py-2.5">
                      <span className="mt-0.5 w-14 shrink-0 font-mono text-[11px] text-tertiary">{r.id}</span>
                      <LanguageTag language={r.language} compact />
                      <p
                        lang={LANGUAGE_META[asLanguage(r.language)].htmlLang}
                        className="min-w-0 flex-1 text-[13px] leading-relaxed text-foreground/85"
                      >
                        {r.text}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        <TicketActions
          status={status}
          onStatusChange={onStatusChange}
          label={title}
          className="shrink-0 lg:pt-0.5"
        />
      </div>
    </li>
  )
}
