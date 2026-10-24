'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import { CheckCircle2, ChevronLeft, ClipboardCheck, FileImage, LocateFixed, MapPin, ShieldCheck, Sparkles, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { submitComplaint as submitToApi } from '@/lib/api'
import { CATEGORY_META, CITIZEN_STORAGE_KEY, DEPARTMENT_LABEL, LANGUAGE_META, triageCitizenComplaint, type CitizenTriage } from '@/lib/triage'
import type { Category, Department, Language, RawComplaint } from '@/lib/types'

const SAMPLES = [
  { label: 'Water leak', text: 'School ke paas pipe phoot gaya hai, road par pani bhar raha hai.' },
  { label: 'Pothole', text: 'बस स्टॉप के सामने बड़ा गड्ढा है, बाइक वाले गिर रहे हैं।' },
  { label: 'Garbage', text: 'मार्केटच्या कोपऱ्यात चार दिवसांपासून कचरा उचललेला नाही.' },
  { label: 'Streetlight', text: 'Streetlight near the park entrance has been broken for a week.' },
]

const PROBLEM_TYPES: Array<{ value: 'auto' | Category; label: string }> = [
  { value: 'auto', label: 'Auto-detect from description' },
  { value: 'road_damage', label: 'Road or pothole' },
  { value: 'water_leak', label: 'Water leak' },
  { value: 'garbage', label: 'Garbage collection' },
  { value: 'drainage', label: 'Drainage or sewage' },
  { value: 'streetlight', label: 'Streetlight or electrical' },
  { value: 'other', label: 'Other civic issue' },
]

const DEPARTMENT_BY_CATEGORY: Record<Category, Department> = {
  road_damage: 'roads',
  water_leak: 'water_supply',
  garbage: 'sanitation',
  drainage: 'drainage',
  streetlight: 'electrical',
  other: 'other',
}

function createId() {
  return `USR-${Date.now().toString(36).toUpperCase().slice(-6)}`
}

function detectLanguage(text: string): Language {
  if (/[^\u0900-\u097F]*[\u0900-\u097F]/.test(text)) {
    return /(आहे|मध्ये|च्या|रस्त्यावर|पाण्याची|उचललेला|नाही)/.test(text) ? 'mr' : 'hi'
  }
  return /(hai|hain|ka|ki|ke|ko|se|par|pani|gaddha|kachra|nala|kripya|bahut)/i.test(text) ? 'hinglish' : 'en'
}

function applyProblemType(triage: CitizenTriage, problemType: 'auto' | Category): CitizenTriage {
  if (problemType === 'auto') return triage
  return {
    ...triage,
    category: problemType,
    department: DEPARTMENT_BY_CATEGORY[problemType],
    confidence: Math.max(triage.confidence, 0.9),
    needsReview: problemType === 'other',
    severityReason: `${CATEGORY_META[problemType].label} was selected for this report. ${triage.severityReason}`,
  }
}

function urgencyStyle(urgency: string) {
  if (urgency === 'critical') return 'border-danger/25 bg-danger/10 text-danger'
  if (urgency === 'high') return 'border-warning/30 bg-warning/10 text-warning'
  return 'border-border bg-muted text-foreground'
}

export function CitizenPortal() {
  const [text, setText] = useState('')
  const [problemType, setProblemType] = useState<'auto' | Category>('auto')
  const [landmark, setLandmark] = useState('')
  const [locationStatus, setLocationStatus] = useState<string | null>(null)
  const [photoName, setPhotoName] = useState<string | null>(null)
  const [result, setResult] = useState<RawComplaint | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const characterCount = text.trim().length
  const canSubmit = characterCount >= 10
  const detectedLanguage = useMemo(() => detectLanguage(text), [text])
  const triagePreview = useMemo(
    () => (canSubmit ? applyProblemType(triageCitizenComplaint(text), problemType) : null),
    [canSubmit, problemType, text],
  )

  function chooseSample(sample: (typeof SAMPLES)[number]) {
    setText(sample.text)
    setResult(null)
  }

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setLocationStatus('Current location is not available in this browser. Add a nearby landmark instead.')
      return
    }
    setLocationStatus('Getting your current location…')
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setLandmark(`Current location: ${coords.latitude.toFixed(5)}, ${coords.longitude.toFixed(5)}`)
        setLocationStatus('Current location added.')
      },
      () => setLocationStatus('Location permission was not granted. Add a nearby landmark instead.'),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    )
  }

  async function submitComplaint() {
    if (busy) return
    if (!canSubmit) {
      setNotice('Please describe the issue in at least a few words.')
      return
    }
    setBusy(true)
    setNotice('Analysing your report...')
    try {
      const fromApi = await submitToApi(text.trim())
      setResult({ ...fromApi, location_hint: landmark.trim() || fromApi.location_hint })
      setNotice(null)
      return
    } catch {
      // API unreachable: fall back to the local rules below
    } finally {
      setBusy(false)
    }
    const triage = applyProblemType(triageCitizenComplaint(text), problemType)
    const complaint: RawComplaint = {
      id: createId(),
      text: text.trim(),
      language: detectLanguage(text),
      category: triage.category,
      department: triage.department,
      severity: triage.severity,
      severity_reason: triage.severityReason,
      needs_human_review: triage.needsReview,
      confidence: triage.confidence,
      cluster_id: -1,
      location_hint: landmark.trim() || 'Ward 12, Pune',
    }
    let existing: RawComplaint[] = []
    try {
      const savedReports = JSON.parse(window.localStorage.getItem(CITIZEN_STORAGE_KEY) ?? '[]')
      if (Array.isArray(savedReports)) existing = savedReports as RawComplaint[]
    } catch {
      existing = []
    }
    window.localStorage.setItem(CITIZEN_STORAGE_KEY, JSON.stringify([complaint, ...existing]))
    setResult(complaint)
    setNotice(null)
  }

  function startAnother() {
    setText('')
    setLandmark('')
    setLocationStatus(null)
    setPhotoName(null)
    setResult(null)
    setNotice(null)
  }

  if (result) {
    const category = CATEGORY_META[result.category as keyof typeof CATEGORY_META]
    return (
      <main className="min-h-dvh bg-background px-4 py-6 sm:px-6 lg:py-10">
        <div className="mx-auto max-w-xl">
          <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
            <ChevronLeft className="size-4" /> Back to operations dashboard
          </Link>
          <section className="mt-8 rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
            <div className="flex size-12 items-center justify-center rounded-full bg-success/10 text-success"><CheckCircle2 className="size-6" /></div>
            <p className="mt-5 text-sm font-medium text-success">Complaint registered</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight">We have routed your report.</h1>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">Keep your complaint number if you need to follow up with Ward 12.</p>
            <div className="mt-6 rounded-xl border border-border bg-subtle p-4 font-mono text-sm font-semibold">{result.id}</div>
            <dl className="mt-5 divide-y divide-border rounded-xl border border-border px-4">
              <div className="flex items-center justify-between gap-4 py-3"><dt className="text-sm text-muted-foreground">Issue type</dt><dd className="text-sm font-medium">{category.label}</dd></div>
              <div className="flex items-center justify-between gap-4 py-3"><dt className="text-sm text-muted-foreground">Assigned department</dt><dd className="text-sm font-medium">{DEPARTMENT_LABEL[result.department as keyof typeof DEPARTMENT_LABEL]}</dd></div>
              <div className="flex items-center justify-between gap-4 py-3"><dt className="text-sm text-muted-foreground">Urgency</dt><dd className={`rounded-full border px-2.5 py-1 text-xs font-semibold uppercase ${urgencyStyle(result.severity >= 5 ? 'critical' : result.severity >= 4 ? 'high' : 'medium')}`}>{result.severity >= 5 ? 'Critical' : result.severity >= 4 ? 'High' : 'Medium'}</dd></div>
              <div className="py-3"><dt className="text-sm text-muted-foreground">Why</dt><dd className="mt-1 text-sm leading-6">{result.severity_reason}</dd></div>
            </dl>
            {result.needs_human_review && <p className="mt-4 rounded-lg border border-warning/30 bg-warning/10 px-3 py-2 text-sm text-warning">An officer will review this report before dispatch.</p>}
            <div className="mt-6 grid gap-3 sm:grid-cols-2"><Button onClick={startAnother} variant="outline" size="lg">Submit another report</Button><Link href="/"><Button size="lg" className="w-full">Open operations dashboard</Button></Link></div>
          </section>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-dvh bg-background px-4 py-6 sm:px-6 lg:py-10">
      <div className="mx-auto max-w-5xl">
        <header className="flex items-center justify-between gap-4">
          <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"><ChevronLeft className="size-4" /> Operations dashboard</Link>
          <span className="hidden items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground sm:inline-flex"><ShieldCheck className="size-3.5 text-success" /> Ward 12 demo</span>
        </header>
        <div className="mt-10 grid gap-8 lg:grid-cols-[1.25fr_0.75fr] lg:items-start">
          <section>
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground"><Sparkles className="size-3.5" /> CivicSort citizen portal</span>
            <h1 className="mt-5 max-w-xl text-4xl font-semibold tracking-[-0.035em] sm:text-5xl">Report a civic issue.</h1>
            <p className="mt-4 max-w-xl text-base leading-7 text-muted-foreground">Tell Pune Municipal Corporation what happened. Write naturally in English, Hindi, Marathi, or Hinglish.</p>
            <div className="mt-7 flex flex-wrap gap-2">
              {SAMPLES.map((sample) => <button key={sample.label} type="button" onClick={() => chooseSample(sample)} className="rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground">Try: {sample.label}</button>)}
            </div>
            <div className="mt-8 rounded-2xl border border-border bg-card p-5 shadow-sm sm:p-6">
              <label htmlFor="complaint" className="text-sm font-semibold">What is the issue?</label>
              <textarea id="complaint" value={text} onChange={(event) => setText(event.target.value)} maxLength={1200} placeholder="Example: School ke paas pipe phoot gaya hai aur road par pani aa raha hai." className="mt-2 min-h-36 w-full resize-y rounded-xl border border-input bg-background px-3 py-3 text-sm leading-6 outline-none transition-colors placeholder:text-muted-foreground focus:border-foreground/40 focus:ring-2 focus:ring-ring/30" />
              <div className="mt-2 flex justify-between gap-3 text-xs text-muted-foreground"><span>{text ? `Language detected: ${LANGUAGE_META[detectedLanguage].label}` : 'Language is detected automatically.'} Do not include phone, ID, or bank details.</span><span className="shrink-0">{text.length}/1200</span></div>
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-semibold">Type of problem<select value={problemType} onChange={(event) => setProblemType(event.target.value as 'auto' | Category)} className="mt-2 h-10 w-full rounded-lg border border-input bg-background px-3 text-sm font-normal outline-none focus:ring-2 focus:ring-ring/30">{PROBLEM_TYPES.map((problem) => <option key={problem.value} value={problem.value}>{problem.label}</option>)}</select></label>
                <div className="block text-sm font-semibold"><div className="flex items-center justify-between gap-2"><span>Location <span className="font-normal text-muted-foreground">optional</span></span><button type="button" onClick={useCurrentLocation} className="inline-flex items-center gap-1 text-xs font-medium text-success hover:underline"><LocateFixed className="size-3.5" /> Use current</button></div><div className="relative mt-2"><MapPin className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground" /><input value={landmark} onChange={(event) => { setLandmark(event.target.value); setLocationStatus(null) }} placeholder="e.g. Tilak Road school gate" className="h-10 w-full rounded-lg border border-input bg-background pl-9 pr-3 text-sm font-normal outline-none focus:ring-2 focus:ring-ring/30" /></div>{locationStatus && <p className="mt-1.5 text-xs font-normal text-muted-foreground">{locationStatus}</p>}</div>
              </div>
              <label className="mt-5 flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-dashed border-border bg-subtle px-4 py-3 transition-colors hover:border-foreground/30"><input type="file" accept="image/jpeg,image/png" className="sr-only" onChange={(event) => setPhotoName(event.target.files?.[0]?.name ?? null)} /><span className="flex items-center gap-3"><span className="flex size-9 items-center justify-center rounded-lg border border-border bg-card"><Upload className="size-4" /></span><span><span className="block text-sm font-medium">Attach a photo</span><span className="block text-xs text-muted-foreground">Optional · JPG or PNG</span></span></span>{photoName ? <span className="flex items-center gap-1 text-xs text-success"><FileImage className="size-3.5" /> {photoName}</span> : <span className="text-xs text-muted-foreground">Choose file</span>}</label>
              {notice && <p className="mt-4 rounded-lg border border-danger/25 bg-danger/10 px-3 py-2 text-sm text-danger">{notice}</p>}
              {triagePreview && <div className="mt-5 flex items-start gap-3 rounded-xl border border-border bg-subtle p-3"><ClipboardCheck className="mt-0.5 size-4 shrink-0 text-success" /><p className="text-sm leading-6 text-muted-foreground">This report appears to be a <span className="font-medium text-foreground">{CATEGORY_META[triagePreview.category].label}</span> issue and will be routed to <span className="font-medium text-foreground">{DEPARTMENT_LABEL[triagePreview.department]}</span>.</p></div>}
              <Button onClick={submitComplaint} disabled={!canSubmit} size="lg" className="mt-5 w-full"><LocateFixed className="size-4" /> Submit and route complaint</Button>
            </div>
          </section>
          <aside className="rounded-2xl border border-border bg-card p-5 shadow-sm lg:mt-20">
            <h2 className="text-sm font-semibold">What happens next</h2>
            <ol className="mt-5 space-y-5">{[
              ['1', 'We understand the report', 'CivicSort automatically detects the language and issue.'],
              ['2', 'The right team receives it', 'Roads, water, sanitation, drainage, or electrical teams receive the route.'],
              ['3', 'Urgent issues rise first', 'Safety risks receive a higher priority in the operations queue.'],
              ['4', 'Similar reports are grouped', 'Officers can see the number of people affected by one incident.'],
            ].map(([number, title, detail]) => <li key={number} className="flex gap-3"><span className="flex size-6 shrink-0 items-center justify-center rounded-full border border-border bg-subtle font-mono text-xs text-muted-foreground">{number}</span><span><strong className="block text-sm">{title}</strong><span className="mt-1 block text-xs leading-5 text-muted-foreground">{detail}</span></span></li>)}</ol>
            <div className="mt-6 border-t border-border pt-4 text-xs leading-5 text-muted-foreground">For an immediate life-threatening emergency, contact local emergency services. This demo stores reports on this browser and shows them in the operations dashboard.</div>
          </aside>
        </div>
      </div>
    </main>
  )
}
