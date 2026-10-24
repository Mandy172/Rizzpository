import { ConsoleShell } from '@/components/console/console-shell'
import { complaints } from '@/lib/complaints-data'

export default function Page() {
  return <ConsoleShell complaints={complaints} />
}
