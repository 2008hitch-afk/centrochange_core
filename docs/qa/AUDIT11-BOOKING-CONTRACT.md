# AUDIT-11 #201 — Experience-first contract / guest booking

**Status:** IMPLEMENTATION DRAFT / NOT YET OWNER ACCEPTED  
**Baseline:** `main 26d7dcc` → PR #202, `audit-11/public-first-meeting-two-mode`  
**Source of truth:** Owner screenshots shared 03/11/2026 and verbal confirmation. The Fresha link is a **layout and workflow reference**, not an SDK, asset source or license for cloning. No Fresha logo, rating or proprietary UI code is used.

## 1. Outcome and single public journey

- **User role:** anonymous client (Guest), no ERP technical knowledge.
- **Goal:** book a free first meeting, not a subsequent therapy session.
- **Entry point:** `/primo_incontro` (same public React experience as Premium public shell).
- **First action:** choose one of exactly two modes: `In sede` or `Online`.
- **Second action:** choose `Marco` or `Francesca`, never an internal practitioner ID.
- **Third action:** view real 20-minute slots for the chosen mode/director and choose exactly one.
- **Fourth action:** enter minimal identity/contact details, review mode/director/date/slot/**Gratis 0 €**, submit once.
- **Success outcome:** exactly one public Patient Appointment for a free 20-minute conversation; no auto-created or reserved second session; the secretary later arranges a full session through the internal agenda.
- **Backend mapping:** `CC Public Booking Route` identifies the existing director+center; a separate private server mapping `cc_public_first_meeting_types` binds each mode to its own native Appointment Type. `CC Center Service`, `Appointment Type`, `Item Price`, `Patient Appointment`, `CC Patient Assignment`, `CC Booking Confirmation`, audit append remain canonical.
- **Technical fields policy:** never show/accept `center`, `patient`, `practitioner`, `appointment_type`, `price` or `duration` from Guest; server enforces mode, directory allowlist, 20 minutes and 0 EUR.

## 2. Product visuals (owner-provided Fresha patterns, original identity)

Spacious light surface, Centro Change identity, rounded selectable cards, focused single-task stages, desktop summary sidebar and mobile inline summary, large accessible primary CTA, Italian dates HH:mm, clear progress, no group services, gifts, category listing, multi-service cart, external ratings or Fresha branding. Reference screenshots belong to the Owner chat; no copyrighted screenshots shipped in app or Git repo.

**Status of design evidence:** user explicitly selected the pattern. Final screenshot-by-screenshot Owner UAT **NOT_TESTED**; no claim of owner-signed design contract or visual parity without actual side-by-side review.

## 3. Business rules / security

Only `sede` and `online`, only `Marco` and `Francesca`. The two services are **Primo colloquio conoscitivo — 20 minutes — Gratis** and **Seduta — 45 minutes — 44 €**. In sede and Online are modes of the first service, not additional services. The public flow books exactly one free meeting; the secretary books the paid session separately after the meeting. The information box may explain both moments, but 44 € must never be presented as the amount due for the public booking.

Enforce server-side:
- Mapping exists for two different Appointment Type IDs, private and operator-controlled, not Guest-provided.
- Appointment Type is first-meeting, linked to enabled CC Center Service in operational center.
- Live canonical snapshot: `duration=20`, `price=0`, `currency=EUR`, Item service label includes modality to make Agenda distinguish venue from online.
- Public API denies invalid mode/director, inactive center/service, missing/ambiguous mapping, paid/long appointment, slot collision, future horizon breach and identity matching against existing patients; preserve transaction+idempotency, CSRF, rate limits and private audit.
- Confirmation content refers ONLY to booked free meeting and says follow-up is set by secretary. In DEV/UAT messages are simulated, never claim actual SMTP delivery.

## 4. Non-schema runtime configuration — NOT APPLIED

The proposed code reads a private, audited, two-entry site configuration (example placeholders, **not real IDs**):

```json
{"cc_public_first_meeting_types": {
  "sede": "<existing first meeting Appointment Type: 20 min, 0 EUR, Item name indicates sede>",
  "online": "<different first meeting Appointment Type: 20 min, 0 EUR, Item name indicates online>"
}}
```

**Critical:** at writing time we have not verified that both eligible native Appointment Types and zero-price Items exist in the actual center database. We have **NOT** created/modified the types, prices, site_config, DocPerm or schema. Any required data/config authorization is a separate single Owner gate and must be backed up/reversible. No runtime config ⇒ endpoint responds safely unavailable; **no false guest booking.**

## 5. Acceptance evidence to collect before readiness

1. Synthetic browser 1440 / 390: both mode cards only, Director choice, date time, validation, retry, keyboard, errors, empty, mobile no overflow; screen evidence linked to HEAD.
2. Real isolated Frappe/MariaDB clone with **approved synthetic** director/center/config fixtures: both modes and both directors, one free 20 min appointment, distinct service label in Agenda, no paid or second appointment, concurrency and payment snapshots.
3. Negative REST: invalid route/mode, unauthorized service, 44€/45min pre-existing catalog, IDOR, POST/GET and CSRF, replay/different payload, conflicting slots, existing patient email, duplicate submissions and proper cleanup/fingerprint.
4. Confirmation #73: one simulated Communication, no actual send; fail/retry/log correct, says secretary schedules follow-up and notifies only initial meeting.
5. Exact SHA CI PASS, independent reviewer PASS, Owner visual acceptance and **separate STAGING/merge gates**. Do not promote PASS_LOCAL to PASS_LIVE.

**Current result:** implementation candidate / `WAITING_CATALOG_CONFIG_AND_ISOLATED_FRAPPE_UAT` / NO DEPLOY / NO MERGE.
