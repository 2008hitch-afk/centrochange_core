import { displayDate, money } from './api'

const labels: Record<string, string> = {
  appointment: 'Seduta', appointment_label: 'Seduta', amount: 'Importo', amount_known: 'Importo definito',
  assignee: 'Responsabile', attempt_count: 'Tentativi', cc_incoming_source: 'XML ricevuto',
  center: 'Centro', condition_details: 'Dettaglio condizione', corrects: 'Corregge',
  currency: 'Valuta', customer: 'Cliente', date: 'Data', defer_until: 'Rinvio fino al',
  deposit: 'Entrata', detected_at: 'Rilevata il', direction: 'Direzione',
  docstatus: 'Stato documento', due_at: 'Scadenza', error_class: 'Esito',
  exception_type: 'Condizione', expected_amount: 'Compenso atteso', external_protocol: 'Protocollo esterno',
  grand_total: 'Totale', invoice_date: 'Data fattura', invoice_number: 'Numero fattura',
  known_expected: 'Compenso noto', outstanding: 'Residuo', outstanding_amount: 'Residuo',
  paid_amount: 'Importo pagato', party: 'Soggetto', payment_type: 'Tipo pagamento',
  posting_date: 'Data registrazione', practitioner: 'Professionista', priority: 'Priorità',
  problem: 'Da verificare', purchase_invoice: 'Fattura fornitore', reference_doctype: 'Tipo fonte',
  reference_label: 'Fonte', reference_name: 'Riferimento', reference_number: 'Riferimento',
  replay: 'Richiesta ripetuta', resolved_at: 'Risolta il', retryable: 'Ripetibile',
  rule: 'Regola', state: 'Stato', status: 'Stato', supplier: 'Fornitore',
  total: 'Totale', unallocated_amount: 'Non allocato', unresolved_count: 'Da verificare',
  withdrawal: 'Uscita'
}

const values: Record<string, string> = {
  Receive: 'Incasso', Pay: 'Pagamento', 'Internal Transfer': 'Giroconto',
  Draft: 'Bozza', Submitted: 'Confermato', Cancelled: 'Annullato',
  Paid: 'Pagata', Unpaid: 'Da pagare', 'Partly Paid': 'Pagata in parte',
  Overdue: 'Scaduta', Open: 'Aperta', Closed: 'Chiusa',
  Pending: 'In attesa', Resolved: 'Risolta', Error: 'Errore',
  Incoming: 'In entrata', Outgoing: 'In uscita'
}

export const financeFieldLabel = (key: string) => labels[key] ?? key.replaceAll('_', ' ')

export function financeFieldValue(key: string, value: unknown): string {
  if (value == null || value === '') return '—'
  if (key === 'docstatus') return ({ 0: 'Bozza', 1: 'Confermato', 2: 'Annullato' } as Record<number, string>)[Number(value)] ?? String(value)
  if (['replay', 'retryable', 'amount_known'].includes(key)) return Number(value) ? 'Sì' : 'No'
  if (['posting_date', 'invoice_date', 'date'].includes(key)) return displayDate(value)
  if (['detected_at', 'due_at', 'defer_until', 'resolved_at'].includes(key)) {
    const raw = String(value)
    return displayDate(raw) + (raw.length >= 16 ? ` ${raw.slice(11, 16)}` : '')
  }
  if (['amount', 'expected_amount', 'known_expected', 'grand_total', 'total',
    'outstanding', 'outstanding_amount', 'paid_amount', 'unallocated_amount',
    'deposit', 'withdrawal'].includes(key)) return money(value)
  return values[String(value)] ?? String(value)
}
