import { CATEGORY_META, CATEGORY_ORDER, asCategory } from '@/lib/triage'
import type { RawComplaint } from '@/lib/types'
import { cn } from '@/lib/utils'

export function CategoryBreakdown({ reports }: { reports: RawComplaint[] }) {
  const total = reports.length
  const rows = CATEGORY_ORDER.map((c) => ({
    key: c,
    ...CATEGORY_META[c],
    count: reports.filter((r) => asCategory(r.category) === c).length,
  })).filter((r) => r.key !== 'other' || r.count > 0)
  const max = Math.max(1, ...rows.map((r) => r.count))

  return (
    <section aria-labelledby="category-heading" className="rounded-xl border border-border bg-card">
      <div className="flex items-baseline justify-between gap-4 px-5 pb-3 pt-4">
        <div>
          <h2 id="category-heading" className="text-[14px] font-semibold tracking-[-0.005em]">
            Reports by category
          </h2>
          <p className="mt-0.5 text-[12px] text-muted-foreground">Current filtered intake</p>
        </div>
        <p className="font-mono text-[12px] text-tertiary tabular-nums">{total} total</p>
      </div>

      <div className="px-5">
        <div
          className="flex h-1.5 w-full gap-[2px] overflow-hidden rounded-full bg-muted"
          role="img"
          aria-label={rows.map((r) => `${r.label} ${r.count}`).join(', ')}
        >
          {total > 0 &&
            rows
              .filter((r) => r.count > 0)
              .map((r) => (
                <span
                  key={r.key}
                  className={cn('h-full transition-[width] duration-500', r.bar)}
                  style={{ width: `${(r.count / total) * 100}%` }}
                />
              ))}
        </div>
      </div>

      <ul className="mt-4 grid grid-cols-1 border-t border-border sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {rows.map((r) => {
          const pct = total ? Math.round((r.count / total) * 100) : 0
          return (
            <li
              key={r.key}
              className="flex flex-col gap-2.5 border-b border-border px-5 py-3.5 sm:border-r xl:border-b-0 xl:last:border-r-0"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="flex items-center gap-2 text-[13px] text-foreground/90">
                  <span className={cn('size-2 rounded-[3px]', r.dot)} aria-hidden="true" />
                  {r.label}
                </span>
                <span className="flex items-baseline gap-1.5 tabular-nums">
                  <span className="text-[13px] font-semibold">{r.count}</span>
                  <span className="font-mono text-[11px] text-tertiary">{pct}%</span>
                </span>
              </div>
              <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className={cn('h-full rounded-full transition-[width] duration-500', r.bar)}
                  style={{ width: `${(r.count / max) * 100}%` }}
                />
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
