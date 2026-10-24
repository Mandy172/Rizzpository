import { Check, RotateCcw, Truck } from 'lucide-react'
import type { TicketStatus } from '@/lib/types'
import { cn } from '@/lib/utils'

interface TicketActionsProps {
  status: TicketStatus
  onStatusChange: (status: TicketStatus) => void
  label: string
  className?: string
}

const base =
  'inline-flex h-8 shrink-0 items-center whitespace-nowrap gap-1.5 rounded-lg px-2.5 text-[12px] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60 disabled:pointer-events-none disabled:opacity-40'

export function TicketActions({ status, onStatusChange, label, className }: TicketActionsProps) {
  if (status === 'resolved') {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <button
          type="button"
          onClick={() => onStatusChange('open')}
          className={cn(base, 'text-muted-foreground hover:bg-muted hover:text-foreground')}
          aria-label={`Reopen ${label}`}
        >
          <RotateCcw className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
          Reopen
        </button>
      </div>
    )
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <button
        type="button"
        disabled={status === 'dispatched'}
        onClick={() => onStatusChange('dispatched')}
        className={cn(base, 'border border-border bg-card text-foreground/90 hover:border-ring/50 hover:bg-muted')}
        aria-label={`Dispatch crew to ${label}`}
      >
        <Truck className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
        {status === 'dispatched' ? 'Dispatched' : 'Dispatch crew'}
      </button>
      <button
        type="button"
        onClick={() => onStatusChange('resolved')}
        className={cn(base, 'border border-transparent text-muted-foreground hover:bg-muted hover:text-foreground')}
        aria-label={`Resolve ${label}`}
      >
        <Check className="size-3.5" strokeWidth={2} aria-hidden="true" />
        Resolve
      </button>
    </div>
  )
}
