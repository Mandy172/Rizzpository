import type { RawComplaint } from './types'

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export async function fetchComplaints(): Promise<RawComplaint[]> {
  const res = await fetch(`${API_URL}/complaints`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`API ${res.status}`)
  return res.json()
}

export async function submitComplaint(text: string): Promise<RawComplaint> {
  const res = await fetch(`${API_URL}/triage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error(`API ${res.status}`)
  return res.json()
}
