'use client'

import { Activity, Bell, ChevronDown, ChevronRight } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { ThemeToggle } from './theme-toggle'

const NOTIFICATIONS = [
  { title: 'Duplicate group expanded', body: 'Tilak Road water line now has 4 linked reports', time: '2m' },
  { title: 'Severity 5 hazard', body: 'Bus stop pothole — two-wheelers falling', time: '6m' },
  { title: 'Review requested', body: 'Injured stray dog in park flagged for an operator', time: '14m' },
]

export function TopNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/70">
      <div className="mx-auto flex h-14 max-w-[1440px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-8 shrink-0 items-center justify-center rounded-[10px] border border-border bg-card">
            <Activity className="size-4 text-foreground" strokeWidth={1.75} aria-hidden="true" />
          </div>
          <div className="flex min-w-0 items-center gap-2">
            <h1 className="truncate text-[15px] font-semibold tracking-[-0.01em]">Live operations</h1>
            <span className="shrink-0 whitespace-nowrap rounded-[5px] border border-border bg-muted px-1.5 py-px font-mono text-[10px] font-medium tracking-[0.08em] text-muted-foreground">
              PUNE PMC
            </span>
          </div>
          <nav aria-label="Breadcrumb" className="hidden items-center md:flex">
            <span className="mx-3 h-4 w-px bg-border" aria-hidden="true" />
            <ol className="flex items-center gap-1.5 text-[13px]">
              <li className="text-muted-foreground">Complaint triage</li>
              <li aria-hidden="true">
                <ChevronRight className="size-3.5 text-tertiary" strokeWidth={1.75} />
              </li>
              <li aria-current="page" className="text-foreground/90">
                Intake and dispatch
              </li>
            </ol>
          </nav>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <div
            className="hidden items-center gap-2 rounded-full border border-border bg-card px-2.5 py-1 sm:flex"
            role="status"
            aria-live="polite"
          >
            <span className="relative flex size-1.5">
              <span className="animate-live-ping absolute inline-flex size-full rounded-full bg-success" />
              <span className="relative inline-flex size-1.5 rounded-full bg-success" />
            </span>
            <span className="text-[12px] text-muted-foreground">
              <span className="text-foreground/80">Feed synced</span>
              <span className="text-tertiary"> · </span>
              just now
            </span>
          </div>

          <Popover>
            <PopoverTrigger
              aria-label="Notifications, 3 unread"
              className="relative flex size-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
            >
              <Bell className="size-4" strokeWidth={1.75} />
              <span className="absolute right-[7px] top-[7px] size-[7px] rounded-full border-[1.5px] border-background bg-danger" />
            </PopoverTrigger>
            <PopoverContent align="end" sideOffset={8} className="w-80 gap-0 p-0">
              <div className="flex items-center justify-between border-b border-border px-3.5 py-2.5">
                <p className="text-[13px] font-medium">Notifications</p>
                <span className="text-[11px] text-muted-foreground">3 unread</span>
              </div>
              <ul className="divide-y divide-border">
                {NOTIFICATIONS.map((n) => (
                  <li key={n.title} className="flex gap-3 px-3.5 py-3">
                    <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-foreground/70" aria-hidden="true" />
                    <div className="min-w-0 flex-1">
                      <p className="text-[13px] font-medium leading-tight">{n.title}</p>
                      <p className="mt-0.5 text-[12px] leading-snug text-muted-foreground">{n.body}</p>
                    </div>
                    <span className="font-mono text-[11px] text-tertiary">{n.time}</span>
                  </li>
                ))}
              </ul>
            </PopoverContent>
          </Popover>

          <ThemeToggle />

          <button
            type="button"
            className="flex items-center gap-1.5 rounded-full border border-border bg-card py-0.5 pl-0.5 pr-2 transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
            aria-label="Operator menu"
          >
            <span className="flex size-6 items-center justify-center rounded-full bg-foreground text-[10px] font-semibold tracking-wide text-background">
              OP
            </span>
            <span className="hidden text-[12px] font-medium text-foreground/80 lg:inline">Ward 12</span>
            <ChevronDown className="size-3 text-tertiary" strokeWidth={2} aria-hidden="true" />
          </button>
        </div>
      </div>
    </header>
  )
}
