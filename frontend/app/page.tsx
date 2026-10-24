import { LiveConsole } from '@/components/console/live-console'
import { complaints } from '@/lib/complaints-data'

export default function Page() {
  return <LiveConsole initial={complaints} />
}
