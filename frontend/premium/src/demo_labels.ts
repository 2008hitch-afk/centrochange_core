import type { Boot, FinanceBoot } from './api'

// Exact IDs and display strings come from the private, versioned UAT manifest.
// This map is presentation-only: all API calls retain canonical identifiers.
let labels: Record<string, string> = {}
let operationalLabels: Record<string, string> = {}
let financialLabels: Record<string, string> = {}

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
  const display = String(fallback ?? '')
  return operationalLabels[id] ?? operationalLabels[display] ?? (display || id)
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
