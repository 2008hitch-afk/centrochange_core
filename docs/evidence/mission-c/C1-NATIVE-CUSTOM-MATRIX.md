# C1 — Matrice nativo/custom Unified Desk

Stato: analisi tecnica, non decisione di adozione. Issue #109 / piano #110.

Baseline applicativa main `2fab181cd61cfc69e341d9fa1849038c6646e87e`; prototipo dipendente dalla PR DRAFT #107 (`d50299f8d9ad32640259ff1c3a1fded47db5c447`, codice collaudato `8639b7982255446eacf0147ae952346442849f1b`). TARGET sperimentale Frappe/ERPNext16.50.0, Healthcare16.6.1, Builder1.35.1. RC22 non aggiornato.

## Matrice di parità

| Area | Sorgente canonica | Classificazione | Fit e rischio | Acceptance discriminante | Sforzo |
|---|---|---|---|---|---|
| Agenda settimanale | operations.workspace.agenda/schedules; scheduling.booking | CC_CUSTOM_DESK_PAGE | Il calendario Marley get_events è esplicitamente bloccato: non rispetta snapshot e contesto CC. Page nativa, griglia 1+7 condivisa; servizi esistenti. | Settimana, righe professionisti, dettagli, resize, A/B/C | Medio |
| Prenota / sposta / cancella | scheduling.booking; operations.sessions | CC_CUSTOM_DESK_PAGE | Dialog supportati; mutazioni solo servizi CC con motivo e chiave idempotente. Nessun save diretto Patient Appointment. | Booking, collisione, snapshot, cambio data, annullo, audit | Medio |
| Seduta / storico / note | operations.workspace.patient_history; operations.notes; sessions | CC_CUSTOM_DESK_PAGE | Dati canonici; note private solo relativo professionista. Non usare form clinici aggregati. | Dettaglio autorizzato, note private negative, lifecycle | Medio |
| Pazienti | Patient; security.permissions; operations.workspace | NATIVE_WITH_SUPPORTED_CUSTOMIZATION | List/Form solo nei confini già concessi. Ricerca assegnata e storia tramite servizi CC quando metadata nativo non concede accesso. Nessun nuovo grant. | List/direct/query/export/print e A/B/C | Medio |
| Professionisti | Healthcare Practitioner; security.lifecycle | NATIVE_WITH_SUPPORTED_CUSTOMIZATION | Identità native e form dove già permesso; associazioni esclusivamente lifecycle CC. | Centro, self-view, professionista senza assegnazioni | Basso |
| Disponibilità | Practitioner Schedule / Availability; scheduling.availability | CC_CUSTOM_DESK_PAGE | Master nativi, scritture native protette; gestione solo servizi canonici. | Disponibilità/assenza, centro e autore | Medio |
| Servizi, prezzi, pacchetti | Item/Item Price/Appointment Type; operations.packages | NATIVE_WITH_SUPPORTED_CUSTOMIZATION | Catalogo nativo per Manager; ledger pacchetti CC, nessuna ripartizione inventata. | Snapshot immutabile, consumo/ripristino pacchetto | Medio |
| Contabilità / registri | GL Entry/Payment Ledger Entry; finance.permissions | NATIVE_WITH_SUPPORTED_CUSTOMIZATION | Read List/Form solo dove guard corrente consente. Nessun nuovo ruolo Accounts User. | Query/direct/export/print cross-center negative | Medio |
| Fatture pazienti / fornitori | Sales Invoice/Purchase Invoice; receivables/payables | CC_CUSTOM_DESK_PAGE | Documenti ERPNext; azioni validate da servizi CC. Form nativi non sostituiscono workflow autorizzato. | Emetti, paga, annulla, rettifica, source links | Medio |
| Incassi / pagamenti | Payment Entry; native_adapter; incoming | CC_CUSTOM_DESK_PAGE | Un solo ledger nativo; autorizzazione attore effettivo PR107, nessuna impersonazione. | Payment Entry, residuo, audit, actor negative | Medio |
| Banca / riconciliazione | Bank Transaction; finance.banking | CC_CUSTOM_DESK_PAGE | Servizi canonici guidano candidati e allocazioni; no tool di riconciliazione globale non scoped. | Candidato, riconcilia, annulla, idempotenza | Medio |
| Report Centro / Professionisti / Pazienti | finance.reporting; patient_reporting; professional_view | CC_CUSTOM_DESK_PAGE | Stesse proiezioni e drill-down; date operative distinte da posting date; payer condiviso non duplicato. | Totale = record, periodi, payer, negative export | Medio |
| Report contabili ERPNext generici per ruoli limitati | finance.request_guard | BLOCKED_NEEDS_DECISION | Guard approvato nega query_report e helper erpnext.accounts ai non Manager. Non sbloccarli per il prototipo. | 403 server-side conservato | Non implementare |
| SdI simulato | finance.sdi/fiscal; CC Fiscal Transaction | CC_CUSTOM_DESK_PAGE | Solo simulatori già esistenti, payload privato e catena tentativi. | Preparazione, simulazione, correzione, no provider | Medio |
| TS simulato | finance.ts; CC TS Input Review | CC_CUSTOM_DESK_PAGE | Input review append-only; nessun invio reale, nessun automatismo fiscale aggiunto. | Opposizione, eligibility, versione e payload autorizzati | Medio |
| Audit / registro modifiche | CC Audit Event; security.audit | NATIVE_WITH_SUPPORTED_CUSTOMIZATION | Read-only proiezione corrente; nessun diritto di modifica o note private aggregate. | Append-only, prima/dopo, motivi, visibilità | Basso |
| Amministrazione accessi / centri | security.lifecycle; admin services | CC_CUSTOM_DESK_PAGE | Form guidati ai servizi già approvati; User/Role nativi non sono sostituti equivalenti. | Membership, assignment, disable, revoca immediata | Medio |
| Coda amministrativa / compensi | finance.admin_queue/professional_economics | CC_CUSTOM_DESK_PAGE | Regole DECISION054 immutate, soglie e override soltanto Manager. | Sospeso, override, catena precedente, Finance denied | Medio |
| Notifiche / job | operations.notifications/automation | CC_CUSTOM_DESK_PAGE | Coda e dispatcher canonici, DEV senza consegna reale. | Retry/idempotenza, destinatario e stato | Basso |
| Login / logout | Frappe authentication; PR107 login compatibility | NATIVE_WITH_SUPPORTED_CUSTOMIZATION | Sessioni native, nessun provider aggiunto, identità italiana; chrome Desk sperimentale dichiarato. | Login, logout, Guest, ruoli senza grant | Basso |
| Sito pubblico / primo incontro | www/primo_incontro | KEEP_WEBAPP | Pubblico separato dal Desk e dai dati autenticati. | Guest bounded endpoint, nessuna esposizione master | Nessuno |
| Stampa / export | print formats; reporting.export_csv | NATIVE_WITH_SUPPORTED_CUSTOMIZATION | Riutilizzare formato e servizio scoped; nessun export generico come bypass. | Print e CSV autorizzati, injection/cross-center negative | Basso |
| Validazione DEV | www/validazione | KEEP_WEBAPP | Harness tecnico non è prodotto operativo; riusare per confronto sintetico. | Solo DEV autorizzato | Nessuno |
| Cutover / identità globale Desk | HC0005 DECISION004; C4 | BLOCKED_NEEDS_DECISION | Webapp rimane primaria. Nessuna scelta finale, promozione TARGET o dismissione automatica. | Owner confronto e decisione separata | Non implementare |

## Componenti ufficiali e pin

- Frappe `f20f92d29706510551b4438cc196b0323a7f1a92`: [Page API](https://docs.frappe.io/framework/user/en/api/page), [List API](https://docs.frappe.io/framework/user/en/api/list).
- [Page loader/role gate pinned](https://github.com/frappe/frappe/blob/f20f92d29706510551b4438cc196b0323a7f1a92/frappe/core/doctype/page/page.py): JSON standard Page, `is_permitted`, JS/CSS caricati dal modulo. Il gate Page non sostituisce i guard dei servizi.
- [Page component pinned](https://github.com/frappe/frappe/blob/f20f92d29706510551b4438cc196b0323a7f1a92/frappe/public/js/frappe/ui/page.js): `make_app_page`, toolbar/fields, lifecycle.
- [Dialog pinned](https://github.com/frappe/frappe/blob/f20f92d29706510551b4438cc196b0323a7f1a92/frappe/public/js/frappe/ui/dialog.js): Dialog nativo per azioni CC.
- [Workspace pinned](https://github.com/frappe/frappe/blob/f20f92d29706510551b4438cc196b0323a7f1a92/frappe/public/js/frappe/views/workspace/workspace.js): navigazione supportata, non un permission boundary.
- ERPNext `7474d9e786277383de1242ab882f16856d17a9c9`, Healthcare `dda107b26e3a0fe1dbd65c7257371235de054a04`, Builder `37e958bc4f801d06d0438c21b97b42c45c4eaa51`: riuso pin R5, nessun upgrade aggiuntivo.

## Navigazione per ruoli e limiti

Direzione: operazioni, Finance e amministrazione già autorizzate. Segreteria: operazioni e report già permessi; nessuna nota privata. Finance/Accountant: Finance nei centri correnti, read/write secondo guard esistente. Professionisti A/B: solo contesti propri; C senza assegnazione: nessun paziente o seduta. Guest: nessun Desk, solo pubblico. `desk_access=1` dei ruoli CC è già esistente, non viene modificato.

Le superfici native sono candidate, non PASS preventivi: accesso Form/List, metadata e API devono essere verificati sul clone. Le funzionalità non implementate nel primo percorso C2 restano esplicitamente non verificate. Non si duplicano anagrafiche, ledger, policy, endpoint autorizzativi o ruoli.

## Verifica versione Desk durante C2

Frappe16.50 usa anche [Sidebar standard pinned](https://github.com/frappe/frappe/blob/f20f92d29706510551b4438cc196b0323a7f1a92/frappe/desk/doctype/sidebar/sidebar.py), con JSON esportato sotto modulo/sidebar/nome/nome.json. La Sidebar calcolata automaticamente elencava nomi tecnici: il prototipo usa Sidebar di modulo esplicita con link alla Page. Nessun nuovo grant; i servizi rimangono i permission boundary. Confermato sul runtime C109, non inferito dalle sole API storiche Workspace.
