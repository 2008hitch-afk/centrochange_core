import type { Boot, FinanceBoot } from './api'

// Exact IDs and display strings come from the private, versioned UAT manifest.
// This map is presentation-only: all API calls retain canonical identifiers.
let labels: Record<string, string> = {}

export function configureDemoLabels(boot: Boot | null, financeBoot: FinanceBoot | null) {
  labels = { ...(boot?.demo_labels ?? {}), ...(financeBoot?.demo_labels ?? {}) }
}

export function demoText(value: unknown): string {
  const original = String(value ?? '')
  return labels[original] ?? original
}

export function demoPreferred(identifier: unknown, fallback: unknown): string {
  const id = String(identifier ?? '')
  return labels[id] ?? demoText(fallback)
}

export function demoMatches(value: unknown, query: string): boolean {
  const term = query.trim().toLocaleLowerCase('it-IT')
  return !term || `${String(value ?? '')} ${demoText(value)}`.toLocaleLowerCase('it-IT').includes(term)
}
