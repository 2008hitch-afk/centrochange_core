# EMPV — Registro skill Codex (19/10/2026)

Installazione limitata allo spazio utente. Nessun `sudo`, servizio o dipendenza del gestionale modificati. Host Linux `srv2033673`, utente `empv26`, Codex CLI `0.163.0`, Node `22.22.1`, npm `9.2.0`, Git `2.53.0`. Nessuna copia duplicata delle skill Superpowers.

| Skill / pacchetto | Fonte e licenza verificata | Versione / commit fonte | Installazione | Verifica | Attivazione condizionale |
|---|---|---|---|---|---|
| Superpowers (`brainstorming`, `writing-plans`, `test-driven-development`, `systematic-debugging`, `requesting-code-review`, `verification-before-completion`, `using-git-worktrees` e altre) | [obra/superpowers](https://github.com/obra/superpowers), MIT | plugin `6.4.2`; upstream consultato a `bb92a77741419a4ab5f06e711a283343f1ada0c3` | `/home/empv26/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2` | `codex plugin add superpowers@openai-curated-remote --json` riuscito; plugin abilitato, 15 file `SKILL.md` presenti | scegliere brainstorming/planning per problemi aperti, TDD per feature, debugging per difetti, review per codice e verification prima di dichiarare esito. Worktrees solo quando servono. |
| `web-design-guidelines` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills), MIT dichiarata nel README | `063bee94c3f4df8453406c830b0a7df0f2860278`, metadata 1.0.0 | `/home/empv26/.agents/skills/web-design-guidelines` | `npx skills ls -g --json`; SKILL SHA-256 `f4647ca866a3accf763777f83e7682954f0187cd6bea7eea0399796652414e8f` coincide con fonte | audit di navigazione, form, accessibilità, responsive e messaggi. Le linee guida vanno verificate sulla versione corrente; non prevalgono su decisioni cliente. |
| `frontend-design` | [anthropics/skills](https://github.com/anthropics/skills), Apache-2.0 nel `LICENSE.txt` specifico | `dbd4588f9e1033efb41dad4bef2f7947c8993d44` | `/home/empv26/.agents/skills/frontend-design` | `npx skills ls -g --json`; SKILL SHA-256 `d91970639e9f5c37682ac7ab60094d35f1c7c1f38d731bd56396563aee10c1d3` coincide con fonte | prototipi visuali dopo analisi dei compiti; non decide processi o permessi. |
| `caveman` | già presente nella sessione locale | installazione preesistente | `/home/empv26/.codex/skills/caveman` | nessuna modifica | solo su richiesta esplicita. |

## Skill escluse

| Candidata | Fonte verificata | Esito |
|---|---|---|
| `frappe-app-dev`, `frappe-code-review`, `ui-design` | [frappe/skills](https://github.com/frappe/skills), commit `c1118cbf175a3d4393fb7d02d749876eaf8a86e8` | Repository pubblico, ma nessuna licenza OSS esplicita individuata nel repository/skill. Non installate. Usare documentazione ufficiale e sorgente pinned. |
| `deep-app-audit` | stessa fonte | Non necessaria per audit UX; inoltre licenza non verificata. |
| skill ERPNext | [venetanji/erpnext-skills](https://github.com/venetanji/erpnext-skills), commit `0fdf2f865430864469796e59262244bcd2d97562` | README indica «MIT (to be added)» e non contiene LICENSE attuale: esclusa. |

## Orchestrazione EMPV

Codex può scoprire le skill attraverso `codex plugin list` e `npx skills ls -g`; ciò verifica installazione e disponibilità al CLI. Il caricamento in una **nuova sessione interattiva** non è stato provato: stato `NON VERIFICATO`, non dichiarare automaticamente che ogni trigger funzioni. Ogni task sceglie le skill per attività e stack reale; non si eseguono tutte insieme. Le skill generali sono disponibili nei progetti EMPV; Frappe/ERPNext solo nei rispettivi stack dopo licenza verificata; skill grafiche solo in UX/UI; testing e review quando c'è un artefatto appropriato. Nessuna skill sostituisce `AGENTS.md`, decisioni Owner, documentazione upstream pinned o gate del DEV.

### Integrazione minima proposta per `AGENTS.md` (non applicata)

> Prima di ogni attività selezionare soltanto le skill pertinenti al compito e allo stack. Per Frappe/ERPNext verificare licenza OSS e compatibilità con la versione pinned prima dell'uso. Skill UX/UI per audit e prototipi; skill di test per verifica; skill di code review quando esiste codice da rivedere. Le skill sono consultive: istruzioni del repository, decisioni Owner e autorizzazioni operative prevalgono. Evitare installazioni duplicate.

La proposta si aggiunge alle regole esistenti, senza rimuoverle. Nessuna skill può autorizzare deploy o scritture sul Site.
