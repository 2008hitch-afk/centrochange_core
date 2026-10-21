# #148 — Esecuzione API di dominio React: DECISION-063 (Owner APPROVATO)

**Data:** 21/10/2026  
**Stato:** AUTORIZZAZIONE DI IMPLEMENTAZIONE DEL CODICE, NON PROVA DI COMPLETAMENTO  
**Fonte canonica:** [HC-0005 DECISION-063](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-063-authorize-scoped-react-api-implementation.md).  
**Autorizzazioni collegate:** [DECISION-060](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-060-premium-react-frontend-architecture.md), [DECISION-061](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-061-authorize-premium-react-frontend-macro-goal.md), [DECISION-062](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-062-single-stack-react-consolidation.md).  
**Implementazione:** [issue #148](https://github.com/2008hitch-afk/centrochange_core/issues/148) / [PR DRAFT #150](https://github.com/2008hitch-afk/centrochange_core/pull/150).  
**Input:** [SCOPED-MASTER-API-PROPOSAL.md](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/SCOPED-MASTER-API-PROPOSAL.md), [SYNTHETIC-UI-COVERAGE.md](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/SYNTHETIC-UI-COVERAGE-2026-10-21.md) e [single-stack execution gate](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/SINGLE-STACK-EXECUTION-GATE-2026-10-21.md).

## Outcome autorizzato — opzione A, sviluppo integrato senza micropassaggi

La scelta Owner **«Approvo A»** autorizza a completare **tutte le API di dominio necessarie per le normali attività del MVP** nel repo/branch di #148, entro i **campi, ruoli e business rule già approvati**. Non autorizza un nuovo modello di permessi né l'installazione runtime.

Lavorare dal candidato esistente PR #150, attualmente React `PARTIAL / SYNTHETIC_UI_QA_PASS` con 77 PASS, 1 SKIP, 64 screenshot di sviluppo e 11 liste/form `Archivi` simulate **senza POST**. Questa UI è preview, non evidenza di scritture live.

### Copertura richiesta

1. **Catalogo/servizi** per CC Center Service + ERPNext Item + Marley Appointment Type: list/detail e create/update/enable entro le semantiche già dimostrate; utilizzare o estendere servizi di dominio, **non** CRUD indiscriminato. 
2. **Tariffe/listini**: Item Price in solo dominio Centro Change e price snapshot già approvati, mai retroattivi su appuntamenti già prenotati.
3. **Template pacchetto**: CC Package Template, solo campi/regole già fissati; nessuna nuova unità/eleggibilità/calcolo implicito, nessun edit retroattivo di pacchetti emessi.
4. **Patient e Healthcare Practitioner**: create/edit dei soli campi anagrafici già consentiti ai ruoli/scope correnti, senza toccare note cliniche, assegnazioni riservate, diritti, membership e legami Customer fiscali non approvati.
5. **Payment Entry**: liste e dettaglio *read-only* server-scoped correlati ai flussi finanza già presenti; eventuali azioni di incasso tramite servizi receivables/incoming/banking **già approvati**.
6. **Documenti**: anteprima/stampa *read-only* in formato già governato da ERPNext e permessi effettivi, eventualmente riusando una route sicura pinned se verificata. Niente nuovo formato fiscale o export arbitrario.
7. **React wiring**: client tipizzato per endpoint autorizzati, form stabili e stati completi; preview sintetica resta distinta e non finge salvataggi backend.

Le signature in `SCOPED-MASTER-API-PROPOSAL.md` sono **ipotesi di contratto**; Codex le può implementare solo dopo confronto source-pinned e verifica che campo/ruolo/regola abbiano già fonte approvata. Le scelte con impatto aziendale materialmente nuovo rimangono al gate e la UI relativa resta fail-closed. Non estendere la superficie POST per raggiungere artificiosamente `UI_COMPLETE`.

## Guardrail implementativi e test

- Source of truth: DocType Frappe/Marley/ERPNext e codice `centrochange_core` pinned. Permesso finale server-side basato su sessione, membership centro, permessi nativi DocType e proprietà del record; nessun `ignore_permissions` non giustificato o endpoint CRUD generico esposto a React.
- Whitelist campi per endpoint; validazione tipi, link, centro, valuta/listino se già autorizzati, input non attendibili, output con minima PII, bounded pagination e status/errori uniformi in italiano.
- Denial tests: Guest, ruolo negato, membership revocata, centro A→B, IDOR, linked doc altro centro, payload con campi proibiti, CSRF mancante, `docstatus` e `modified` falsificati, request_key replay, versione stantia, duplicates, error transazionale e assenza di scrittura dopo 401/403/409/422.
- Reuse funzioni/document hooks ufficiali pinned, preserva audit e idempotenza. **Non cambiare permessi esistenti** né dati reali, struttura documenti o logica contabile/clinica.
- Test Python unit/fixture per i servizi API e Vitest/Playwright React con mock; test offline e compile/build. Il live backend, i ruoli 7+Guest e performance rimangono `NOT_VERIFIED` fino al gate DEV separato.
- Eseguire in una sola sessione di sviluppo quanto indipendentemente fattibile, niente conferme per singolo endpoint. In caso di blocco materiale, documentare `BLOCKED_BY_OWNER_POLICY` sul **solo** contratto interessato, completando il resto.

## Esplicitamente non autorizzato

- **NO** nuova allocazione/creazione `Payment Entry` diretta o nuove regole contabili, anche se la proposal la descrive come eventuale.
- **NO** nuove policy prezzi, fiscalità, Patient↔Customer, campi clinici, eleggibilità pacchetti o autorizzazioni di ruoli; i mock non costituiscono autorizzazione.
- **NO** modifica al DEV `centrochange-dev`, build Docker on-host, backup/restore runtime, compose, nuovi Site/volumi/container, cleanup, merge, cutover, produzione, GOAL-03, dati reali, invii SdI/TS/PEC/SMTP/banca.
- **NO** dichiarare `READY_FOR_OWNER_VISUAL_UAT`, `BACKEND_LIVE_PASS` o `FRONTEND_INTEGRATED` dalla sola API codificata con test mock.

## Consegna di Codex nello stesso #148 / PR #150

- Code diff minimal scoped al dominio esistente, con API e React client/UX.
- Contratti endpoint finali + matrice **API → DocType canonico → campi whitelist → ruolo/centro → operazioni → permessi server → test positivi e negativi**.
- Evidenze automatizzate e report separati `API_CODED`, `SYNTHETIC_TEST_PASS`, `LIVE_BACKEND_NOT_VERIFIED`.
- Gap per i contratti non implementabili senza nuova policy, con una sola decisione Owner aggregata.
- Nessuna nuova PR implementativa in parallelo, nessuna espansione scope GOAL-03, nessun runtime deploy.
- Conservare come decisione successiva unica il piano owner-gated di integrazione sul **solo** `centrochange-dev`, dopo safety preflight/backup/restore e suite reali.

## Prompt operativo riusabile nella sessione Codex già aperta

```text
Continua il macro-goal ESISTENTE #148 dalla HEAD effettiva della PR DRAFT #150. L'Owner ha APPROVATO l'opzione A e la DECISION-063 è registrata nel repository HITCH.

Leggi DECISION-060/061/062/063, docs/ui/PREMIUM-REACT-SCOPED-API-IMPLEMENTATION-v1.md su main, SCOPED-MASTER-API-PROPOSAL.md sulla PR #150 e AGENTS.md. Conserva branch/worktree, stato git e lavoro già svolto.

Questo è UN SOLO CICLO DI CODICE: implementa tutti gli endpoint necessari e autorizzati per catalogo/Item/Appointment Type/servizi del centro, Item Price, Package Template, Patient, Practitioner, Payment Entry READ-ONLY, preview/stampa già autorizzata, e collegali alle schermate React. Prima di ciascuna write API ricava fields, ruoli, perimetro centro, permessi e regole già approvate da source/pin; preferisci servizi esistenti. Non inventare alcun campo o permesso per far funzionare una schermata demo.

Implementa endpoint di dominio permission-first (CSRF, cross-center/record-level ACL, whitelisted fields, optimistic locking/idempotenza/audit), read projections bounded e test positivi/negativi con fixture sintetiche. Dove una regola/campo/ruolo non ha fonte approvata, blocca fail-closed quel SOLO ambito e prosegui gli altri senza micropassaggi.

Usa la stessa PR #150, aggiorna React client/wiring, test Python e Playwright desktop/mobile, build/typecheck e report copertura. NON confondere mocked PASS con Frappe LIVE PASS. Non mettere POST veri in preview sintetica senza il backend verificato.

NON autorizzati: Payment Entry create/allocate diretti, nuovi ruoli o policy cliniche/contabili/fiscali, legami Customer inediti, mutazioni/dev deploy/backup/restore/Docker, merge/cutover, dati reali o produzione. Anche se hai sudo, non mutare il DEV.

Consegna API candidate codificate e testate offline, una matrice endpoint→ruolo/campi/DocType→test, gap materiali con proposta unica Owner, e piano esistente di collaudo live separato. Prosegui in autonomia fino alla consegna dello scope fattibile, senza interruzioni per micropassaggi ordinari.
```
