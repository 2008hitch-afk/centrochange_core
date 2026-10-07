# #77 — Final application permission review

The existing role model is preserved. No delta proposed/applied.

| Principal | Operational patients/sessions | Private notes | Accounting/report/export | Management/audit/recovery | Technical administration |
|---|---|---|---|---|---|
| Professional A/B | Exact assigned Patient/center; own practitioner | Own authored professional context only | No full fiscal access; scoped operational report/export only | Denied | Denied |
| Professional C unassigned | No patients/sessions | None | No full fiscal access | Denied | Denied |
| Secretariat | Authorized centers and current Patient assignments | Denied | Authorized-center read/write, existing policy | Membership/threshold/override/audit denied | Denied |
| Finance | Fiscal projection in authorized centers; no operational Patient API | Denied | Authorized-center read/write | Threshold/override/audit/recovery denied | Denied |
| Accountant | Fiscal projection in authorized centers | Denied | Read-only authorized-center reports; mutation denied | Denied | Denied |
| Manager / Direzione completa | Existing application-wide management scope | Denied without professional authorship/context | Current application read/write | Current audited management services | No System Manager/Administrator grant |
| Guest | Controlled public first-meeting ingress only | Denied | Denied | Denied | Denied |

Manager's existing global application scope is explicit, not a newly expanded membership boundary. No Manager-private-note bypass. Native generic list/print/export/email rights do not follow from hidden navigation: each direct/HTTP probe checks actual permissions. Scoped report exports remain separate from native query-report paths blocked for non-managers. Private financial downloads check parent document scope. Native print on operational Patient/Appointment is not granted; scoped Centro Change session printing remains separately guarded.

Runtime matrix and positive/negative probes: `security.final_review_acceptance.run` and pinned Playwright `permissions.cjs`. Revocation probes use governed services inside full rollback; no seed/reset or lasting Owner dataset change. Subsequent current-candidate critical/report regressions reconcile backend values to canonical sources.

Owner review required before closing #77/final GOAL-02 acceptance. Explicit profile exclusions and native catalog setup boundary in APPLICATION-DIRECTION-PROFILE.md require review, not inferred permission changes.
