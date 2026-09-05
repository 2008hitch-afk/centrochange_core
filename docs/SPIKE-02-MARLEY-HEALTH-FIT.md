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
| S02-PAT-007 | Restricted Physician Custom DocPerm must make zero assignment expose zero Patients before any DocShare exists | Transactional `setup_custom_perms('Patient')`, zeroed Physician Patient rights, temporary removal of A/B Patient User Permissions, rollback | **PASS** | With no Patient shares, both A and B were denied `get_list('Patient')`; `frappe.permissions.has_permission` returned false for read/write on Patient A and B; direct read/write checks were denied with `PermissionError`; rollback restored `Custom DocPerm=0`, both Patient User Permissions, and `DocShare=0` | Scope is limited to zero assignment in normal list/document paths; no DocShare assignment, revocation, reassignment, report/export or Marley endpoint behavior has been tested yet | Restricted Physician Custom DocPerm satisfies the zero-assignment invariant in the tested scope and is a viable foundation for the DocShare experiment; the overall assignment model remains OPEN | Add transactional DocShare A -> Patient A and B -> Patient B; verify assigned-only list/read/write and cross-access denial |
| S02-PAT-008 | A DocShare allow-list must expose only the Patient assigned to each professional when Physician has no global Patient rights | Restricted Physician Custom DocPerm + transactional `DocShare` A -> Patient A and B -> Patient B with read/write, direct Patient User Permissions temporarily removed, rollback | **PASS** | A listed only Patient A and had read/write plus direct read/write on A while all equivalent checks on Patient B were denied; B showed the symmetric result for Patient B; rollback restored `Custom DocPerm=0`, both experimental Patient User Permissions, and `DocShare=0` | Scope is limited to normal list, `has_permission`, and direct document read/write paths; share revocation, reassignment ordering, create/delete/share rights, report/export/query paths and Marley endpoints remain untested | Native Custom DocPerm + DocShare can implement assigned-only Patient read/write in the tested scope; overall assignment model is promising but not yet sufficient for persistence | Remove an active Patient DocShare transactionally and verify access disappears immediately for list, `has_permission`, and direct read/write |
| S02-PAT-009 | Revoking an active Patient DocShare must remove access immediately without affecting another professional's assignment | Restricted Physician Custom DocPerm + transactional A/B DocShares; `frappe.share.remove('Patient', Patient A, A)` followed by immediate permission probes | **PASS** | Before revocation A saw Patient A and B saw Patient B; immediately after removing A's share, A's Patient list was denied and read/write plus direct read/write were denied for both Patients; B still listed only Patient B with read/write true on B and false on A; rollback restored `Custom DocPerm=0`, both experimental Patient User Permissions, and `DocShare=0` | Tested in one process/transaction with cache cleared; no concurrent-request or commit-boundary reassignment behavior has yet been proven | Native DocShare revocation removes the assignment grant immediately in the tested permission paths and does not broaden another user's access; reassignment still requires transaction-order validation | Reassign Patient A from A to B in one transaction, remove old share before adding new share, and verify intermediate/final access semantics |
| S02-PAT-010 | Reassigning a Patient must avoid a dual-access state inside the assignment transaction | Restricted Physician Custom DocPerm + A/B DocShares; remove A -> Patient A first, verify midpoint, then add B -> Patient A in the same Frappe DB transaction | **PASS** in tested single-session sequencing | Initial state: A saw Patient A and B did not. Midpoint after removing A but before adding B: A could not list/read Patient A and B still could not read it. Final in-transaction state: A remained denied while B listed Patient A and Patient B and had read/write on Patient A. Frappe connection reported `REPEATABLE-READ` and `autocommit=0`; rollback restored `Custom DocPerm=0`, both experimental Patient User Permissions, and `DocShare=0` | This probe observed one application/DB session only; it did not exercise a concurrent request or another worker across the commit boundary | `remove-old -> add-new` in one transaction avoids an in-transaction dual-access state and is the safe candidate ordering; production reassignment should be atomic, but cross-session visibility/cache behavior still needs evidence | Validate what another Frappe session sees before and after reassignment commit; do not claim complete no-leakage semantics until that boundary is tested |
| S02-PAT-011 | A concurrent Frappe session must observe only the committed assignment before reassignment commit and the new assignment after commit | Temporary committed restricted Custom DocPerm + initial DocShares; separate writer session performed remove A -> Patient A then add B -> Patient A without commit; explicit fresh observer sessions for A and B probed before and after commit | **PASS** in tested cross-session boundary | Before commit: A listed Patient A and `read Patient A = true`, while B listed only Patient B and `read Patient A = false`. After commit: A's Patient list was denied and `read Patient A = false`, while B listed Patient A and Patient B and `read Patient A = true`. The final baseline was subsequently restored and verified as `Custom DocPerm=0`, two direct Patient User Permissions with A -> Patient A and B -> Patient B, and `DocShare=0` | Scope uses fresh observer sessions and normal Patient list/read permission paths; long-lived observer transactions, write-path cross-session checks, workflow rights and leak vectors remain untested. The V2 cleanup harness initially had a `use`/`user` typo and left the temporary baseline at `0/0/0`; an immediate deterministic restore recreated the two original experimental User Permissions and verified `0/2/0` | Together with S02-PAT-010, the evidence supports atomic `remove-old -> add-new -> commit` reassignment semantics in the tested Frappe/MariaDB paths without a pre-commit grant to B or post-commit grant to A | Determine the minimum create/delete/share rights required by the Patient workflow, then proceed to leak-vector validation |
| S02-PAT-012 | The Patient assignment grant should expose only workflow rights that are actually required, without silently preserving broad Physician privileges | Restricted Physician Custom DocPerm with all Patient role rights zero plus DocShare `read=1, write=1, share=0`; runtime `has_permission` and direct `check_permission` probes; source inspection of Frappe v16 `has_permission` share fallback | **PARTIAL** | For A, assigned Patient read/write were allowed; create/delete/share/report/export were denied. Patient B remained denied for read/write/delete/share/print/email. Rollback restored `Custom DocPerm=0`, two direct Patient User Permissions and `DocShare=0` | `print` and `email` were allowed on the assigned Patient even though those Custom DocPerm rights were zero. Frappe v16 explicitly maps `email` and `print` share checks to the `read` DocShare right (`rights = ['read' if ptype in ('email', 'print') else ptype]`), and standard DocShare has no independent print/email fields. Therefore native DocPerm + DocShare cannot express `read=yes` while `print/email=no` through this mechanism alone. No authoritative Centro Change requirement for practitioner print/email has yet been found | The candidate gives a much narrower privilege surface than default Marley, but its effective grant is `read/write + print/email`, not pure `read/write`. This is a policy/fit gap, not yet an architecture failure: it matters only if Centro Change requires print/email suppression for practitioners | Resolve the intended practitioner policy for Patient print/email from the correct product/security source; if suppression is required, evaluate whether a supported hook/small extension can enforce it without patching Frappe/Marley core |
| S02-PAT-013 | Marley Patient History must not expose medical-record data for a Patient outside the professional's assignment scope | Marley `healthcare.healthcare.page.patient_history.patient_history.get_feed(name)` invoked as professional A with caller-supplied Patient B and a known synthetic Patient Medical Record fixture | **FAIL** in tested endpoint | As `spike02.pro.a@example.invalid`, `get_feed('Spike02 Patient B')` returned synthetic record `HLC-PMR-2026-00001` with subject `SPIKE02 LEAK FIXTURE B`; because the fixture is non-empty and known in advance, the result is probative | Scope is this specific Marley endpoint and synthetic fixture. This does not prove every Marley endpoint bypasses Patient permissions and does not by itself determine Marley option A/B/C | Normal Frappe Patient permissions and Marley whitelisted endpoints must be treated as separate security surfaces. `get_feed(name)` cannot be relied on to enforce the candidate assigned-only boundary without an explicit supported guard or exclusion from the professional-facing surface | Preserve the fixture and test the next high-signal Marley endpoint independently; prioritize `get_feed_for_dt` and selected `patient_progress` methods before defining a mitigation surface |

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

### Transactional zero-assignment probe with restricted Physician permissions

Preconditions observed before the mutation:

- A and B each had only role `Physician`;
- `disable_document_sharing = 0`;
- no Patient `Custom DocPerm` existed;
- no Patient `DocShare` existed;
- the two experimental direct Patient User Permissions were present.

Inside one transaction, standard Patient permissions were copied to `Custom DocPerm`, all Patient rights on the `Physician` custom row were set to zero, and the two direct Patient User Permissions were temporarily deleted. Before any DocShare was created, both A and B were denied the normal Patient list path:

```text
PermissionError: Insufficient Permission for Patient
```

Using the runtime `frappe.permissions.has_permission()` implementation, both users returned `False` for `read` and `write` on both synthetic Patient records. Direct document `read` and `write` permission checks for both records were also denied with `PermissionError`.

The transaction was then rolled back. The persistent state was checked immediately afterward and matched the pre-test state exactly:

```text
Custom DocPerm Patient = 0
Patient User Permission A/B = 2
Patient DocShare = 0
```

Result: **PASS** for the exact zero-assignment invariant in the tested normal list and document paths. This does not yet prove that DocShare provides the required assigned-only allow-list, nor revocation, reassignment, leak-vector behavior, or the final set of workflow rights.

### Transactional DocShare assigned-only probe

Using the same restricted `Physician` Custom DocPerm foundation, the two experimental direct Patient User Permissions were temporarily removed and two native DocShare rows were created in the same transaction:

```text
A -> Spike02 Patient A: read=1, write=1, share=0
B -> Spike02 Patient B: read=1, write=1, share=0
```

Observed as A:

```text
visible Patients -> [Spike02 Patient A]
Patient A read/write -> true / true
Patient A direct read/write -> allowed / allowed
Patient B read/write -> false / false
Patient B direct read/write -> PermissionError / PermissionError
```

Observed as B symmetrically:

```text
visible Patients -> [Spike02 Patient B]
Patient B read/write -> true / true
Patient B direct read/write -> allowed / allowed
Patient A read/write -> false / false
Patient A direct read/write -> PermissionError / PermissionError
```

The transaction was rolled back and the persistent state immediately returned to:

```text
Custom DocPerm Patient = 0
Patient User Permission A/B = 2
Patient DocShare = 0
```

Result: **PASS** for assigned-only Patient list/read/write isolation in the tested normal Frappe permission paths. This materially strengthens the Custom DocPerm + DocShare candidate, but does not yet establish safe revocation, reassignment, create/delete/share policy, leak-vector behavior, or final architectural fit.

### Transactional DocShare revocation probe

The validated restricted Custom DocPerm + DocShare setup was recreated transactionally. Before revocation, A listed only Patient A and B listed only Patient B, with read permission true on the assigned record.

The A -> Patient A share was then removed with native `frappe.share.remove()` and caches were cleared. Without leaving the transaction, A immediately changed to:

```text
Patient list -> PermissionError
Patient A read/write -> false / false
Patient A direct read/write -> PermissionError / PermissionError
Patient B read/write -> false / false
Patient B direct read/write -> PermissionError / PermissionError
```

B remained isolated and unaffected:

```text
visible Patients -> [Spike02 Patient B]
Patient A read/write -> false / false
Patient B read/write -> true / true
```

Rollback again restored the persistent baseline:

```text
Custom DocPerm Patient = 0
Patient User Permission A/B = 2
Patient DocShare = 0
```

Result: **PASS** for immediate revocation in the tested normal permission paths. This does not yet prove behavior across concurrent requests or the commit boundary of a real reassignment transaction.

### Transactional Patient reassignment sequencing probe

The validated restricted Custom DocPerm + DocShare setup was recreated transactionally with initial assignment A -> Patient A and B -> Patient B. The Frappe DB connection reported:

```text
transaction_isolation = REPEATABLE-READ
transaction_autocommit = 0
```

The reassignment sequence was deliberately executed as `remove old share` first, then `add new share`, without committing between those operations.

Initial state:

```text
A visible -> [Spike02 Patient A]
A read Patient A -> true
B visible -> [Spike02 Patient B]
B read Patient A -> false
```

Midpoint, after removing A -> Patient A but before adding B -> Patient A:

```text
A Patient list -> PermissionError
A read Patient A -> false
B visible -> [Spike02 Patient B]
B read Patient A -> false
```

Final state inside the same transaction after adding B -> Patient A:

```text
A Patient list -> PermissionError
A read/write Patient A -> false / false
B visible -> [Spike02 Patient A, Spike02 Patient B]
B read/write Patient A -> true / true
```

Rollback restored the persistent baseline exactly:

```text
Custom DocPerm Patient = 0
Patient User Permission A/B = 2
Patient DocShare = 0
```

Result: **PASS** for the exact single-session transactional sequencing tested. No point in that sequence exposed Patient A to both A and B simultaneously. This is not yet proof of cross-session or multi-worker behavior around commit; that remains a separate gating concern before claiming complete reassignment security.

### Cross-session reassignment commit-boundary probe

A temporary committed candidate permission setup was created so independent Frappe sessions could observe the assignment around a real commit boundary. Initial committed state was A -> Patient A and B -> Patient B under restricted `Physician` Custom DocPerm. A separate writer session then removed A -> Patient A and added B -> Patient A without committing. Explicit fresh observer sessions for A and B were run before commit and again after commit.

While the writer transaction was still uncommitted:

```text
A visible -> [Spike02 Patient A]
A read Patient A -> true
B visible -> [Spike02 Patient B]
B read Patient A -> false
```

After the writer committed, fresh observer sessions reported:

```text
A Patient list -> PermissionError
A read Patient A -> false
B visible -> [Spike02 Patient A, Spike02 Patient B]
B read Patient A -> true
```

Result: **PASS** for the tested cross-session commit boundary. The old assignee continues to observe the previously committed grant before commit; the new assignee does not receive the uncommitted grant. After commit, the old grant is gone and the new grant is visible.

The V2 cleanup harness then hit a test-script typo (`use` instead of `user`) while recreating the two experimental direct Patient User Permissions, leaving the temporary post-test state at `0 / 0 / 0`. This was a harness cleanup defect, not a permission-engine result. A separate deterministic restore was immediately executed and verified:

```text
Custom DocPerm Patient = 0
Patient User Permission A/B = 2
Patient DocShare = 0
A -> Patient -> Spike02 Patient A
B -> Patient -> Spike02 Patient B
```

The PASS is limited to fresh cross-session list/read observations around the tested commit boundary; long-lived observer transactions, cross-session write behavior, workflow rights and leak vectors remain outside this result.

### Patient workflow privilege surface under DocShare

With the restricted `Physician` Custom DocPerm foundation and A -> Patient A / B -> Patient B shares configured as `read=1, write=1, share=0`, A's effective permissions were probed at both DocType and document level.

Observed on A's assigned Patient:

```text
read   = true
write  = true
delete = false
share  = false
print  = true
email  = true
```

At DocType level, `create`, `delete`, `share`, `report` and `export` were false. The unassigned Patient B remained denied for all tested rights, including print/email.

Runtime source inspection explains the surprising print/email behavior. Frappe v16 `has_permission()` defines shareable rights including `email` and `print`, then maps both to the `read` share right:

```text
rights = ["read" if ptype in ("email", "print") else ptype]
```

`DocShare` itself exposes standard fields for `read`, `write`, `share` and `submit`; there are no independent standard print/email fields. Therefore a normal DocShare that grants read also satisfies print/email permission checks on that shared document.

Result: **PARTIAL**. The candidate successfully removes the broad Marley Physician rights for create/delete/share/report/export while preserving assigned read/write, but its effective native grant also includes print/email. No authoritative Centro Change requirement has yet established whether practitioner print/email must be forbidden, so this is currently a policy/fit gap rather than a demonstrated architecture failure.

Rollback restored the persistent baseline exactly:

```text
Custom DocPerm Patient = 0
Patient User Permission A/B = 2
Patient DocShare = 0
```

### Marley `patient_history.get_feed` assignment-boundary failure

A known synthetic `Patient Medical Record` fixture existed for Patient B:

```text
name               = HLC-PMR-2026-00001
owner              = Administrator
communication_date = 2026-09-05
reference_doctype  = null
reference_name     = null
subject            = SPIKE02 LEAK FIXTURE B
```

The Marley Patient History function was invoked under professional A's Frappe identity with Patient B supplied as the target. The observed result contained that known Patient-B fixture.

```text
caller user  = spike02.pro.a@example.invalid
target       = Spike02 Patient B
returned PMR = HLC-PMR-2026-00001
subject      = SPIKE02 LEAK FIXTURE B
```

This is stronger than an empty-feed probe: a known non-empty Patient-B record was returned while execution was under professional A.

Result for the tested endpoint: **FAIL** for assigned-only Patient isolation.

The conclusion is deliberately endpoint-scoped. It does not establish that every Marley endpoint bypasses Frappe permissions, and it does not select Marley option A/B/C.

Architecture implication:

- normal Frappe Patient permission paths and Marley whitelisted methods must be validated separately;
- the candidate Custom DocPerm + DocShare assignment model is insufficient by itself if an application endpoint reads Patient-linked records without enforcing the same assignment boundary;
- `patient_history.get_feed(name)` therefore needs an explicit supported permission guard/extension or exclusion from the professional-facing allowed surface;
- no Frappe or Marley core patch is authorized by this finding.

Next evidence remains incremental: test one additional high-signal Marley endpoint against a known cross-patient fixture before generalizing the result.

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
| Restricted Custom DocPerm zero-assignment behavior | **PASS** — A/B list denied; read/write denied; rollback restored baseline |
| Custom DocPerm + DocShare assignment model | **PARTIAL** — assigned-only A/B, immediate revocation, safe single-session sequencing and fresh cross-session commit-boundary reassignment are PASS; workflow privilege policy and application leak vectors remain open |
| Patient reassignment security | **PASS** in tested scope — remove-old/add-new sequencing and fresh A/B observer behavior across commit are consistent with atomic reassignment |
| Patient workflow privilege surface | **PARTIAL** — create/delete/share/report/export denied as desired in the candidate; assigned read implies print/email through Frappe share semantics, and Centro Change policy for those rights is not yet resolved |
| Marley `patient_history.get_feed` assignment isolation | **FAIL** in tested endpoint — A received known Patient-B PMR fixture |
| Same-practitioner overlap rejection | **OPEN** |
| Practitioner Availability enforcement | **OPEN** |
| Reschedule / move / cancel / history | **OPEN** |
| Reports / export / query leak vectors | **OPEN** |
| Other Marley endpoints using permission-bypassing access | **OPEN** |
| Upgrade / maintenance risk | **OPEN** |
| Final Marley A/B/C fit | **OPEN — no decision** |

## Next test plan

### Phase 1 — Patient assignment security — gating

1. Design a **transactional** test of a restricted `Physician` Custom DocPerm on `Patient` plus Frappe DocShare.
2. Prove the zero-assignment invariant: professional with zero shares sees zero Patients. **PASS in S02-PAT-007 for tested normal list/document paths.**
3. Share Patient A to A and Patient B to B; verify list, `has_permission`, direct read and direct write. **PASS in S02-PAT-008 for tested normal list/document paths.**
4. Remove a Share and verify access disappears immediately. **PASS in S02-PAT-009 for tested normal list/document paths.**
5. Reassign Patient A from A to B and test ordering/transaction semantics so there is no leakage window. **PASS in S02-PAT-010 for single-session sequencing and S02-PAT-011 for fresh cross-session A/B visibility across commit.**
6. Determine which create/delete/share rights are actually required by the Centro Change workflow; do not preserve broad Marley defaults by assumption. **S02-PAT-012 confirms create/delete/share/report/export can remain denied, but Frappe read sharing also grants print/email; intended Centro Change policy for those two rights remains to be resolved.**

Patient reassignment is now sufficiently positive for the tested security gate; the overall assignment architecture remains **PARTIAL** until workflow policy and leak vectors are validated.

Do not persist a new permission architecture until these probes demonstrate the invariant safely.

### Phase 2 — Leak vectors

For Patient and Patient Appointment:

- normal list API;
- direct document access;
- report/query paths;
- export paths;
- relevant Marley whitelisted endpoints — `patient_history.get_feed(name)` is **FAIL** in S02-PAT-013 for the tested cross-patient fixture;
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

---

## Checkpoint 3 — CC-CAP-020 Patient History evidence from automated testlab

The following rows continue the validation matrix with evidence produced by the deterministic `centrochange-testlab` runner. They are additive to the matrix above. `S02-PAT-019` is deliberately retained as a PARTIAL discovery because it invalidated an incomplete surface assumption; `S02-PAT-020` is the corrected follow-up.

| ID | Area / requirement | Native mechanism tested | Result | Positive evidence | Negative evidence / limit | Architecture implication | Next test / decision |
|---|---|---|---|---|---|---|---|
| S02-PAT-014 | Marley `get_feed_for_dt` must not expose Patient Medical Record data for a Patient outside the professional assignment boundary | `healthcare.healthcare.page.patient_history.patient_history.get_feed_for_dt('Patient', Patient B)` under professional A with a known referenced synthetic Patient-B PMR | **FAIL** in tested endpoint | Normal controls established `Patient A read=true`, `Patient B read=false`; the exact Patient-B PMR fixture was nevertheless returned by `get_feed_for_dt` | Endpoint-specific to the tested `reference_doctype=Patient` case and synthetic fixture; does not generalize to every Marley endpoint | Both PMR-returning Patient History paths now have independent non-empty cross-assignment FAIL evidence; the module cannot be used as-is for assigned-only professional access | Evaluate the smallest supported guard/extension surface rather than continuing ad-hoc Patient History endpoint discovery |
| S02-PAT-015 | A Patient Progress endpoint must not reveal cross-assignment Patient activity | Marley `patient_progress.get_patient_heatmap_data(patient, date)` under the same A-allowed/B-denied Patient boundary, measured before/after one exact Patient-B PMR fixture | **FAIL** in tested endpoint | Baseline Patient-B heatmap total was 0; after exactly one Patient-B PMR insert on an unused date, the result visible through the endpoint changed by `+1`; rollback/cleanup verified | This belongs primarily to adjacent Patient Progress / CC-CAP-021 and is not proof that all Patient Progress methods fail | Confirms the authorization concern is not confined to one Patient History function, while preserving endpoint-specific classification | Continue Patient Progress under its own capability gate; do not use this result to decide CC-CAP-020 alone |
| S02-PAT-016 | Determine whether a supported explicit Patient authorization guard can preserve Patient History functionality while enforcing assignment isolation | Reproduced both original Patient History paths, explicit `frappe.has_permission('Patient','read', doc=...)` guard, and per-returned-record Patient filtering | **PASS** for guard semantics | Cross-assignment visibility reproduced for both `get_feed` and `get_feed_for_dt`; explicit Patient guard denied Patient B while preserving a non-empty Patient A result; per-record Patient filtering preserved own PMR and removed cross PMR; rollback/cleanup verified | This proves authorization semantics, not product wiring. `frappe.get_list('Patient Medical Record', filters={'patient': Patient B})` alone still returned the cross fixture | A narrow guarded extension is technically viable. Simply substituting `get_list` for `db.get_all` is not sufficient in the tested runtime | Verify supported Frappe interception/override surface and PMR metadata before recommending implementation shape |
| S02-PAT-017 | Centro Change must be able to guard Marley whitelisted methods without patching Marley core | Installed Frappe `override_whitelisted_methods` dispatch behavior | **PASS** source/runtime evidence | `frappe.handler.execute_cmd` resolves `frappe.override_whitelisted_method(cmd)`; `frappe.override_whitelisted_method` reads the `override_whitelisted_methods` hook; no current override is registered for the two Marley Patient History methods | Does not itself prove a future override implementation is correct; runtime regression tests remain required | A supported extension interception point exists without modifying Marley core | Combine with S02-PAT-016 to evaluate guarded override candidate |
| S02-PAT-018 | Understand why PMR permission-aware list access does not inherit the Patient assignment boundary automatically | Exact runtime `Patient Medical Record` metadata and Physician permission row | **PASS** metadata observation | `Patient Medical Record.patient` has `ignore_user_permissions=1`; Physician PMR permissions include read/write/create/delete/share/report/export/print/email | Metadata alone is not exposure proof; non-empty runtime exposure is established separately in S02-PAT-013/014/016 | Replacing `db.get_all` with `get_list` alone is not a sufficient fix. Global PMR permission redesign would be a separate, broader intervention | Prefer explicit Patient guard candidate unless a simpler global permission model is independently proven |
| S02-PAT-019 | Inventory the complete whitelisted Patient History module surface | AST inspection of exact installed Marley `patient_history.py` | **PARTIAL** discovery | Installed source found; source details for whitelisted functions recorded | Initial assumption that the module exposed only two whitelisted functions was false: a third `get_patient_history_doctypes` function was discovered | The test correctly prevented an incomplete surface conclusion | Correct the expected surface and rerun as V2 |
| S02-PAT-020 | Correctly classify the complete whitelisted Patient History module surface | V2 AST inventory of exact installed `patient_history.py` | **PASS** | Exact surface is three functions: `get_feed`, `get_feed_for_dt`, `get_patient_history_doctypes`; the first two PMR data endpoints use direct `frappe.db.get_all` and no explicit Patient guard was detected; the third reads `Patient History Settings` via `frappe.get_single` | Source pattern is supporting evidence only; runtime security classification for the data methods comes from non-empty probes | All Patient-record feed endpoints in this module are now runtime-tested; the third function is settings/DocType metadata rather than a Patient-record feed path | Patient History endpoint discovery is sufficient for CC-CAP-020 recommendation; no need to treat settings inventory as a Patient-data FAIL |
| S02-PAT-021 | Confirm whether generic Frappe whitelisted RPC dispatch adds document-level authorization around an app method | Exact installed `frappe.handler.execute_cmd` source/runtime inventory | **PASS** source/runtime evidence | Dispatcher checks override resolution, whitelisting and HTTP method, then invokes the resolved method through `frappe.call` | No generic `has_permission` or `check_permission` guard is present in `execute_cmd`; individual methods may still implement their own authorization | Patient-level authorization for these Marley methods must be in the method or a supported override/guard; generic RPC dispatch does not repair the missing boundary | CC-CAP-020 evidence is sufficient for candidate recommendation |

### Automated mutation cleanup baseline

The testlab v0.2 mutation probes enforce rollback and cleanup verification. After the CC-CAP-020 mutating probes, the verified runtime baseline is:

```text
Patient Custom DocPerm = 0
Patient DocShare        = 0
Temporary PAT014/015/016 PMR fixtures = absent
Persistent Patient User Permission A -> Patient A = preserved
Persistent Patient User Permission B -> Patient B = preserved
```

No Frappe, ERPNext or Marley core patch was introduced.

### Patient History module surface and authorization model

The exact installed Marley Patient History module exposes three whitelisted functions:

```text
get_feed(name, ...)
    -> Patient Medical Record via frappe.db.get_all

get_feed_for_dt(doctype, docname)
    -> Patient Medical Record via frappe.db.get_all

get_patient_history_doctypes()
    -> Patient History Settings via frappe.get_single
```

The first two are the Patient-record data endpoints. Both now have independent non-empty cross-assignment runtime FAIL evidence. The third function returns configured DocType names and is not currently classified as a Patient-record exposure path.

The generic Frappe whitelisted RPC dispatcher checks that a function is whitelisted and that the HTTP method is allowed, but it does not add a document-level Patient permission check around the called function. Therefore the assignment boundary must be enforced by the endpoint implementation or by a supported override/guard.

### Why `get_list` alone is not the fix

S02-PAT-016 directly observed that, in the tested runtime, the following permission-aware list query still returned the cross-assignment PMR fixture:

```text
frappe.get_list(
    'Patient Medical Record',
    filters={'patient': 'Spike02 Patient B'},
    ...
)
```

S02-PAT-018 provides the metadata explanation: `Patient Medical Record.patient` is configured with `ignore_user_permissions=1`, while Physician has broad PMR permissions. Therefore changing only the data-access API from `frappe.db.get_all` to `frappe.get_list` is not equivalent to enforcing the Centro Change Patient assignment boundary.

A global PMR permission redesign remains theoretically possible, but it would affect a broader DocType permission model and would still need independent zero-assignment, workflow and upgrade validation. Current evidence does not show it to be simpler or safer than a narrow explicit guard.

### Guarded extension viability

S02-PAT-016 proves the core authorization semantics needed for a narrow extension:

```text
Professional A -> Patient A read = true
Professional A -> Patient B read = false

explicit Patient permission guard:
- Patient A -> allowed
- Patient B -> denied
- own non-empty Patient History result preserved
```

For `get_feed_for_dt`, which accepts a generic `(doctype, docname)`, blindly checking only the caller-supplied reference is not sufficient for all possible reference doctypes. The tested stronger strategy was to include each returned PMR's `patient` and retain only records for which the current user has Patient read permission. That preserved the own fixture and removed the cross-assignment fixture.

S02-PAT-017 confirms that the installed Frappe runtime provides the supported `override_whitelisted_methods` hook. This creates a maintainable extension path in `centrochange_core` without patching Marley core.

### CC-CAP-020 candidate evaluation

1. **Marley Patient History as-is** — **not acceptable** for assigned-only professional access in the tested runtime. Both PMR-returning data endpoints have independent non-empty FAIL evidence.
2. **Native query substitution / `get_list` alone** — **insufficient** as a standalone solution in the tested runtime. PMR metadata ignores Patient User Permissions and the cross fixture remained visible through `get_list`.
3. **Supported guarded extension in `centrochange_core`** — **technically viable and currently preferred candidate**. Explicit Patient authorization semantics are PASS and Frappe exposes a supported whitelisted-method override surface.
4. **Custom Patient History feed** — valid fallback with greater implementation, UX and maintenance cost.
5. **Exclude Marley Patient History from the professional-facing surface** — valid lowest-risk fallback if the feature is not required by the Centro Change UX.

If the guarded extension is later approved for implementation, the minimum expected shape is:

- override `healthcare.healthcare.page.patient_history.patient_history.get_feed`;
- require current-user Patient read permission on the requested Patient before returning feed data;
- override `get_feed_for_dt`;
- authorize returned PMR rows by their Patient and, where product semantics require it, also constrain/authorize the referenced doctype/document;
- preserve the Marley method signatures and response contract used by the page;
- regression-test own/cross Patient, non-empty fixtures, pagination, date/document filters, reference-doctype cases and upgrades.

This is an implementation candidate only; no product code has been changed by the spike.

### Quality / security / development speed / maintenance assessment

- **Security:** Marley Patient History as-is fails the assigned-only requirement. The guarded extension has positive proof of authorization semantics but still requires product implementation and regression coverage.
- **Quality / UX:** a signature-compatible override can retain the Marley page and interaction model; a custom feed carries a larger redevelopment surface.
- **Development speed:** a narrow two-data-endpoint override is materially smaller than rebuilding Patient History or redesigning PMR permissions globally.
- **Maintenance / upgrade:** `override_whitelisted_methods` is an explicit Frappe extension surface, but endpoint signatures, response semantics and permission behavior must be pinned in regression tests for future Frappe/Marley upgrades.

### CC-CAP-020 capability recommendation ready — user decision pending

For **CC-CAP-020 Patient History / clinical feed only**, the current evidence supports the following recommendation:

> **Recommend `EXTENSION`: retain Marley Patient History only behind Centro Change guarded overrides of the two PMR-returning methods, with explicit per-Patient authorization and regression tests.**

This recommendation is **not an approval**, does not authorize product code changes, and does not decide the broader Spike 02 Marley A/B/C outcome. Patient Progress and the remaining Marley authorization surface remain separate capability/security work.

### Phase 2 checkpoint update

The original Phase 2 Patient History discovery objective is now sufficiently evidenced for a capability-level decision:

- `patient_history.get_feed` -> **FAIL** as-is;
- `patient_history.get_feed_for_dt` -> **FAIL** as-is;
- complete Patient History whitelisted module surface -> identified;
- generic Frappe RPC dispatch behavior -> identified;
- PMR metadata explaining `get_list` insufficiency -> identified;
- explicit Patient guard semantics -> **PASS**;
- supported Frappe override surface -> **PASS**.

The broader leak-vector phase remains open for Patient Appointment, reports/export/query paths and adjacent Marley capabilities. In particular, S02-PAT-015 is carried forward into Patient Progress / CC-CAP-021 rather than being used to generalize CC-CAP-020 beyond its tested surface.
