import type { Metadata } from 'next'
import { CitizenPortal } from '@/components/report/citizen-portal'

export const metadata: Metadata = {
  title: 'Report a civic issue · CivicSort',
  description: 'Submit a multilingual civic complaint to the CivicSort Ward 12 demo.',
}

export default function ReportPage() {
  return <CitizenPortal />
}
