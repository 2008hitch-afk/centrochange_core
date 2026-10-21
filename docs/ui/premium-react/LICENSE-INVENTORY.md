# License and supply-chain inventory — #148

Reviewed before isolated `npm ci --ignore-scripts` on 2026-10-21. Exact direct pins and integrity hashes are in `frontend/premium/package-lock.json` (lockfile v3). No global package, remote installer, paid UI kit or install script executed. `npm audit --json` returned zero vulnerabilities at review time; future registry changes can alter this result.

| Dependency | Pin | License / source | Scope |
|---|---:|---|---|
| React / React DOM | 19.3.1 | MIT, npm / React | runtime |
| React Big Calendar | 1.20.0 | MIT, [upstream](https://github.com/bigcalendar/react-big-calendar) | runtime, multiresource day calendar |
| Day.js | 1.11.21 | MIT, npm | runtime, calendar localizer |
| Lucide React | 0.468.0 | ISC, npm | runtime icons |
| Vite | 8.3.5 | MIT, npm | build only; Node >=22.12, host 22.22.1 |
| TypeScript | 5.9.3 | Apache-2.0, npm | check only |
| Playwright Test | 1.58.2 | Apache-2.0, npm | browser tests only; existing local Chromium cache |
| React types / React Big Calendar types | 19.2.3 / 1.16.3 | MIT, DefinitelyTyped | check only |
| `cldrjs` transitively | 0.5.5 | MIT text in installed `LICENSE-MIT`; `package.json` uses older `licenses` metadata | transitive runtime dependency |
| `lightningcss` transitively | 1.33.0 | MPL-2.0 | build tool only; no source modifications |

Installed package inspection: 60 present packages; 48 package metadata MIT, 5 Apache-2.0, 2 ISC, 1 BSD-3-Clause, 3 MPL-2.0, 1 older metadata resolved to MIT license file. Optional platform packages in lockfile were not all installed; their individual platform license files are **NOT_VERIFIED**. No installed package had `hasInstallScript=true`. The source WebP logo is a separately reviewed brand asset, not an npm license. Owner-directed brand use is recorded; formal redistribution rights remain **NOT_VERIFIED**.

Candidates not installed: Anthropic `frontend-design` and Vercel `web-design-guidelines` local consultative skills, NextLevelBuilder `ui-ux-pro-max`, Vercel `react-best-practices`, OpenAI `frontend-testing-debugging`. Untitled UI React FREE is MIT for its free base but copy-based, not a pinned npm component dependency. FullCalendar Standard is MIT; Premium/Scheduler resources require paid licensing, so no premium package was used. No skill installation was necessary for this candidate.
