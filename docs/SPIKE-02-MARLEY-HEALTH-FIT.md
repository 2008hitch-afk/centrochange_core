# Spike 02 — Marley Health fit — Runtime Validation Matrix

Status: **IN PROGRESS — RUNTIME VALIDATION REQUIRED**

Issue: #4 — `Spike 02 — Marley Health fit: runtime checkpoint 1`

Branch: `spike-02/marley-health-fit`

Baseline commit before this evidence document: `92ad072557c30d0894c49499d7ab479cccefd834`

## Purpose

This file is the versioned technical knowledge base for Spike 02.

For every significant runtime test, record:

1. the Centro Change requirement being tested;
2. the native Frappe / ERPNext / Marley mechanism used;
3. the observed runtime result;
4. positive evidence;
5. negative evidence or limitations;
6. security / architecture implications;
7. the next test required.

This is a fit investigation, not a final architecture decision. No result in this file, by itself, authorizes Marley option A/B/C.

## Result vocabulary

- **PASS** — the tested requirement is satisfied inside the exact tested scope.
- **PARTIAL** — useful native behavior exists, but it is insufficient for the full requirement or has an unresolved edge case.
- **FAIL** — observed behavior is incompatible with the tested requirement.
- **OPEN** — evidence is not yet sufficient for a result.
- **OBSERVED** — verified fact or implementation behavior used to design later tests; not itself a requirement pass/fail.

A PASS must never be generalized outside the scenario actually exercised.

## Runtime baseline

Synthetic DEV only.

| Component | Runtime |
|---|---|
| Frappe | `16.31.0` |
| ERPNext | `16.32.0` |
| Builder | `1.33.0` |
| centrochange_core | `0.0.1` |
| Marley Health / healthcare | `16.5.2` |
| Marley tag | `v16.5.2` |
| Marley commit | `934d6c162868139dfbe80c23d6102adb7ec25adb` |
| Site | `centrochange.local` |
| Compose project | `centrochange-dev` |
| Data | synthetic only |

Current relevant System Setting:

```text
apply_strict_user_permissions = 0
```

No core patch to Frappe, ERPNext, or Marley is part of the runtime validation described here.

## Persistent synthetic runtime state at checkpoint 2

### Company

```text
Centro Change DEV
abbr = CCD
currency = EUR
```

### Professionals

```text
spike02.pro.a@example.invalid -> HLC-PRAC-2026-00001
spike02.pro.b@example.invalid -> HLC-PRAC-2026-00002
```

Both users have role `Physician`.

Native Frappe User Permissions created for the practitioner link:

```text
A -> Healthcare Practitioner -> HLC-PRAC-2026-00001
B -> Healthcare Practitioner -> HLC-PRAC-2026-00002
```

### Patients

```text
Spike02 Patient A
Spike02 Patient B
```

Current direct Patient User Permissions created during the spike:

```text
A -> Patient -> Spike02 Patient A
B -> Patient -> Spike02 Patient B
```

These Patient permissions are experimental runtime state. They are not yet an accepted assignment architecture.

### Appointment Type

```text
Spike02 Session
allow_booking_for = Practitioner
default_duration = 60
```

### Appointments

```text
HLC-APP-2026-00001
Patient     = Spike02 Patient A
Practitioner= HLC-PRAC-2026-00001
Date        = 2026-09-10
Time        = 10:00:00
Duration    = 60
Status      = Scheduled
Event       = EV00001

HLC-APP-2026-00002
Patient     = Spike02 Patient B
Practitioner= HLC-PRAC-2026-00002
Date        = 2026-09-10
Time        = 10:00:00
Duration    = 60
Status      = Scheduled
Event       = EV00002
```

## Validation matrix

| ID | Area / requirement | Native mechanism tested | Result | Positive evidence | Negative evidence / limit | Architecture implication | Next test |
|---|---|---|---|---|---|---|---|
| S02-BOOT-001 | Site must have a valid ERPNext runtime before Marley business tests | Frappe + ERPNext Setup Wizard | **PASS** | Setup Wizard completed; ERPNext and Frappe report `is_setup_complete=1`; Company and standard masters were created | Initial site was installed but not initialized; manual seeding of missing ERPNext masters failed correctly on native dependencies | Use native ERPNext bootstrap; do not hand-seed standard dependencies | Keep as baseline only |
| S02-MARLEY-001 | Marley must install and migrate without core patching | Marley app install + migrate | **PASS** | `healthcare 16.5.2` installed; migrate and ping passed; required healthcare DocTypes present | Build required `socketio_port` in common config for Marley patient portal assets | Dependency is technically installable with pinned build/runtime configuration | Upgrade-risk review later |
| S02-PERM-001 | User must map to exactly one professional identity | Marley Healthcare Practitioner + native Frappe User Permission | **PASS** | A maps to Practitioner A, B maps to Practitioner B; Marley/Frappe created corresponding Practitioner User Permissions | This proves identity restriction only, not Patient access | Reuse native User -> Healthcare Practitioner link | Continue propagation tests |
| S02-PERM-002 | Professional A must not list Practitioner B | Frappe User Permission on `Healthcare Practitioner` | **PASS** | As A, practitioner list returned only `HLC-PRAC-2026-00001` | Only A-side list probe recorded at this checkpoint | Native Practitioner isolation is promising | Optionally close B-side symmetry later |
| S02-SCHED-001 | A normal practitioner appointment must be creatable through standard DocType behavior | Marley `Patient Appointment` via normal Frappe insert | **PASS** | Appointment A created as `HLC-APP-2026-00001`; Marley populated title, status, start/end datetime and `EV00001` | This is creation-path evidence only; no reschedule/cancel/history conclusion yet | Patient Appointment is viable enough for deeper fit tests | Test lifecycle later |
| S02-SCHED-002 | Different practitioners must be able to occupy the same timeslot | Marley overlap validation | **PASS** in tested case | Appointment B was accepted at the same 10:00–11:00 slot as A when practitioner and patient differed | One positive case does not prove all overlap rules | No false cross-practitioner overlap observed | Test same-practitioner collision and Patient collision |
| S02-PERM-003 | A must list only A appointments | Practitioner User Permission propagation to `Patient Appointment.practitioner` | **PASS** | As A, `get_list` returned only `HLC-APP-2026-00001` | Scope limited to two synthetic appointments | Native Frappe permission propagation works for Patient Appointment list | Test direct read/write and symmetry |
| S02-PERM-004 | A must not directly read or modify B appointment | Frappe permission engine + direct client read + document save | **PASS** | `has_permission` read/write on B = false; direct read = `PermissionError`; direct write = `PermissionError` | Does not yet cover reports/export/custom Marley endpoints | Strong server-side isolation for normal document access | Test leak vectors later |
| S02-PERM-005 | B must be symmetrically isolated from A appointment | Same native permission path as A | **PASS** | B lists only B; own read/write true; A read/write false; direct read/write A both `PermissionError` | Same untested leak vectors remain | Bidirectional Appointment isolation confirmed in normal permission paths | Test reports/query/export/endpoints |
| S02-PAT-001 | Physician must see only assigned Patients under default Marley/Frappe permissions | Marley `Patient` + standard `Physician` DocPerm | **FAIL** | None for isolation | Before direct Patient User Permissions, A listed both Patient A and B and had read/write on Patient B | Default Marley Physician permission model is incompatible with the isolation requirement | Find native-first restriction model |
| S02-PAT-002 | Marley should expose a native Patient -> Practitioner assignment relation usable by Frappe permissions | Patient / Practitioner metadata and Marley permission/assignment source inspection | **FAIL** for direct native relation found | Existing Practitioner relation is strong on Appointment | No Patient field linking to Healthcare Practitioner found; no active Patient-specific permission hook or Marley Patient assignment mechanism found in inspected server-side sources | Do not assume Practitioner User Permission can automatically protect Patient | Evaluate Frappe-native alternatives |
| S02-PAT-003 | Direct Frappe Patient User Permission should restrict an assigned professional | `User Permission: Patient` | **PARTIAL** | With A -> Patient A, A listed only Patient A; own read/write true; Patient B read/write false | Result depends on the user having at least one applicable Patient User Permission | Native mechanism works as allow-list only while at least one rule exists | Test zero-assignment state |
| S02-PAT-004 | Same direct Patient User Permission behavior must work for B | `User Permission: Patient` | **PARTIAL** | With B -> Patient B, B listed only B; direct read/write of Patient A both denied with `PermissionError` | Same zero-assignment risk as A | Symmetric allow-list behavior confirmed | Zero-assignment remains gating test |
| S02-PAT-005 | A professional with zero assigned Patients must see zero Patients | Remove A's sole Patient User Permission transactionally, probe, rollback | **FAIL** | Rollback restored original permission and isolation correctly | With zero Patient User Permissions, A immediately listed both Patient A and Patient B and could read both | Direct Patient User Permission alone is unsafe as the complete assignment model; zero assignment becomes global access | Test role restriction + DocShare or another server-side model |
| S02-CONF-001 | `apply_strict_user_permissions` might solve zero-assignment leakage | Frappe v16 permission/query implementation inspection | **FAIL** as proposed solution | Strict mode can exclude blank Link values when a relevant User Permission exists | It does not create a restriction for a user with no applicable User Permission; Patient also has no Practitioner Link to leverage | Keep `apply_strict_user_permissions=0` during baseline; do not treat strict as Patient assignment solution | No toggle required for this hypothesis |
| S02-PAT-006 | Understand why default Physician sees all Patients | Standard `DocPerm` inspection | **OBSERVED** | Standard behavior is explained deterministically | `Physician` on `Patient` has `read=1`, `write=1`, `create=1`, `delete=1`, `share=1` | Any DocShare assignment model must first remove/restrict global role access | Test reversible Custom DocPerm + DocShare design |
| S02-PERM-006 | A Custom DocPerm can override standard permissions without patching Marley core | Frappe `get_valid_perms`, `setup_custom_perms`, `copy_perms` implementation inspection | **OBSERVED** | Frappe uses Custom DocPerm for a DocType when custom permissions exist, rather than adding standard DocPerm rows for that DocType | No runtime mutation has been performed yet; effect on Centro Change workflows is untested | Candidate native configuration path exists, but it is global and security-sensitive | Design transactional Custom DocPerm + DocShare test before persisting |

## Detailed evidence notes

### Setup Wizard blocker closed

Before setup, the site had ERPNext and Frappe installed but both reported `is_setup_complete=0`. Standard ERPNext masters such as UOM, Warehouse Type, Customer Group, Territory and Fiscal Year were missing. A direct Company insert failed on missing native dependencies.

The native Setup Wizard was completed with synthetic DEV values. Post-setup runtime evidence:

```text
erpnext 16.32.0  has_setup_wizard=1  is_setup_complete=1
frappe  16.31.0  has_setup_wizard=1  is_setup_complete=1

Company        1
Gender         7
UOM            239
Warehouse Type 1
Customer Group 5
Territory      3
Fiscal Year    1
```

Operational conclusion: the initial runtime blocker is closed.

### Patient Appointment validation behavior observed in Marley source/runtime

For practitioner appointments, Marley validates:

- overlap;
- the `appointment_for` target;
- appointment date/time;
- positive appointment end after applying duration;
- Practitioner Availability rows of type `Unavailable`;
- Customer presence only when Healthcare Settings `show_payment_popup` is enabled.

Runtime setting observed:

```text
Healthcare Settings.show_payment_popup = 0
```

Therefore Customer creation was not required for the synthetic appointment probes.

### Appointment isolation evidence

With only the native Practitioner User Permission and `apply_strict_user_permissions=0`:

```text
A get_list Patient Appointment -> HLC-APP-2026-00001 only
A read own  -> true
A write own -> true
A read B    -> false
A write B   -> false
A direct read B  -> PermissionError
A direct write B -> PermissionError

B get_list Patient Appointment -> HLC-APP-2026-00002 only
B read own  -> true
B write own -> true
B read A    -> false
B write A   -> false
B direct read A  -> PermissionError
B direct write A -> PermissionError
```

Conclusion limited to tested normal list/document paths: **PASS**.

### Patient baseline failure

Before direct Patient User Permissions were added:

```text
A visible Patients -> [Spike02 Patient A, Spike02 Patient B]
A can read Patient B  -> true
A can write Patient B -> true
```

Standard Marley/Frappe `Physician` DocPerm on Patient:

```text
read   = 1
write  = 1
create = 1
delete = 1
share  = 1
```

This is incompatible with the Centro Change isolation requirement without additional permission design.

### Direct Patient User Permission: useful but insufficient

After adding:

```text
A -> Patient -> Spike02 Patient A
B -> Patient -> Spike02 Patient B
```

A and B were individually isolated from the other's Patient under `get_list`, `has_permission`, direct read and direct write probes.

However, deleting A's only Patient User Permission inside a transaction produced:

```text
visible_with_zero_patient_permissions:
- Spike02 Patient A
- Spike02 Patient B

zero_perm_can_read_A = true
zero_perm_can_read_B = true
```

After rollback:

```text
permission_exists_after_rollback = true
visible_after_rollback = [Spike02 Patient A]
```

Architecture implication: direct Patient User Permissions are an effective allow-list only when at least one applicable Patient rule exists. They are **not sufficient as the complete assignment model**, because zero assigned Patients must not mean access to all Patients.

### `apply_strict_user_permissions`

Frappe v16 code inspection shows that strict mode changes how empty Link values are handled when a relevant User Permission exists. It does not manufacture a User Permission rule when none exists.

Because Patient has no native Link to Healthcare Practitioner, strict mode is not supported by current evidence as a solution for Patient assignment/isolation.

No change to the setting has been made; baseline remains:

```text
apply_strict_user_permissions = 0
```

### Native Patient-Practitioner assignment search

Inspected Patient/Healthcare Practitioner metadata and relevant Marley server-side permission/assignment code. No direct Patient -> Healthcare Practitioner Link, active Patient permission hook, or Marley-specific Patient assignment mechanism was found in the inspected scope.

This is a negative finding in the inspected version, not a claim about every possible indirect workflow in Marley.

### Custom DocPerm semantics

Frappe v16 `get_valid_perms()` loads standard `DocPerm` and `Custom DocPerm`, but standard rows are retained only for DocTypes that do not have custom permissions. `setup_custom_perms()` copies standard permissions into Custom DocPerm before modifications.

Implication: a reversible native configuration experiment is possible without editing Marley core, but any Custom DocPerm on Patient changes the effective permission model globally for that DocType and therefore must be tested deliberately.

## Current assessment by capability

| Capability | Current evidence |
|---|---|
| Marley install / migrate | **PASS** |
| Native User -> Healthcare Practitioner mapping | **PASS** |
| Practitioner list isolation | **PASS** for A-side probe |
| Patient Appointment list isolation | **PASS** A/B |
| Patient Appointment direct read/write isolation | **PASS** A/B |
| Different practitioners, same timeslot | **PASS** in tested case |
| Default Patient isolation for Physician | **FAIL** |
| Patient isolation with direct Patient User Permission | **PARTIAL** |
| Zero-Patient assignment with direct User Permission model | **FAIL** |
| `apply_strict_user_permissions` as zero-assignment fix | **FAIL** as hypothesis |
| Native Patient -> Practitioner relation | **Not found in inspected scope** |
| Custom DocPerm + DocShare assignment model | **OPEN** |
| Same-practitioner overlap rejection | **OPEN** |
| Practitioner Availability enforcement | **OPEN** |
| Reschedule / move / cancel / history | **OPEN** |
| Patient reassignment security | **OPEN** |
| Reports / export / query leak vectors | **OPEN** |
| Marley endpoints using permission-bypassing access | **OPEN** |
| Upgrade / maintenance risk | **OPEN** |
| Final Marley A/B/C fit | **OPEN — no decision** |

## Next test plan

### Phase 1 — Patient assignment security — gating

1. Design a **transactional** test of a restricted `Physician` Custom DocPerm on `Patient` plus Frappe DocShare.
2. Prove the zero-assignment invariant: professional with zero shares sees zero Patients.
3. Share Patient A to A and Patient B to B; verify list, `has_permission`, direct read and direct write.
4. Remove a Share and verify access disappears immediately.
5. Reassign Patient A from A to B and test ordering/transaction semantics so there is no leakage window.
6. Determine which create/delete/share rights are actually required by the Centro Change workflow; do not preserve broad Marley defaults by assumption.

Do not persist a new permission architecture until these probes demonstrate the invariant safely.

### Phase 2 — Leak vectors

For Patient and Patient Appointment:

- normal list API;
- direct document access;
- report/query paths;
- export paths;
- relevant Marley whitelisted endpoints;
- any endpoint using `frappe.get_all` or other permission-bypassing access where user-facing data could leak.

### Phase 3 — Scheduling invariants

- same practitioner, overlapping appointment -> must be rejected;
- same patient, overlapping appointment -> expected behavior to be defined and tested;
- different practitioners, same slot -> already positive in one case;
- `Practitioner Availability` type `Unavailable` -> conflicting appointment must be rejected;
- availability scope and any Dynamic Link security behavior.

### Phase 4 — Appointment lifecycle

- move/reschedule;
- cancellation;
- history/audit trail;
- Event synchronization;
- behavior when Patient assignment changes before/after appointments.

### Phase 5 — Extensibility and fit

Classify each unmet requirement as:

1. native configuration;
2. native hook / small extension in `centrochange_core`;
3. substantial custom model;
4. incompatible with maintainable Marley reuse.

No direct upstream core modification is allowed.

### Phase 6 — Security and upgrade risk

Evaluate:

- reliance on public vs internal Frappe/Marley APIs;
- permission behavior under upgrade;
- custom permission configuration migration/versioning;
- test coverage required to prevent regressions.

### Phase 7 — Spike decision proposal

Only after the gating runtime tests above, prepare — but do not autonomously approve — one of:

- **A — extended Marley reuse**;
- **B — selective Marley reuse**;
- **C — no Marley reuse for the relevant domain**.

The proposal must trace every recommendation back to this validation matrix.

## Update discipline

After every significant Spike 02 test:

1. add or update one matrix row;
2. record both positive and negative evidence;
3. distinguish runtime fact from inference;
4. record persistent DEV state changes;
5. name the next test that the result changes or enables;
6. do not convert a local PASS into a broader architecture conclusion;
7. keep Issue #4 as the operational checkpoint/index and this file as the structured technical knowledge base.

## Data and governance boundaries

- Synthetic DEV data only.
- No client secrets or real patient/customer data.
- Runtime backups stay outside Git.
- No patch to Frappe/ERPNext/Marley core.
- Native-first, not native-at-all-costs.
- No final Marley fit decision until the spike evidence is sufficient and the user explicitly decides.
