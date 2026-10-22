# AUDIT-02 Navigation Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` in this worktree. Track each test before its code change.

**Goal:** Make the existing Premium navigation complete and center scoped without changing native Frappe login or permissions.

**Architecture:** Keep Frappe as the session and authorization authority. Scope patient projections to the selected Branch on the server, then use the existing search API for header suggestions. Preserve the existing hash route and visual system while fixing URL normalization and mobile keyboard behavior.

**Tech Stack:** Frappe Python, React 19, Vite, Playwright.

**Spec:** GitHub #161 and `docs/qa/FUNCTIONAL-COVERAGE-DETAIL.csv`.

## Global constraints

- Base `335de5709e1c7b477be0b677f69913ecc2f6a9e6`; dedicated branch from `main`.
- No DEV mutation, schema, role, permission, deploy, merge or `cc_premium_primary` change.
- Patient and center IDs stay canonical in API calls; only approved demo aliases appear in UI.
- Tests use synthetic fixtures; distinguish offline and browser fixtures from live Frappe evidence.

## Review focus

- Manager switches A/B: no A patient appears in B bootstrap or search.
- Professional searches: only current assigned patient/center pairs appear.
- Delayed A request after switching B: no A suggestion appears.
- Invalid or unauthorized hash: route and URL return to an allowed landing page.
- Mobile menu and search: keyboard focus remains usable and Escape closes overlays.

### Task 1: Center scoped patient projections

**Files:** `operations/workspace.py`; `tests/test_premium_navigation_scope.py`.

- [x] Write offline tests for manager A/B, professional assignment, denied center and bounded search.
- [x] Run focused tests and observe expected failures.
- [x] Use active `CC Patient Assignment` rows for manager center scope in bootstrap/search; retain document permissions and non-manager assignment guards.
- [x] Run focused tests and complete Python suite (51/51).

### Task 2: Existing shell navigation and global search

**Files:** `frontend/premium/src/main.tsx`, `views.tsx`, `style.css`; `frontend/premium/tests/navigation.spec.ts` or `premium.spec.ts`.

- [x] Write browser regressions for desktop/mobile header search, direct hash/F5/back-forward, role navigation, stale response, menu keyboard and overflow.
- [x] Run focused browser tests and observe failures.
- [x] Add bounded autocomplete with approved `workspace.patient_search`; open the selected patient in the existing Patients view. Normalize invalid hashes. Complete mobile search and menu behavior with current design tokens.
- [x] Run focused browser tests, typecheck, build and full synthetic browser suites (100 pass/8 device skips; scoped 30/30).

### Task 3: Coverage and PR evidence

**Files:** `docs/qa/FUNCTIONAL-COVERAGE-DETAIL.csv`, `docs/qa/PREMIUM-REACT-INTERFACE-INVENTORY.md`, `docs/qa/AUDIT-02-NAVIGATION-REPORT.md`.

- [x] Map each shell action to requirement, React, endpoint, DocType, roles, test and residual live gate.
- [x] Verify source manifest and generated assets; run Python and browser suites. Candidate image is pending the authorized DEV gate.
- [ ] Commit, push the dedicated branch, open reviewable PR, verify GitHub Actions, update #161/#156.

**Owner gate:** DEV installation and real multirole/center UAT require one later controlled authorization with backup and rollback. Do not mark #161 DONE before review, DEV check and Owner walkthrough.
