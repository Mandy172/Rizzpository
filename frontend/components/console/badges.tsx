import { CATEGORY_META, DEPARTMENT_LABEL, LANGUAGE_META, asCategory, asDepartment, asLanguage } from '@/lib/triage'
import type { TicketStatus } from '@/lib/types'
import { cn } from '@/lib/utils'

const SEVERITY_TONE: Record<number, string> = {
  5: 'bg-danger/10 text-danger',
  4: 'bg-warning/10 text-warning',
  3: 'bg-muted text-foreground/80',
  2: 'bg-muted text-muted-foreground',
  1: 'bg-muted text-muted-foreground',
}

const SEVERITY_PIP: Record<number, string> = {
  5: 'bg-danger',
  4: 'bg-warning',
  3: 'bg-foreground/70',
  2: 'bg-muted-foreground',
  1: 'bg-muted-foreground',
}

export function SeverityBadge({ level }: { level: number }) {
  return (
    <span
      className={cn(
        'inline-flex h-[22px] items-center gap-1.5 rounded-md px-1.5 font-mono text-[11px] font-medium',
        SEVERITY_TONE[level],
      )}
      aria-label={`Severity ${level} of 5`}
    >
      <span className="flex items-end gap-[2px]" aria-hidden="true">
        {[1, 2, 3, 4, 5].map((i) => (
          <span
            key={i}
            className={cn('w-[3px] rounded-[1px]', i <= level ? SEVERITY_PIP[level] : 'bg-current opacity-20')}
            style={{ height: 4 + i * 1.5 }}
          />
        ))}
      </span>
      S{level}
    </span>
  )
}

export function CategoryPill({ category }: { category: string }) {
  const meta = CATEGORY_META[asCategory(category)]
  return (
    <span className="inline-flex h-[22px] items-center gap-1.5 rounded-md bg-muted px-2 text-[12px] text-foreground/80">
      <span className={cn('size-1.5 rounded-full', meta.dot)} aria-hidden="true" />
      {meta.label}
    </span>
  )
}

export function DepartmentPill({ department }: { department: string }) {
  return (
    <span className="inline-flex h-[22px] items-center rounded-md bg-muted px-2 text-[12px] text-muted-foreground">
      {DEPARTMENT_LABEL[asDepartment(department)]}
    </span>
  )
}

export function LanguageTag({ language, compact = false }: { language: string; compact?: boolean }) {
  const meta = LANGUAGE_META[asLanguage(language)]
  return (
    <span
      className="inline-flex h-[22px] items-center rounded-md border border-border px-1.5 text-[11px] font-medium text-muted-foreground"
      title={meta.label}
    >
      {compact ? <span className="font-mono">{meta.short}</span> : meta.label}
    </span>
  )
}

export function StatusPill({ status }: { status: TicketStatus }) {
  if (status === 'open') return null
  return (
    <span
      className={cn(
        'inline-flex h-[22px] items-center gap-1.5 rounded-md px-2 text-[12px] font-medium',
        status === 'dispatched' ? 'bg-foreground/[0.06] text-foreground/90' : 'bg-success/10 text-success',
      )}
    >
      <span
        className={cn('size-1.5 rounded-full', status === 'dispatched' ? 'bg-foreground/70' : 'bg-success')}
        aria-hidden="true"
      />
      {status === 'dispatched' ? 'Crew dispatched' : 'Resolved'}
    </span>
  )
}
