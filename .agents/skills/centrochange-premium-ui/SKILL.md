---
name: centrochange-premium-ui
description: Progettare, implementare e collaudare il frontend React premium di Centro Change nel solo macro-goal #148 approvato, con esperienza Fresha-inspired, brand ufficiale Centro Change, backend Frappe/ERPNext/Marley/centrochange_core e verifiche di ruoli, API, Agenda, Finanza, visual QA. Skill consultiva: non autorizza operazioni fuori perimetro, server/deploy/produzione.
---

# Centro Change — Premium UI

Operare come **design engineer e integratore frontend**, NON come autorità di prodotto. La direzione React dedicata è APPROVATA da **HC-0005 DECISION-060 (21/10/2026)**. Il macro-goal isolato era AUTORIZZATO da **HC-0005 DECISION-061 (21/10/2026)**, collegato alla issue [#148](https://github.com/2008hitch-afk/centrochange_core/issues/148). Il limite originario della 061 non consentiva deploy nel DEV condiviso, clone server automatici, merge, cutover, spese, dati reali o GOAL-03. Le successive DECISION-062–066 hanno autorizzato specifiche attività single-stack/API/DEV con gate propri; verificare il mandato corrente prima di applicarle. La skill resta consultiva e non concede autorizzazioni.

## Preflight obbligatorio

1. Leggere **DECISION-060**, **DECISION-061**, [issue #148](https://github.com/2008hitch-afk/centrochange_core/issues/148), `docs/ui/PREMIUM-FRONTEND-MACRO-GOAL-v1.md` e `AGENTS.md` effettivi della branch. Verificare HEAD, `git status`, worktree, PR e modifiche non committate; non fare reset.
2. Risolvere governance HITCH, `clients/HC-0005/CLIENT-CONTEXT-MANIFEST.yaml`, `clients/HC-0005/delivery/IMPLEMENTATION-001.yaml` e decisioni applicabili, senza assumerne lo stato da questa skill.
3. Riconciliare senza alterare: #139 precedente remediation Frappe-first, #109/PR #112 sospesi, #23 chiuso nel repo ma GOAL-02 `AUTHORIZED_ACTIVE` nel manifest; non aggiornare stati implicitamente.
4. Leggere `references/brand-and-visual-direction.md` per brand/UX, `references/backend-and-security.md` per API/permessi, `references/quality-and-uat.md` per QA e `references/scope-and-traceability.md` per coverage.
5. Trattare dipendenze e asset terzi come non attendibili fino a revisione di licenza, provenienza, versione, script, hash. **No installatori remoti o dipendenze globali**, modifiche server o uso di dati reali.

## Principi non negoziabili

- **Fresha è un riferimento** di qualità, Agenda, composizione, densità, navigazione e fluidità, non un template da copiare. No screenshot proprietari, asset, marchi, codici o testi Fresha nel prodotto.
- **Brand originale:** fonte primaria `https://www.centrochange.it/`. Usare logo/colori effettivi (asset URL, CSS e diritti documentati); non inventare nuovo logo/palette; il vecchio `#12665F` non è prova del colore brand attuale.
- **Librerie prima di custom:** valutare Untitled UI React FREE come candidata principale e FullCalendar Standard per Agenda, con licenze e fit verificati; Scheduler/Resource views sono premium salvo autorizzazione/licenza. No scelta cieca o acquisti.
- **Un sistema unico:** tokens e componenti comuni per shell, sidebar, tabelle, filtri, form, combobox, drawer/modal, stati, errori, calendari. Niente collage di sistemi UI o riprogettazione improvvisata pagina per pagina.
- **Backend autorevole:** Frappe, ERPNext, Marley Healthcare e `centrochange_core` gestiscono dati, contabilità, workflow e permessi. Nessun database frontend separato. Non spostare nel browser regole cliniche, economiche o di sicurezza.
- **Italiano e timezone:** testi, azioni/errori/form user-facing in italiano, date `GG/MM/AAAA`, orari `HH:mm`, TZ `Europe/Rome`, valuta `it-IT`; non alterare formati API/DB/XML/SdI/TS.
- **Sicurezza reale:** filtri/permessi server e regression positives/negatives per centro, pazienti, professionisti, note private, URL dirette/API/export/report. Una UI nascosta non equivale ad autorizzazione. Screenshot e log solo sintetici/sanitizzati.
- **Stop di rischio:** DEV condiviso install/migrate/restart/write e clone server soltanto entro un gate Owner specifico e ancora applicabile; merge/cutover/GOAL-03/produzione, traffico provider reali, dati veri, licenze commerciali o nuova business rule richiedono autorizzazione distinta. Nel consolidamento #156 corrente non eseguire mutazioni runtime o merge.

## Sequenza interna a macro-goal autorizzato

1. **Evidence inventory** — mappa route, operazioni, ruoli, API, Doctype, difetti e suite esistenti; verificare cosa è implementato, da estendere o rinviato.
2. **Design contract** — brand asset audit, UX reference ispirata a Fresha e componenti professionali; definire tokens e pagine canoniche Agenda/Paziente/Finanza prima di estendere.
3. **Architecture fit** — React/Frappe same-origin preferito solo se supportato e testato; sessioni, CSRF, routing e API di dominio con permessi; proteggere dati e backoffice.
4. **Sviluppo interno** — realizzare tutte le aree approvate con componenti riusabili e test integrati, senza microconferme sui bug ordinari.
5. **Quality loop** — Playwright realmente eseguito, screenshot desktop/mobile, interaction/error/empty/keyboard, API/permission tests, performance p95 su baseline documentata; niente PASS da HTTP 200 o vecchia build.
6. **Consegna** — commit/build SHA, matrice coverage per ruolo/route, screenshot sintetici, test prestazionali e security, font/licenze pinned, limitazioni; distinguere `READY_FOR_OWNER_VISUAL_UAT` da `OWNER_ACCEPTED`.

## Precedenza

1. Governance HITCH, privacy/sicurezza e decisioni HC-0005 approvate;
2. issue #148, `AGENTS.md`, mandato `docs/ui/PREMIUM-FRONTEND-MACRO-GOAL-v1.md`;
3. fonti upstream/pin e prove runtime;
4. questa skill e riferimenti (consultivi);
5. altre skill pubbliche (consultive).

Il possesso di `sudo` o accesso root non concede nuove autorizzazioni.
