# Centro Change — Native UX and client demo, 20 October 2026

**Result: `CLIENT_DEMO_READY_FOR_OWNER_REVIEW = YES` for a private Owner-led screen-share.** This is not Owner visual acceptance or client acceptance. The native forms are clearer, while the remaining presentation limits below still require the Owner's judgment.

## Installed baseline and safety

- Issue #75; PR #142 approved direction at `8de2e72`; this implementation branch is `issue-75/native-ux-implementation`. Its application source is `cc763958c234c9cbcc8cb46ce9f57533e47410ba`; the later commits contain only the executor, targeted cache refresh, tests and evidence.
- One cumulative DEV update ran with `infra/issue75_native_ux_install.py` SHA-256 `5c4a6fa24b1ee74b7e399b63304b492bfc69dfd56211ebd4ed4ceaf5a24ce50f`. Private gate: 20 October 2026, 07:49:35–11:49:35 UTC operation; recovery reserve until 12:49:35 UTC. The executor returned `DEV_UPDATED_WITH_GAPS`, with **essential installation status PASS**. The two inherited mutative finance/security fixture campaigns were deliberately `BLOCKED` by their previously documented cleanup risk; no critical gate was skipped or relabeled PASS.
- Installed image: `sha256:17380aa9aed4ee287d8c46ed1d851fe94ef42aa6586f3b9f379e0b8aff3f3602`, tag `centrochange-single:issue75-native-cc76395`, on the six application services. All **9/9** project services are running. Database and Redis images, Site and permissions were preserved. Centro A remains active; Centro B remains inactive.
- Four-part Site backup (database, public files, private files, configuration) was encrypted and each part decrypted and hash-verified before activation. A checkpoint and prior-image rollback tags were recorded privately. No rollback or second image update occurred.
- Synthetic data fingerprint before update, after update, after cache refresh and after browser checks: `82dc3825e195bbcd9300f0a6787c043b9f105db324752f06ea3aae23afec7ecd`. The bounded refresh of 11 stale `doctype_form_meta` client-cache keys changed no database record, service, hook or permission fingerprint. No reset or seed occurred.

## What changed

| Problem | Cause | Native-first correction | Live result |
|---|---|---|---|
| Patient and Practitioner Forms foregrounded technical sidebars and scattered optional sections | Default Frappe Form layout and limited section labels | Preserved native fields and validation; translated sections; collapsed optional sections; added a compact field guide and an explicit «Strumenti e tracciabilità» control to reopen native sidebar tools | Both Forms rendered on desktop/mobile with editable native controls and no horizontal overflow |
| Patient invoice did not clearly show paid amount or the next step | Summary omitted paid amount and retained synthetic subject codes | Added state-aware paid/residual display, readable synthetic subject and service in the presentation summary, Italian native labels and input guidance; canonical fields and ledger unchanged | Submitted and canceled examples rendered; canceled document no longer suggests a residual incasso |
| Other native Forms lacked consistent input guidance | Existing Form scripts focused on labels or summaries | Added compact «Come compilare» guidance to Item, Item Price, Appointment Type, Center Service, Package Template, Purchase Invoice, Payment Entry and Bank Transaction; clarified labels in Finance | 11/11 targeted Form types rendered at both desktop and mobile |
| New JS files were served but Forms still showed old presentation | Frappe 16.50 client cache retained old `__js` in `doctype_form_meta` | Versioned, bounded refresh of exactly 11 keys after proving fresh source had the marker | 11/11 refreshed; fresh login displays the installed scripts; data and permissions unchanged |
| First invoice browser probe reported four failures | Probe inspected `cur_frm` before asynchronous Form refresh inserted the context | Added a separate post-render finance probe that waits for the visible context | 4/4 finance Form checks PASS; no application redeploy |

No Agenda source, grid, filter, action, navigation or responsive rule changed. The [desktop before](agenda-before-desktop.png) and [after](agenda-after-desktop.png) screenshots have the **same SHA-256** `02f69ccc4c4ad0c7c6509e52a542dc811275c52258e2d32fb2ac7820b405f40e`; the [mobile before](agenda-before-mobile.png) and [after](agenda-after-mobile.png) screenshots likewise match at `d73f959fa1cd431da1b56507ca99b5af6d55d999c0cb04c865f349082da7357a`. Agenda geometry stayed 14 date elements and widths 1116 px desktop / 330 px mobile.

## Browser and role evidence

- Native Form probe: **20/24 initial PASS**, with four invoice checks racing the asynchronous refresh. Targeted post-render invoice probe: **4/4 PASS**, yielding **22/22 targeted Form/viewport pairs plus 2/2 Agenda snapshots**. These are rendering, field-affordance and navigation checks, not new save transactions.
- Read-only Owner UAT sweep on the installed image: **87/87 routes PASS**, across Direzione desktop/mobile, Segreteria mobile, Professionisti A/B/C mobile, Finance desktop and Commercialista desktop. It found no unexpected writes. The separate demo regression passed **3/3** landing/navigation checks (Direzione desktop/mobile and Finance desktop).
- Essential runtime authorization, Administrator Desk, asset bytes, Socket.IO Origin gate, six hooks, schema and permission fingerprints passed in the installer. Direct unauthorized access checks remain part of its `ESSENTIAL_PASS` read-only suite. No new mutative finance/security fixture campaign was run.
- The prior [MVP completion report](../../mvp-functional-audit/CENTROCHANGE-MVP-DEV-FIRST-COMPLETION-2026-10-19.md) documents **46/46 functional capability PASS** with synthetic transactions. This UX update did not rerun those 46 write workflows. A fresh browser save/persistence test of the modified native Forms is **not claimed** because it would require a verified exact cleanup of new Site and audit records; no Owner demo record was changed merely to obtain a green test.

Private full browser JSON and screenshots: `~/.local/state/centrochange-single/browser-evidence/issue75-native-ux-after/` and `issue75-role-sweep/`. Sanitized comparison screenshots: [Patient before](../empv-ux-audit/screenshots/patient-form.png) / [after](patient-after-desktop.png), [Practitioner before](../empv-ux-audit/screenshots/practitioner-form.png) / [after](practitioner-after-desktop.png), [invoice before](../empv-ux-audit/screenshots/invoice-form.png) / [after](invoice-after-desktop.png), [professional invoice mobile](professional-invoice-after-mobile.png).

## Twelve presentation paths

The [client runbook](../../../uat/CLIENT-DEMO-RUNBOOK-2026-10-19.md) remains the presentation sequence. All **12/12 paths have a currently reachable route** in the 87/87 live sweep and prior functional evidence in the 46-capability package. The updated Patient, Practitioner, Catalog, Tariff and accounting Forms were checked live as detailed above. Booking, notes, POS, bank reconciliation and simulated SdI/TS transactions are supported by earlier functional evidence; they were **not rerun as new write transactions** in this UX update. The Owner should present those with the synthetic examples and explain the previous functional result, rather than implying a new live transaction was performed.

## Remaining concrete limits

1. Some canonical synthetic IDs remain visible inside native editable/read-only fields and line-item tables; the human label is now prominent in the page title or document summary. Replacing those stored field values would change canonical data and is outside this UX update.
2. Pinned upstream native controls still show a few English terms in advanced areas (for example `Internal`, `Immutable Incoming Source` and the rich-text placeholder). Italian localization is therefore **PARTIAL**, not a complete copy PASS.
3. On a narrow screen, native tabs and long table labels are compact and may need horizontal navigation. One mobile Finance screenshot captured a native notification overlay; the Form remained available. Owner visual review should decide whether this impairs the planned screen-share.
4. The new form hierarchy and field guidance were verified visually and with DOM/computed layout checks. New post-update save, refresh and error-recovery transactions on these Forms remain **BLOCKED** by the unverified audit/fixture cleanup path. Underlying functional save workflows had previously passed and no server-side field or permission was changed.

**Access:** Owner uses the existing private SSH tunnel and private demo credentials in the runbook. No direct client account or public DEV exposure was created. PR stays DRAFT; no merge, GOAL-03 or production action occurred.
