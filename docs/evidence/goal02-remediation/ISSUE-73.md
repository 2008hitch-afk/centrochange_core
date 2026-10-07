# #73 — Immediate synthetic first-meeting confirmation

Status: TECHNICAL PASS / READY_FOR_OWNER_UAT; Owner UAT-09 recheck required.
Branch `issue-73/first-meeting-confirmation`, base `issue-72/ts-reviewed-detail`.
Named immutable candidate `goal02-20261007-rc24`, source `129dbe1`, same pinned dependencies; all 196 app files byte parity PASS, six identical images, no source overlay.

Migration required only for new CC Booking Confirmation outbox (one unique appointment, immutable recipient/message context, delivery state/attempt/error and native Communication reference). Existing role scopes unchanged: confirmation administration uses existing CC Manager, API/direct writes service-controlled, no new role. Immediate simulated sink inserts native Communication; no sendmail, SMTP, provider or Email Queue call. Recipients must be example.invalid. Public booking replay retains exactly one confirmation. Failed sink delivery rolls back just its partial delivery, keeps booking and failure evidence, and enables reasoned management retry in Notifiche. No new client instructions/business rule.

Backend 8 checks PASS: booking/Communication; replay; content; simulated failure retention; management visibility/retry; retry replay; no Email Queue; unauthorized principals denied. Entire fixture rolled back. Browser PASS: real public slot form; management administration entry; Finance endpoint denied; no JS errors. Browser deliberately does not submit another persistent test patient; the public service mutation path is exercised in the rollback backend test. Dataset preserved, no reset/seed.

Native-first sources: https://docs.frappe.io/framework/user/en/basics, https://docs.frappe.io/framework/user/en/python-api/hooks . Pinned Frappe 16.31.0 `communication/email.py.make(send_email=False)` and Communication controller inspected. Native automatic sending would require a real provider and different delivery semantics; custom outbox uses native Communication plus a strictly simulated sink. No upstream patch. No production/real mail authorization.
