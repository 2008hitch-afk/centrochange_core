# Native Form input affordance — candidate evidence

Status: **PARTIAL / not ready for DEV installation**. The unchanged DEV was inspected read-only, then an encrypted synthetic Site backup was restored into a temporary isolated Docker project. The clone served a CSS-only candidate image. The candidate has not been installed on the shared DEV.

## Exact cause

On the pinned Frappe 16.50 `Patient` Form, the loaded `desk.bundle.P52FIUJ5.css`
contains a later `.form-control { border: none }` rule. The existing Centro
Change CSS changes `border-color`, but not `border-width` or `border-style`.
Chromium computed `0px none` on empty `last_name`, `mobile`, `phone`, `email`
and `report_preference`, and also on populated editable controls. The empty
fields therefore had a white surface with no visible boundary.

## Candidate correction

`cc_premium_nexus.css` now sets the complete 1px border on editable Frappe
Form controls, a visible keyboard focus outline, a distinct dashed read-only
surface, and a contextual error border. Every new selector is scoped to
`body.cc-client-desk.cc-native-view .form-page .frappe-control`; no Agenda
selector, DocType, permission, validation or data is changed.

## Browser proof and limits

* Read-only DEV Chromium, Segreteria Patient: PASS desktop and mobile. Ten
  editable controls had a 0px border before; zero after browser CSS preview.
  Seven were empty. Native select, read-only, focus and simulated invalid
  states were distinct. No DEV source, data, service or cache was changed.
* Isolated full Site clone: encrypted backup restore PASS, CSS-only candidate
  image hash PASS, cleanup PASS. Manager password was reset **only on the
  clone** with a randomly generated private fixture. The clone was removed.
* Clone Chromium: **12/22 PASS, 0 FAIL, 10 BLOCKED** across eleven native
  Form routes at 1440px and 390px. Patient, Healthcare Practitioner, Item,
  Appointment Type, CC Center Service and CC Package Template had visible
  empty editable controls at both widths. The five finance Forms (Sales
  Invoice, Purchase Invoice, Item Price, Payment Entry, Bank Transaction)
  showed no editable `.form-control` for the authorised Finance account; a
  Frappe dialog directed the user to the authorised financial reports.
  Their read-only presentation exists, but editable-state acceptance is
  **not demonstrated**. An earlier Manager clone run showed Item Price
  editable at both widths, giving 14/22 PASS for that role mix; the
  final Finance role run is the conservative result.
* Agenda, Segreteria: desktop 1440px and mobile 390px screenshots were pixel
  identical before/after CSS preview; calendar geometry was identical. This
  does not replace a later post-deploy regression.
* Save and refresh persistence, actual native required-field validation,
  all advanced/conditional controls and the remaining role matrix are not
  established by this CSS test. No synthetic document was saved on shared DEV.

Representative sanitised images: `patient-desktop-before.png`,
`patient-desktop-after-preview.png`, `patient-clone-desktop.png`,
`practitioner-clone-mobile.png`, `item-price-clone-desktop.png`,
`patient-focus-preview.png`, `patient-error-preview.png`. Full private clone
matrices remain under `~/.local/state/centrochange-single/browser-evidence/issue75-form-isolated/`.

Baseline DEV: source `e52a88a960a699b08cfad91d2b86e2fbfdcfb6ec`, image
`sha256:6ecc23d0fe6ddc25b294d265546889aedee6049849a2cf58358f0087cb6c611e`,
9/9 services running. No DEV mutation, deployment or restart was performed.

## Test-runner defects corrected

The first clone browser run could not traverse its root-owned evidence directory.
The runner now stores browser artifacts under a separate private directory owned
by `empv26`, with no backup contents exposed. The first attempt at resetting
clone-only Manager credentials then failed because Frappe resolved its log path
from the wrong working directory; the command now uses the pinned Bench `sites`
directory and `FRAPPE_STREAM_LOGGING=1`. Both attempts cleaned the clone and
left the DEV unchanged. Neither condition was an application failure.

## Gate before installation

1. Establish the intended edit path and authorised role for the five finance
   Forms, then test their editable empty, filled, select, focus, error and
   read-only states without altering the shared DEV dataset.
2. Verify actual synthetic save, refresh and persistence in an isolated Site.
3. Freeze one cumulative source commit, verify the exact base image and active
   Compose, run read-only preflight, then request one Owner gate for the
   controlled update with encrypted backup and one rollback path.
