import type { Category, Department, Filters, Language, RawComplaint, Ticket } from './types'

export const CATEGORY_META: Record<Category, { label: string; dot: string; bar: string }> = {
  road_damage: { label: 'Roads', dot: 'bg-cat-roads', bar: 'bg-cat-roads' },
  water_leak: { label: 'Water leak', dot: 'bg-cat-water', bar: 'bg-cat-water' },
  garbage: { label: 'Garbage', dot: 'bg-cat-garbage', bar: 'bg-cat-garbage' },
  drainage: { label: 'Drainage', dot: 'bg-cat-drainage', bar: 'bg-cat-drainage' },
  streetlight: { label: 'Electrical', dot: 'bg-cat-electrical', bar: 'bg-cat-electrical' },
  other: { label: 'Other', dot: 'bg-cat-other', bar: 'bg-cat-other' },
}

export const CATEGORY_ORDER: Category[] = [
  'road_damage',
  'water_leak',
  'garbage',
  'drainage',
  'streetlight',
  'other',
]

export const DEPARTMENT_LABEL: Record<Department, string> = {
  roads: 'Roads',
  water_supply: 'Water Supply',
  sanitation: 'Sanitation',
  drainage: 'Drainage',
  electrical: 'Electrical',
  other: 'General Admin',
}

export const DEPARTMENT_ORDER: Department[] = [
  'roads',
  'water_supply',
  'sanitation',
  'drainage',
  'electrical',
  'other',
]

export const LANGUAGE_META: Record<Language, { label: string; short: string; htmlLang: string }> = {
  en: { label: 'English', short: 'EN', htmlLang: 'en' },
  hi: { label: 'Hindi', short: 'HI', htmlLang: 'hi' },
  mr: { label: 'Marathi', short: 'MR', htmlLang: 'mr' },
  hinglish: { label: 'Hinglish', short: 'HG', htmlLang: 'hi-Latn' },
}

export const LANGUAGE_ORDER: Language[] = ['en', 'hi', 'mr', 'hinglish']

export const SEVERITY_LEVELS = [5, 4, 3, 2, 1]

export const REVIEW_CONFIDENCE_THRESHOLD = 0.7

export function asCategory(value: string): Category {
  return (value in CATEGORY_META ? value : 'other') as Category
}

export function asDepartment(value: string): Department {
  return (value in DEPARTMENT_LABEL ? value : 'other') as Department
}

export function asLanguage(value: string): Language {
  return (value in LANGUAGE_META ? value : 'en') as Language
}

export function matchesQuery(c: RawComplaint, query: string) {
  const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean)
  if (terms.length === 0) return true
  const haystack = [
    c.id,
    c.text,
    c.location_hint ?? '',
    c.severity_reason,
    CATEGORY_META[asCategory(c.category)].label,
    DEPARTMENT_LABEL[asDepartment(c.department)],
  ]
    .join(' ')
    .toLowerCase()
  return terms.every((term) => haystack.includes(term))
}

export function matchesFilters(c: RawComplaint, f: Filters) {
  if (f.categories.length && !f.categories.includes(asCategory(c.category))) return false
  if (f.departments.length && !f.departments.includes(asDepartment(c.department))) return false
  if (f.languages.length && !f.languages.includes(asLanguage(c.language))) return false
  if (f.severities.length && !f.severities.includes(c.severity)) return false
  return true
}

export function activeFilterCount(f: Filters) {
  return f.categories.length + f.departments.length + f.languages.length + f.severities.length
}

function priorityScore(severity: number, reportCount: number, confidence: number) {
  const raw = severity * 16 + (reportCount - 1) * 6 + Math.round(confidence * 10)
  return Math.min(99, raw)
}

export function buildTickets(reports: RawComplaint[]): Ticket[] {
  const groups = new Map<string, RawComplaint[]>()
  for (const r of reports) {
    const key = r.cluster_id >= 0 ? `GRP-${String(r.cluster_id).padStart(2, '0')}` : r.id
    const list = groups.get(key)
    if (list) list.push(r)
    else groups.set(key, [r])
  }

  const tickets: Ticket[] = []
  for (const [key, list] of groups) {
    const sorted = [...list].sort(
      (a, b) =>
        b.severity - a.severity ||
        Number(b.language === 'en') - Number(a.language === 'en') ||
        a.id.localeCompare(b.id),
    )
    const primary = sorted[0]
    const severity = primary.severity
    const avgConfidence = list.reduce((s, r) => s + r.confidence, 0) / list.length
    const languages = LANGUAGE_ORDER.filter((l) => list.some((r) => asLanguage(r.language) === l))
    tickets.push({
      key,
      primary,
      reports: sorted,
      clusterId: primary.cluster_id >= 0 ? primary.cluster_id : null,
      severity,
      priority: priorityScore(severity, list.length, avgConfidence),
      needsReview: list.some(
        (r) => r.needs_human_review || r.confidence < REVIEW_CONFIDENCE_THRESHOLD,
      ),
      languages,
    })
  }

  return tickets.sort((a, b) => b.priority - a.priority || a.key.localeCompare(b.key))
}

export function ticketTitle(t: Ticket) {
  const withHint = t.reports.find((r) => r.language === 'en' && r.location_hint) ?? t.reports.find((r) => r.location_hint)
  if (withHint?.location_hint) {
    const hint = withHint.location_hint
    return hint.charAt(0).toUpperCase() + hint.slice(1)
  }
  return CATEGORY_META[asCategory(t.primary.category)].label
}
