export type Language = 'en' | 'hi' | 'mr' | 'hinglish'

export type Category = 'road_damage' | 'water_leak' | 'garbage' | 'drainage' | 'streetlight' | 'other'

export type Department = 'roads' | 'water_supply' | 'sanitation' | 'drainage' | 'electrical' | 'other'

export interface RawComplaint {
  id: string
  text: string
  language: string
  category: string
  severity: number
  severity_reason: string
  department: string
  needs_human_review: boolean
  confidence: number
  cluster_id: number
  location_hint: string | null
}

export type TicketStatus = 'open' | 'dispatched' | 'resolved'

export interface Ticket {
  key: string
  primary: RawComplaint
  reports: RawComplaint[]
  clusterId: number | null
  severity: number
  priority: number
  needsReview: boolean
  languages: Language[]
}

export interface Filters {
  categories: Category[]
  departments: Department[]
  languages: Language[]
  severities: number[]
}
