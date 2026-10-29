import type { Boot, FinanceBoot } from './api'

// Exact IDs and display strings come from the private, versioned UAT manifest.
// This map is presentation-only: all API calls retain canonical identifiers.
let labels: Record<string, string> = {}
let operationalLabels: Record<string, string> = {}
let financialLabels: Record<string, string> = {}
let patientNames: Record<string, string> = {}

// An unlabelled HTTP fixture is a test record, not a person's display name.
// Keep its canonical ID in API values while making missing presentation data explicit.
export function syntheticCode(value: unknown): boolean {
  return /^CC-HTTP-[A-Za-z0-9]{10}(?:\s+.*)?$/.test(String(value ?? '').trim())
}

// The final single letter or token is an explicit test-fixture discriminator, not a
// fabricated personal name. Never infer a label from non-fixture identifiers.
export function syntheticLetter(value: unknown): string | null {
  const match = /^CC-HTTP-[A-Za-z0-9]{10}\s+([A-Za-z0-9]+)(?:\s+.*)?$/.exec(String(value ?? '').trim())
  return match ? match[1].toLocaleUpperCase('it-IT') : null
}

export function configureDemoLabels(boot: Boot | null, financeBoot: FinanceBoot | null) {
  operationalLabels = boot?.demo_labels ?? {}
  financialLabels = financeBoot?.demo_labels ?? {}
  labels = { ...operationalLabels, ...financialLabels }
  patientNames = Object.fromEntries((boot?.patients ?? []).map(row =>
    [row.name, patientName(row.patient_name, row.first_name, row.last_name) || operationalLabels[row.name] || '']).filter((row): row is [string, string] => Boolean(row[1])))
}

export function demoText(value: unknown): string {
  const original = String(value ?? '')
  if (labels[original] != null) return labels[original]
  const fixture = /^CC-HTTP-[A-Za-z0-9]{10}\s+(SESSION|PACKAGE)$/i.exec(original.trim())
  if (fixture) return fixture[1].toUpperCase() === 'SESSION' ? 'Servizio di prova' : 'Pacchetto di prova'
  return original
}

// Patient and Customer may share an identifier. A demo alias is not a real
// Patient name; never display a fiscal Customer label as a clinical identity.
const technicalPatientValue = (value: string) =>
  !value || /^(?:CC-(?:HTTP|MVP-POS)-|SYNTHETIC[-_]|PAT-[A-Z0-9-]+$)/i.test(value)

function patientName(display: unknown, firstName?: unknown, lastName?: unknown): string {
  const first = String(firstName ?? '').trim()
  const last = String(lastName ?? '').trim()
  if (first && last && !technicalPatientValue(first) && !technicalPatientValue(last)) return `${first} ${last}`
  const name = String(display ?? '').trim()
  return technicalPatientValue(name) ? '' : name
}

// Opaque, stable UI discriminator: never expose a canonical Patient ID as a name.
function missingPatientName(identifier: string): string {
  let hash = 2166136261
  for (let i = 0; i < identifier.length; i++) hash = Math.imul(hash ^ identifier.charCodeAt(i), 16777619)
  return `Anagrafica da completare · scheda ${(hash >>> 0).toString(36).toUpperCase().padStart(7, '0')}`
}

export function demoPatient(identifier: unknown, fallback: unknown, firstName?: unknown, lastName?: unknown): string {
  const id = String(identifier ?? '').trim()
  const display = String(fallback ?? '').trim()
  const currentName = patientName('', firstName, lastName) || patientName(display)
  if (currentName) return currentName
  if (operationalLabels[id]) return operationalLabels[id]
  if (operationalLabels[display]) return operationalLabels[display]
  const canonicalName = patientNames[id]
  if (canonicalName) return canonicalName
  const displayName = patientName(display)
  if (displayName) return displayName
  return missingPatientName(id || display)
}

export function demoCustomer(identifier: unknown, fallback: unknown): string {
  const id = String(identifier ?? '')
  const display = String(fallback ?? '')
  return financialLabels[id] ?? financialLabels[display] ?? (display || id)
}

export function demoMatches(value: unknown, query: string): boolean {
  const term = query.trim().toLocaleLowerCase('it-IT')
  return !term || `${String(value ?? '')} ${demoText(value)}`.toLocaleLowerCase('it-IT').includes(term)
}
