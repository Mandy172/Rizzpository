'use client'

import { Search, X } from 'lucide-react'
import { useEffect, useRef } from 'react'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
}

export function SearchInput({ value, onChange }: SearchInputProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
        inputRef.current?.select()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  return (
    <div className="group relative flex h-8 w-full items-center sm:w-72">
      <Search
        className="pointer-events-none absolute left-2.5 size-3.5 text-tertiary transition-colors group-focus-within:text-muted-foreground"
        strokeWidth={1.75}
        aria-hidden="true"
      />
      <label htmlFor="complaint-search" className="sr-only">
        Search complaints
      </label>
      <input
        ref={inputRef}
        id="complaint-search"
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            onChange('')
            e.currentTarget.blur()
          }
        }}
        placeholder="Search text, location, ID"
        autoComplete="off"
        spellCheck={false}
        className="h-full w-full rounded-lg border border-border bg-card pl-8 pr-14 text-[13px] text-foreground placeholder:text-tertiary transition-colors hover:border-foreground/15 focus-visible:border-foreground/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 [&::-webkit-search-cancel-button]:appearance-none"
      />
      {value ? (
        <button
          type="button"
          onClick={() => {
            onChange('')
            inputRef.current?.focus()
          }}
          aria-label="Clear search"
          className="absolute right-1.5 flex size-5 items-center justify-center rounded-[5px] text-tertiary transition-colors hover:bg-muted hover:text-foreground"
        >
          <X className="size-3" strokeWidth={2} />
        </button>
      ) : (
        <kbd
          aria-hidden="true"
          className="pointer-events-none absolute right-2 hidden h-5 items-center rounded-[5px] border border-border px-1.5 font-mono text-[10px] text-tertiary sm:flex"
        >
          Ctrl K
        </kbd>
      )}
    </div>
  )
}
