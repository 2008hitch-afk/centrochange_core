import type { Center, Practitioner } from './api'
import { demoText, syntheticCode, syntheticLetter } from './demo_labels'

// Prefer an exact, scoped alias, then the descriptive Frappe field. IDs remain
// values for navigation/API calls; missing fixture names are stated plainly.
export function centerName(center: Center): string {
  const alias = demoText(center.name)
  if (alias !== center.name) return alias
  const branch = String(center.branch ?? '').trim()
  const display = demoText(branch)
  if (display && !syntheticCode(display)) return display
  const letter = syntheticLetter(branch)
  return letter ? `Centro di prova ${letter}` : 'Sede senza nome'
}

export function centerNameFor(identifier: string, centers: Center[]): string {
  const center = centers.find(row => row.name === identifier)
  return center ? centerName(center) : 'Sede non disponibile'
}

export function practitionerName(practitioner: Practitioner): string {
  const alias = demoText(practitioner.name)
  if (alias !== practitioner.name) return alias
  const display = demoText(String(practitioner.practitioner_name ?? '').trim())
  if (display && !syntheticCode(display)) return display
  const letter = syntheticLetter(practitioner.practitioner_name)
  return letter ? `Professionista di prova ${letter}` : 'Professionista senza nome'
}

export function practitionerNameFor(identifier: string, practitioners: Practitioner[], snapshot?: string): string {
  const practitioner = practitioners.find(row => row.name === identifier)
  if (practitioner) return practitionerName(practitioner)
  const alias = demoText(identifier)
  if (alias !== identifier) return alias
  const display = demoText(String(snapshot ?? '').trim())
  if (display && !syntheticCode(display)) return display
  const letter = syntheticLetter(snapshot)
  return letter ? `Professionista di prova ${letter}` : 'Professionista non disponibile'
}

// Same presentation wording as the existing Frappe session printout.
const closureNames: Record<string, string> = {
  Pending: 'Da chiudere', Closed: 'Chiusa', 'Auto Locked': 'Bloccata', Reopened: 'Riaperta'
}
const economyNames: Record<string, string> = {
  Pending: 'Da definire', Due: 'Dovuta', 'Non Due': 'Non dovuta',
  'Package Covered': 'Coperta da pacchetto', Waived: 'Rinuncia economica'
}
export const closureName = (value: unknown) => closureNames[String(value ?? '')] ?? String(value ?? '—')
export const economyName = (value: unknown) => economyNames[String(value ?? '')] ?? String(value ?? '—')

const syntheticAuditRoles: Record<string, string> = {
  m: 'Manager di prova', s: 'Segreteria di prova', a: 'Professionista di prova A',
  b: 'Professionista di prova B', c: 'Professionista di prova C',
  f: 'Finanza di prova', t: 'Contabilità di prova'
}

export const auditActorName = (value: unknown) => {
  const raw = String(value ?? '').trim()
  const match = /^cc-http-[a-z0-9]{10}-([msabcft])@example\.invalid$/i.exec(raw)
  return match ? syntheticAuditRoles[match[1].toLowerCase()] : raw || 'Autore non disponibile'
}
