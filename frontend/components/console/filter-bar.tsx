'use client'

import { Check, ChevronDown, ListFilter, X } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import {
  CATEGORY_META,
  CATEGORY_ORDER,
  DEPARTMENT_LABEL,
  DEPARTMENT_ORDER,
  LANGUAGE_META,
  LANGUAGE_ORDER,
  SEVERITY_LEVELS,
  activeFilterCount,
} from '@/lib/triage'
import type { Filters } from '@/lib/types'
import { cn } from '@/lib/utils'
import { SearchInput } from './search-input'

interface FilterBarProps {
  filters: Filters
  onChange: (next: Filters) => void
  query: string
  onQueryChange: (value: string) => void
  visibleReports: number
  activeGroups: number
}

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value]
}

export const EMPTY_FILTERS: Filters = { categories: [], departments: [], languages: [], severities: [] }

export function FilterBar({
  filters,
  onChange,
  query,
  onQueryChange,
  visibleReports,
  activeGroups,
}: FilterBarProps) {
  const count = activeFilterCount(filters)

  const chips: { label: string; remove: () => void }[] = [
    ...filters.categories.map((c) => ({
      label: CATEGORY_META[c].label,
      remove: () => onChange({ ...filters, categories: toggle(filters.categories, c) }),
    })),
    ...filters.departments.map((d) => ({
      label: DEPARTMENT_LABEL[d],
      remove: () => onChange({ ...filters, departments: toggle(filters.departments, d) }),
    })),
    ...filters.languages.map((l) => ({
      label: LANGUAGE_META[l].label,
      remove: () => onChange({ ...filters, languages: toggle(filters.languages, l) }),
    })),
    ...filters.severities.map((s) => ({
      label: `Severity ${s}`,
      remove: () => onChange({ ...filters, severities: toggle(filters.severities, s) }),
    })),
  ]

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 flex-wrap items-center gap-2">
        <SearchInput value={query} onChange={onQueryChange} />
        <Popover>
          <PopoverTrigger
            className={cn(
              'inline-flex h-8 items-center gap-1.5 rounded-lg border border-border bg-card px-2.5 text-[13px] font-medium text-foreground/90 transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60',
              'data-[popup-open]:bg-muted',
            )}
          >
            <ListFilter className="size-3.5 text-muted-foreground" strokeWidth={1.75} aria-hidden="true" />
            Filters
            {count > 0 && (
              <span className="flex h-4 min-w-4 items-center justify-center rounded-[4px] bg-foreground px-1 font-mono text-[10px] font-medium text-background">
                {count}
              </span>
            )}
            <ChevronDown className="size-3.5 text-tertiary" strokeWidth={1.75} aria-hidden="true" />
          </PopoverTrigger>
          <PopoverContent align="start" sideOffset={6} className="w-[340px] gap-0 p-0">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <p className="text-[13px] font-semibold">Filter intake</p>
              <button
                type="button"
                disabled={count === 0}
                onClick={() => onChange(EMPTY_FILTERS)}
                className="text-[12px] text-muted-foreground transition-colors hover:text-foreground disabled:opacity-40"
              >
                Clear all
              </button>
            </div>

            <div className="flex max-h-[60vh] flex-col gap-4 overflow-y-auto px-4 py-4">
              <FilterGroup label="Category">
                {CATEGORY_ORDER.map((c) => (
                  <FilterOption
                    key={c}
                    selected={filters.categories.includes(c)}
                    onClick={() => onChange({ ...filters, categories: toggle(filters.categories, c) })}
                  >
                    <span className={cn('size-1.5 rounded-full', CATEGORY_META[c].dot)} aria-hidden="true" />
                    {CATEGORY_META[c].label}
                  </FilterOption>
                ))}
              </FilterGroup>
              <FilterGroup label="Department">
                {DEPARTMENT_ORDER.map((d) => (
                  <FilterOption
                    key={d}
                    selected={filters.departments.includes(d)}
                    onClick={() => onChange({ ...filters, departments: toggle(filters.departments, d) })}
                  >
                    {DEPARTMENT_LABEL[d]}
                  </FilterOption>
                ))}
              </FilterGroup>
              <FilterGroup label="Language">
                {LANGUAGE_ORDER.map((l) => (
                  <FilterOption
                    key={l}
                    selected={filters.languages.includes(l)}
                    onClick={() => onChange({ ...filters, languages: toggle(filters.languages, l) })}
                  >
                    {LANGUAGE_META[l].label}
                  </FilterOption>
                ))}
              </FilterGroup>
              <FilterGroup label="Severity">
                {SEVERITY_LEVELS.map((s) => (
                  <FilterOption
                    key={s}
                    selected={filters.severities.includes(s)}
                    onClick={() => onChange({ ...filters, severities: toggle(filters.severities, s) })}
                  >
                    <span className="font-mono">S{s}</span>
                  </FilterOption>
                ))}
              </FilterGroup>
            </div>
          </PopoverContent>
        </Popover>

        {chips.map((chip) => (
          <span
            key={chip.label}
            className="inline-flex h-7 items-center gap-1 rounded-md border border-border bg-card pl-2 pr-1 text-[12px] text-foreground/80"
          >
            {chip.label}
            <button
              type="button"
              onClick={chip.remove}
              aria-label={`Remove ${chip.label} filter`}
              className="flex size-4 items-center justify-center rounded-[4px] text-tertiary transition-colors hover:bg-muted hover:text-foreground"
            >
              <X className="size-3" strokeWidth={2} />
            </button>
          </span>
        ))}
      </div>

      <p className="shrink-0 text-[12px] text-muted-foreground tabular-nums">
        <span className="font-medium text-foreground/80">{visibleReports}</span> reports visible
        <span className="mx-1.5 text-tertiary">·</span>
        <span className="font-medium text-foreground/80">{activeGroups}</span> duplicate groups active
      </p>
    </div>
  )
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <fieldset>
      <legend className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-tertiary">{label}</legend>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </fieldset>
  )
}

function FilterOption({
  selected,
  onClick,
  children,
}: {
  selected: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={cn(
        'inline-flex h-7 items-center gap-1.5 rounded-md border px-2 text-[12px] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60',
        selected
          ? 'border-foreground/25 bg-foreground/[0.06] text-foreground'
          : 'border-border text-muted-foreground hover:bg-muted hover:text-foreground',
      )}
    >
      {selected && <Check className="size-3" strokeWidth={2.25} aria-hidden="true" />}
      {children}
    </button>
  )
}
