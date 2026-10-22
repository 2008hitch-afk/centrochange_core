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

## Skill review, 2026-10-21

| Skill | Version/provenance | License | Decision |
|---|---|---|---|
| Repo `centrochange-premium-ui` | This PR `.agents/skills/centrochange-premium-ui/`, read with all four references | repo governance | Applied; brand, Frappe, security, UAT constraints |
| Anthropic `frontend-design` | Already available at `/home/empv26/.agents/skills/frontend-design`; upstream [anthropics/skills](https://github.com/anthropics/skills) commit `dbd4588f9e1033efb41dad4bef2f7947c8993d44`; exact installed copy commit **NOT_VERIFIED** | Apache-2.0 in local `LICENSE.txt` | Consulted; no duplicate install |
| Vercel `web-design-guidelines` | Already available at `/home/empv26/.agents/skills/web-design-guidelines`, metadata 1.0.0; [current upstream rules](https://github.com/vercel-labs/web-interface-guidelines/blob/main/command.md) fetched on 2026-10-21; installed copy commit **NOT_VERIFIED** | upstream skill metadata/README say MIT; standalone LICENSE file absent in `agent-skills` | Consulted, no duplicate install or vendor copy |
| NextLevelBuilder `ui-ux-pro-max` | 2.15.0, exact [upstream commit](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/56ea9cf174ed86786187daa9de0e6247cb0747e4) `56ea9cf174ed86786187daa9de0e6247cb0747e4` | MIT `LICENSE` copied with skill | Installed only in isolated worktree `.agents/skills/ui-ux-pro-max/`; read static guidance and React stack data; no helper script or installer executed |
| Vercel `react-best-practices` | metadata 1.0.0, [upstream commit](https://github.com/vercel-labs/agent-skills/tree/063bee94c3f4df8453406c830b0a7df0f2860278/skills/react-best-practices) `063bee94c3f4df8453406c830b0a7df0f2860278` | skill frontmatter and repo README say MIT; full LICENSE file absent at that commit | Read as consultative performance guidance; not vendored because redistribution evidence is incomplete |
| OpenAI `frontend-testing-debugging` | [openai/plugins source](https://github.com/openai/plugins/tree/0722921d5542fc593105c27bd52630babd8b8c2a/plugins/build-web-apps/skills/frontend-testing-debugging), commit `0722921d5542fc593105c27bd52630babd8b8c2a`; plugin not installed | standalone redistributable license **NOT_VERIFIED** | Read consultatively; no copy. Browser plugin absent, so local Playwright was used as its documented fallback. |

No npm UI dependency added. Untitled UI React FREE and FullCalendar Standard remain evaluated candidates; copying their components or adding paid Scheduler is outside this change. Source `ui-ux-pro-max` contains Python tools and catalog data; `PROVENANCE.md` records the pinned source. The skill content is not imported by React and is not part of the client bundle.
