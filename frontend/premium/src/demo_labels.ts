import type { Boot, FinanceBoot } from './api'

// Exact IDs and display strings come from the private, versioned UAT manifest.
// This map is presentation-only: all API calls retain canonical identifiers.
let labels: Record<string, string> = {}
let operationalLabels: Record<string, string> = {}
let financialLabels: Record<string, string> = {}

// An unlabelled HTTP fixture is a test record, not a person's display name.
// Keep its canonical ID in API values while making missing presentation data explicit.
export function syntheticCode(value: unknown): boolean {
  return /^CC-HTTP-[A-Za-z0-9]{10}(?:\s+\S+)?$/.test(String(value ?? '').trim())
}

// The final single letter is an explicit test-fixture discriminator, not a
// fabricated personal name. Never infer a label from non-fixture identifiers.
export function syntheticLetter(value: unknown): string | null {
  const match = /^CC-HTTP-[A-Za-z0-9]{10}\s+([A-Za-z])$/.exec(String(value ?? '').trim())
  return match ? match[1].toLocaleUpperCase('it-IT') : null
}

export function configureDemoLabels(boot: Boot | null, financeBoot: FinanceBoot | null) {
  operationalLabels = boot?.demo_labels ?? {}
  financialLabels = financeBoot?.demo_labels ?? {}
  labels = { ...operationalLabels, ...financialLabels }
}

export function demoText(value: unknown): string {
  const original = String(value ?? '')
  return labels[original] ?? original
}

// Patient and Customer may have the same Frappe name in synthetic fixtures.
// Keep the two authorized projections separate to avoid showing a fiscal
// Customer label in a clinical/operational Patient context.
export function demoPatient(identifier: unknown, fallback: unknown): string {
  const id = String(identifier ?? '')
  const display = String(fallback ?? '').trim()
  const letter = syntheticLetter(display || id)
  return operationalLabels[id] ?? operationalLabels[display] ??
    financialLabels[`Patient::${id}`] ?? financialLabels[`PatientDisplay::${display}`] ??
    (syntheticCode(display || id)
      ? (letter ? `Paziente di prova ${letter}` : 'Paziente senza nome')
      : (display || id))
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
