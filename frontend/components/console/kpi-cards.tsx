import { Combine, Hourglass, Inbox, ScanEye, TriangleAlert, type LucideIcon } from 'lucide-react'

export interface KpiValues {
  reports: number
  uniqueTickets: number
  awaitingDispatch: number
  urgent: number
  review: number
  groups: number
  linkedReports: number
}

interface Kpi {
  label: string
  value: number
  hint: string
  icon: LucideIcon
  tone?: 'danger' | 'warning'
}

export function KpiCards({ values }: { values: KpiValues }) {
  const kpis: Kpi[] = [
    { label: 'Citizen reports', value: values.reports, hint: `${values.uniqueTickets} unique tickets`, icon: Inbox },
    { label: 'Awaiting dispatch', value: values.awaitingDispatch, hint: 'ready for assignment', icon: Hourglass },
    {
      label: 'Urgent hazards',
      value: values.urgent,
      hint: 'severity 4–5 · open',
      icon: TriangleAlert,
      tone: 'danger',
    },
    { label: 'Human review', value: values.review, hint: 'needs an operator', icon: ScanEye, tone: 'warning' },
    {
      label: 'Duplicate groups',
      value: values.groups,
      hint: `${values.linkedReports} reports linked by AI`,
      icon: Combine,
    },
  ]

  return (
    <section aria-label="Key metrics" className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
      {kpis.map((kpi, i) => (
        <article
          key={kpi.label}
          className={
            'flex flex-col rounded-xl border border-border bg-card p-4 ' + (i === 0 ? 'col-span-2 md:col-span-1' : '')
          }
        >
          <div className="flex items-start justify-between gap-2">
            <h3 className="pt-0.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
              {kpi.label}
            </h3>
            <span className="flex size-7 shrink-0 items-center justify-center rounded-lg border border-border bg-subtle">
              <kpi.icon
                className={
                  'size-3.5 ' +
                  (kpi.tone === 'danger' && kpi.value > 0
                    ? 'text-danger'
                    : kpi.tone === 'warning' && kpi.value > 0
                      ? 'text-warning'
                      : 'text-muted-foreground')
                }
                strokeWidth={1.75}
                aria-hidden="true"
              />
            </span>
          </div>
          <p className="mt-3 text-3xl font-bold tracking-tight tabular-nums">{kpi.value}</p>
          <p className="mt-1 text-[12px] text-muted-foreground">{kpi.hint}</p>
        </article>
      ))}
    </section>
  )
}
