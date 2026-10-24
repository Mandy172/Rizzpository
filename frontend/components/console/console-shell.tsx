'use client'

import { useDeferredValue, useMemo, useState } from 'react'
import { buildTickets, matchesFilters, matchesQuery } from '@/lib/triage'
import type { Filters, RawComplaint, TicketStatus } from '@/lib/types'
import { CategoryBreakdown } from './category-breakdown'
import { EMPTY_FILTERS, FilterBar } from './filter-bar'
import { KpiCards } from './kpi-cards'
import { MainFeed } from './main-feed'
import { TopNav } from './top-nav'

export function ConsoleShell({ complaints }: { complaints: RawComplaint[] }) {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)
  const [statuses, setStatuses] = useState<Record<string, TicketStatus>>({})

  const [query, setQuery] = useState('')
  const deferredQuery = useDeferredValue(query)

  const filtered = useMemo(
    () => complaints.filter((c) => matchesFilters(c, filters) && matchesQuery(c, deferredQuery)),
    [complaints, filters, deferredQuery],
  )
  const tickets = useMemo(() => buildTickets(filtered), [filtered])

  const kpis = useMemo(() => {
    const open = tickets.filter((t) => (statuses[t.key] ?? 'open') === 'open')
    const groups = tickets.filter((t) => t.clusterId !== null)
    return {
      reports: filtered.length,
      uniqueTickets: tickets.length,
      awaitingDispatch: open.filter((t) => !t.needsReview).length,
      urgent: open.filter((t) => t.severity >= 4).length,
      review: open.filter((t) => t.needsReview).length,
      groups: groups.length,
      linkedReports: groups.reduce((sum, g) => sum + g.reports.length, 0),
    }
  }, [filtered, tickets, statuses])

  function updateStatus(key: string, status: TicketStatus) {
    setStatuses((prev) => ({ ...prev, [key]: status }))
  }

  return (
    <div className="min-h-dvh bg-background">
      <TopNav />
      <main className="mx-auto flex max-w-[1440px] flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8 lg:py-6">
        <FilterBar
          filters={filters}
          onChange={setFilters}
          query={query}
          onQueryChange={setQuery}
          visibleReports={filtered.length}
          activeGroups={kpis.groups}
        />
        <KpiCards values={kpis} />
        <CategoryBreakdown reports={filtered} />
        <MainFeed tickets={tickets} statuses={statuses} onStatusChange={updateStatus} />
      </main>
    </div>
  )
}
