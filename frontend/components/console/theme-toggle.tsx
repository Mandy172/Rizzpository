'use client'

import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { useSyncExternalStore } from 'react'
import { cn } from '@/lib/utils'

const subscribe = () => () => {}

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const mounted = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  )
  const isDark = !mounted || resolvedTheme !== 'light'

  function toggle() {
    const root = document.documentElement
    root.classList.add('theme-transition')
    setTheme(isDark ? 'light' : 'dark')
    window.setTimeout(() => root.classList.remove('theme-transition'), 360)
  }

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      onClick={toggle}
      className="relative inline-flex h-7 w-[52px] shrink-0 items-center rounded-full border border-border bg-muted p-0.5 transition-colors hover:border-ring/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60"
    >
      <Sun
        aria-hidden="true"
        className={cn(
          'absolute left-[7px] size-3.5 transition-opacity',
          isDark ? 'text-tertiary opacity-100' : 'opacity-0',
        )}
        strokeWidth={1.75}
      />
      <Moon
        aria-hidden="true"
        className={cn(
          'absolute right-[7px] size-3.5 transition-opacity',
          isDark ? 'opacity-0' : 'text-tertiary opacity-100',
        )}
        strokeWidth={1.75}
      />
      <span
        aria-hidden="true"
        className={cn(
          'relative z-10 flex size-[22px] items-center justify-center rounded-full bg-card shadow-[0_1px_2px_rgb(0_0_0/0.18),0_0_0_0.5px_rgb(0_0_0/0.06)] transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)]',
          isDark ? 'translate-x-[24px]' : 'translate-x-0',
        )}
      >
        {isDark ? (
          <Moon className="size-3 text-foreground" strokeWidth={2} />
        ) : (
          <Sun className="size-3 text-foreground" strokeWidth={2} />
        )}
      </span>
    </button>
  )
}
