export type Row = Record<string, unknown>
export type Center = { name: string; branch: string }
export type Practitioner = { name: string; practitioner_name: string; first_name?: string; last_name?: string; status?: string }
export type Patient = { name: string; patient_name: string; first_name?: string; last_name?: string }
export type Service = { name: string; cc_service_label?: string; cc_service_item?: string; cc_price_snapshot?: number; cc_currency_snapshot?: string; duration?: number }
export type Appointment = { name: string; patient: string; patient_name: string; patient_first_name?: string; patient_last_name?: string; practitioner: string; practitioner_name: string; cc_center: string; appointment_date: string; appointment_time: string; duration: number; status: string; cc_closure_state?: string; cc_economic_state?: string; cc_paid?: number; cc_performed?: number; cc_service_label?: string; cc_price_snapshot?: number; cc_currency_snapshot?: string }
export type PaymentBlocker = { center: string; reference_doctype: 'Sales Invoice' | 'Patient Appointment'; reference_name: string; amount: number; currency: string; due_date: string; original_due_date: string }
export type ReschedulePaymentBlock = { blocked: boolean; can_override: boolean; debts: PaymentBlocker[] }
export type Boot = { center: string; centers: Center[]; patients: Patient[]; practitioners: Practitioner[]; services: Service[]; packages: Row[]; payment_methods: string[]; roles: string[]; demo_labels?: Record<string, string> }
export type FinanceBoot = { center: string; centers: Center[]; can_write: boolean; is_manager: boolean; customers: Row[]; suppliers: Row[]; accounts: Row[]; practitioners: Practitioner[]; items: Row[]; assignees: string[]; simulation_only: boolean; fiscal_verified: boolean; demo_labels?: Record<string, string> }

const prefix = 'centrochange_core.'
async function sessionExpired() {
  if (location.pathname !== '/premium') return false
  try {
    const response = await fetch('/api/method/frappe.auth.get_logged_user', {
      credentials: 'same-origin', headers: { Accept: 'application/json' }
    })
    if (response.status === 401 || response.status === 403) return true
    if (!response.ok) return false
    return (await response.json()).message === 'Guest'
  } catch { return false }
}
export async function call<T>(method: string, args: Row = {}, write = false): Promise<T> {
  const url = '/api/method/' + (method.startsWith('frappe.') || method === 'logout' ? method : prefix + method)
  const headers: Record<string, string> = { Accept: 'application/json' }
  const options: RequestInit = { credentials: 'same-origin', headers, method: write ? 'POST' : 'GET' }
  if (write) {
    const token = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content
    if (!token) throw new Error('Sessione scaduta. Ricarica la pagina.')
    headers['X-Frappe-CSRF-Token'] = token
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(args)
  }
  const query = new URLSearchParams(Object.entries(args).map(([key, value]) => [key, typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value ?? '')]))
  let response: Response
  try { response = await fetch(write ? url : `${url}?${query}`, options) }
  catch { throw new Error('Connessione non disponibile. Riprova.') }
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload.exc) {
    if (response.status === 401 || response.status === 403) {
      if (await sessionExpired()) {
        location.replace('/login?redirect-to=/premium')
        throw new Error('Sessione scaduta. Accedi di nuovo.')
      }
      throw new Error('Accesso negato. Verifica i permessi.')
    }
    let message = 'Operazione non riuscita. Verifica i dati e riprova.'
    try {
      const server = JSON.parse(payload._server_messages ?? '[]')
      const last = JSON.parse(server.at(-1) ?? '{}')
      if (last.message && typeof last.message === 'string') message = last.message.replace(/<[^>]*>/g, '')
    } catch { /* generic error retained */ }
    throw new Error(message)
  }
  return payload.message as T
}

export const ops = <T>(name: string, args: Row = {}, write = false) => call<T>('operations.' + name, args, write)
export const finance = <T>(name: string, args: Row = {}, write = false) => call<T>('finance.' + name, args, write)
export const schedule = <T>(name: string, args: Row = {}, write = false) => call<T>('scheduling.' + name, args, write)
export const requestKey = () => Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('')
export const romeDateAt = (at: Date) => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Rome', year: 'numeric', month: '2-digit', day: '2-digit' }).format(at)
export const romeToday = () => romeDateAt(new Date())
export const recentPaymentStart = () => {
  const [year, month, day] = romeToday().split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day) - 90 * 86_400_000).toISOString().slice(0, 10)
}
export const displayDate = (value: unknown) => { const iso = String(value ?? '').slice(0, 10); return /^\d{4}-\d\d-\d\d$/.test(iso) ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}` : String(value ?? '') }
export const money = (value: unknown, currency = 'EUR') => value == null ? 'Da definire' : new Intl.NumberFormat('it-IT', { style: 'currency', currency }).format(Number(value))
export const time = (value: unknown) => String(value ?? '').slice(0, 5)
