# API / role contract matrix — #148

Status is source-level inspection plus mocked browser exercises; server authorization on this React candidate is **NOT_VERIFIED**. `PRESENTE` means the named React control exists, not that its live workflow passed. Roles below are intended scopes inherited from the existing backend; the server is authority.

| React route / task | Roles | API / method | Canonical record | Access | State / test |
|---|---|---|---|---|---|
| `/premium` session and shell | CC Manager, Secretariat, Professional, Finance, Accountant; other assigned roles to verify | Frappe session, `operations.workspace.bootstrap`, `finance.reporting.bootstrap` | User, Branch, Membership | read, page gate | PRESENTE; mocked `premium.spec.ts`; live NOT_VERIFIED |
| Agenda calendar, center and practitioner | Manager, Secretariat, Professional | `operations.workspace.agenda` | Patient Appointment | scoped read | PRESENTE; mocked desktop/mobile |
| Book session | Manager, Secretariat, Professional when permitted | `scheduling.booking.book` | Patient Appointment | audited POST | PRESENTE; mocked CSRF/request key; live NOT_VERIFIED |
| Move / cancel / close / reopen / waive | permitted operational roles | `scheduling.booking.reschedule`, `operations.lifecycle.*` | Patient Appointment, CC Settlement | audited POST | PRESENTE; live negatives NOT_VERIFIED |
| Patient search and history | assigned operational roles | `operations.workspace.patient_search`, `operations.workspace.patient_history` | Patient, Appointment, Notes, Package | scoped read | PRESENTE; mocked |
| Organizational/private notes | permitted operational / Professional | `operations.notes.add_note` | CC Organizational Note, CC Private Note | audited POST | PRESENTE; private visibility depends on server; live NOT_VERIFIED |
| Availability and absence | permitted operational roles | `operations.workspace.schedules`, `scheduling.availability.set_schedule/create_absence` | Practitioner Schedule, Practitioner Availability | read/POST | PRESENTE; mutation NOT_VERIFIED |
| Operational report and export | Manager / permitted operational | `operations.reporting.summary/export_csv` | Appointment | scoped read/download | PRESENTE; export authorization NOT_VERIFIED |
| Finance bootstrap and summary | Manager, Finance, Accountant, permitted Secretariat | `finance.reporting.bootstrap/summary` | ERPNext accounting documents | scoped read | PRESENTE; mocked |
| Sales/Purchase/Incoming/Bank lists | permitted finance roles | `finance.reporting.records` | Sales Invoice, Purchase Invoice, CC Incoming Invoice, Bank Transaction | scoped read | PRESENTE; mocked Sales list |
| Professional expectation / finance detail | permitted finance roles | `finance.reporting.records`, `finance.professional_economics.position`, `finance.receivables.position`, `finance.incoming.position` | CC Professional Expectation, ERPNext docs | scoped read | PRESENTE; detail live NOT_VERIFIED |
| Administrative queue and manage | finance writer | `finance.admin_queue.list_items/manage` | CC Admin Exception | scoped read/audited POST | PRESENTE; mutation NOT_VERIFIED |
| SdI/TS status only | permitted finance roles | `finance.fiscal.records` | CC Fiscal Transaction | scoped read | PRESENTE; no provider invocation |
| Access memberships read | Manager | `operations.workspace.management_context` | CC Center Membership, User | scoped read | PRESENTE; write UI missing |
| Notifications read | Manager in UI | `frappe.client.get_list` | CC Notification | native permission required | PRESENTE; live permission NOT_VERIFIED |
| Public first encounter | Guest | Existing `www/primo_incontro` / backend flow | Patient / Booking | public guarded | BACKEND_AVAILABLE_UI_MISSING in React |
| Fiscal creation, payment, credit, bank reconciliation, TS/SdI simulation actions | finance writers | existing `finance.*` service methods | ERPNext / CC Fiscal Transaction | audited POST | BACKEND_AVAILABLE_UI_MISSING |
| Package/catalog/assignment forms, private-note correction, print | operational roles | existing domain services | Package, Item, Patient Assignment | scoped read/POST | BACKEND_AVAILABLE_UI_MISSING |

No endpoint was inferred to grant a new permission. No direct generic `/api/resource` call exists in the React source. Role enumeration and negative matrix from #139 are historical fixtures/test methodology only; they have **not** run against this candidate.
