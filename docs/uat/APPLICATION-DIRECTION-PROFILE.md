# Direzione completa / Admin Centro Change — #64

Application profile: **Direzione completa**, implemented by the existing `CC Manager` role. Demo principal `m`. This is a display/profile definition of the current approved role, not a new role, Role Profile document, grant or Administrator account.

The profile accesses Agenda, operational Patients, scheduling/availability, organizational history/notes, Center/Professional/Patient fiscal reporting and exports, Finance/invoices/payments, bank reconciliation, simulated SdI/TS, administrative queue, compensation configuration/override/comparison, access management, notification/first-meeting confirmation recovery and append-only audit register. Each service retains its existing server guard and audit. Sensitive changes still require a reason and canonical services.

Excluded by design: other professionals' confidential notes, infrastructure, runtime configuration, credentials/demo preparator, unrestricted core mutation, technical identity/role provisioning. These exclusions are part of the approved confidentiality/delivery boundary, not missing permissions. `Administrator` and `System Manager` are not operational prerequisites. The existing manager scope is global application management; this task neither expands nor narrows it.

Native catalog setup (practitioners/services/prices/package templates) is currently a guarded technical setup surface, not a newly implemented client catalog editor. Removal of client links to technical setup is tracked in #76. No new catalog capability or additional permission is inferred here.

Decision delta to permission model: **NONE proposed/applied**. Owner review of the explicit profile definition remains required. If Owner intends “complete” to include private clinical notes, infrastructure or different center boundaries, that would require a separately approved exact permission delta; it is not included.
