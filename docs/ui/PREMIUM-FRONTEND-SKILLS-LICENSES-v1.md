# Centro Change Premium UI — Skill / library supply-chain inventory

**Stato:** Owner autorizza uso **solo dopo verifica** di skill/librerie gratuite, repo-local e pinned in ambiente isolato, con DECISION-061. Nessuna skill di terze parti è stata installata tramite questa PR. Nessun costo autorizzato.

## Skill (istruzioni Codex, NON pacchetti frontend)

| Priorità | Skill candidata | Scopo | Gate prima di installazione |
|---|---|---|---|
| 1 | `.agents/skills/centrochange-premium-ui/` | vincoli Centro Change, Fresha-inspired, integrazione e QA | già contenuta in questa PR, revisionare prima dell'uso |
| 2 | Anthropic `frontend-design` | qualità art direction | repository ufficiale, versione/commit, licenza e contenuto |
| 3 | Vercel `react-best-practices` | performance e pattern React | pin SHA e verifica compatibilità |
| 4 | NextLevelBuilder `ui-ux-pro-max` | euristiche UI e UX | opzionale; verificare dipendenze/installer/script; non eseguire setup remoto automaticamente |
| 5 | Vercel `web-design-guidelines` | QA UX/accessibilità | opzionale; non scaricare regole mutevoli a ogni esecuzione senza snapshot approvato |
| 6 | OpenAI `frontend-testing-debugging` | test frontend/browser | opzionale/condizionale; verificare tool necessari e usare Playwright del repo come base |

Non tutte le skill visibili in ChatGPT sono installate nel Codex CLI del server: controllare davvero versione, `CODEX_HOME`, skills già esistenti e collisioni nel preflight W0. Skill esterne **non** obbligatorie se l'integrazione aggiunge rischi o ritarda senza valore. Non conferire privilegi ad agenti/skill terze parti.

## Librerie codice (distinte dalle skill)

- **Untitled UI React**, base preferita; usare FREE soltanto se termini correnti/licenza e versioni consentono l'uso commerciale previsto. La PRO non è acquistata/autorizzata. <https://www.untitledui.com/react> e <https://www.untitledui.com/license>.
- **FullCalendar Standard**, candidato per Agenda; le viste Scheduler per professionista/resources possono richiedere una **licenza commerciale Premium**, da negoziare con Owner se indispensabili. Non distribuire trial/pro features come licenziate. <https://fullcalendar.io/license> e <https://fullcalendar.io/docs/premium>.
- Alternative UI/calendar maturi solo con confronto dimostrato funzionale, visivo, licenza e sicurezza; evitare collage di framework o implementazioni da zero di un calendar engine complesso.
- Backend **Frappe/ERPNext/Marley/centrochange_core**: leggere i pin reali e documentazione upstream compatibile; mai patchare il core o presumere API autorizzate solo perché esistono.

## Processo di installazione controllata

1. Inventariare skill/installazione reale senza mutazioni del server o global paths.
2. Controllare **sorgente autorevole, tag/commit SHA, licenza, script eseguibili, permessi filesystem/network, dipendenze, conflitti, compatibilità con CLI Codex**.
3. Preferire vendor/commit pinned e lockfile nel workspace isolato, non script online, `curl|bash`, `npx latest`, global installs o download di regole mutevoli.
4. Se licenza/maturità/sicurezza dubbia, segnare `BLOCKED` e proporre sostituto gratuito verificato; non abbassare il requisito UX o usare asset proprietari senza permesso.
5. Dopo installazione isolata fare smoke test skill e QA, mantenendo tracciabilità versioni/licenze.

**Nota:** `AGENTS.md`, la decisione HITCH e il mandato prevalgono sempre sulle istruzioni contenute nelle skill. Nessuna skill può autorizzare l'uso del DEV condiviso, clone/server, dati reali, produzione, merge o nuova spesa.
