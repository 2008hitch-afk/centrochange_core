import { call, finance, ops, recentPaymentStart, requestKey, romeToday, type Row } from './api'

export type ArchiveKind = 'Patient' | 'Healthcare Practitioner' | 'Item' | 'Item Price' | 'Appointment Type' | 'CC Center Service' | 'CC Package Template' | 'Sales Invoice' | 'Purchase Invoice' | 'Payment Entry' | 'Bank Transaction'
export type ArchiveRecord = Row & { name: string; modified?: string }
export type PatientProfile = ArchiveRecord & { patient_name: string; first_name: string; last_name?: string; email?: string; modified: string }
export type PractitionerProfile = ArchiveRecord & { practitioner_name: string; first_name: string; last_name?: string; user_id: string; status: string; modified: string }
export type CatalogItem = ArchiveRecord & { item_name: string; item_group: string; stock_uom: string; is_stock_item: number; is_sales_item: number; disabled: number; modified: string }
export type AppointmentProfile = ArchiveRecord & { appointment_type: string; default_duration: number; cc_service_item: string; cc_first_meeting: number; modified: string }
export type CenterService = ArchiveRecord & { center: string; appointment_type: string; enabled: number; modified: string }
export type Tariff = ArchiveRecord & { item_code: string; price_list: string; currency: string; price_list_rate: number; valid_from?: string; valid_upto?: string; modified: string }
export type PackageTemplate = ArchiveRecord & { title: string; service_item: string; units: number; enabled: number; modified: string }
export type PaymentProjection = ArchiveRecord & { posting_date: string; payment_type: 'Receive' | 'Pay' | 'Internal Transfer'; party_type: string; party: string; paid_amount: number; received_amount: number; unallocated_amount: number; docstatus: number; references?: { doctype: 'Sales Invoice' | 'Purchase Invoice'; name: string; allocated_amount: number }[] }
export type ArchivePage<T extends ArchiveRecord = ArchiveRecord> = { rows: T[]; has_more: boolean }
export type PrintPreview = { doctype: string; name: string; format: string; html: string }

const catalogKinds: ArchiveKind[] = ['Item', 'Item Price', 'Appointment Type', 'CC Center Service', 'CC Package Template']
export const editableKinds: ArchiveKind[] = ['Patient', 'Healthcare Practitioner', ...catalogKinds]
export const financeKinds: ArchiveKind[] = ['Sales Invoice', 'Purchase Invoice', 'Payment Entry', 'Bank Transaction']
export const creatableKinds: ArchiveKind[] = ['Item Price', 'Appointment Type', 'CC Center Service', 'CC Package Template']

export async function listArchive(center: string, kind: ArchiveKind, offset = 0, interval?: { start: string; end: string }, search = ''): Promise<ArchivePage> {
  const query = search.trim()
  if (catalogKinds.includes(kind)) return call<ArchivePage>('catalog.records', { center, kind, limit: 100, offset, search: query })
  if (kind === 'Patient') return ops<ArchivePage<PatientProfile>>('profiles.patients', { center, limit: 100, offset, search: query })
  if (kind === 'Healthcare Practitioner') return ops<ArchivePage<PractitionerProfile>>('profiles.practitioners', { center, limit: 100, offset, search: query })
  if (kind === 'Payment Entry') return finance<ArchivePage<PaymentProjection>>('payments.records', { center, start: interval?.start ?? recentPaymentStart(), end: interval?.end ?? romeToday(), limit: 100, offset, search: query })
  const rows = await finance<ArchiveRecord[]>('reporting.records', { center, doctype: kind, search: query })
  return { rows, has_more: false }
}

export async function archiveDetail(center: string, kind: ArchiveKind, name: string): Promise<ArchiveRecord> {
  if (catalogKinds.includes(kind)) return call<ArchiveRecord>('catalog.detail', { center, kind, name })
  if (kind === 'Patient') return ops<PatientProfile>('profiles.patient_detail', { center, name })
  if (kind === 'Healthcare Practitioner') return ops<PractitionerProfile>('profiles.practitioner_detail', { center, name })
  if (kind === 'Payment Entry') return finance<PaymentProjection>('payments.detail', { center, name })
  throw new Error('Dettaglio disponibile nella sezione Finanza autorizzata.')
}

export async function saveArchive(center: string, kind: ArchiveKind, record: ArchiveRecord, draft: Row, reason: string, key = requestKey()) {
  if (!record.modified) throw new Error('Versione della scheda assente. Ricarica la pagina.')
  const base = { center, name: record.name, expected_version: record.modified, request_key: key, reason }
  if (kind === 'Patient') return ops<ArchiveRecord>('profiles.patient_save', { ...base, first_name: draft.first_name, last_name: draft.last_name ?? '', email: draft.email ?? '' }, true)
  if (kind === 'Healthcare Practitioner') return ops<ArchiveRecord>('profiles.practitioner_save', { ...base, first_name: draft.first_name, last_name: draft.last_name ?? '' }, true)
  if (kind === 'Item') return call<ArchiveRecord>('catalog.item_save', { ...base, item_name: draft.item_name }, true)
  if (kind === 'Item Price') return call<ArchiveRecord>('catalog.price_save', { ...base, price_list_rate: draft.price_list_rate }, true)
  if (kind === 'Appointment Type') return call<ArchiveRecord>('catalog.appointment_type_save', { ...base, default_duration: draft.default_duration }, true)
  if (kind === 'CC Center Service') return call<ArchiveRecord>('catalog.service_save', { ...base, enabled: draft.enabled }, true)
  if (kind === 'CC Package Template') return call<ArchiveRecord>('catalog.package_template_save', { ...base, title: draft.title, units: draft.units, enabled: draft.enabled }, true)
  throw new Error('Scrittura non autorizzata per questa scheda.')
}

export async function createArchive(center: string, kind: ArchiveKind, draft: Row, reason: string, key = requestKey()): Promise<{ name: string }> {
  const base = { center, request_key: key, reason }
  if (kind === 'Item Price') return call('catalog.price_create', { ...base, item_code: draft.item_code, valid_from: draft.valid_from, price_list_rate: draft.price_list_rate }, true)
  if (kind === 'Appointment Type') return call('catalog.appointment_type_create', { ...base, appointment_type: draft.appointment_type, service_item: draft.cc_service_item, default_duration: draft.default_duration }, true)
  if (kind === 'CC Center Service') return call('catalog.service_create', { ...base, appointment_type: draft.appointment_type, enabled: draft.enabled }, true)
  if (kind === 'CC Package Template') return call('catalog.package_template_create', { ...base, title: draft.title, service_item: draft.service_item, units: draft.units, enabled: draft.enabled }, true)
  throw new Error('Creazione non autorizzata per questo archivio.')
}

export const documentPreview = (center: string, doctype: 'Sales Invoice' | 'Purchase Invoice' | 'Payment Entry', name: string) =>
  finance<PrintPreview>('documents.preview', { center, doctype, name, print_format: 'Standard' })
