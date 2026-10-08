# MISSION-A-G2D-BUILD-REGRESSION: PASS

Data: 2026-10-08. Solo DEV sintetico, nessuna acceptance finale GOAL-02, upgrade, deploy RC22 o avvio GOAL-03.
Autorizzazione letta: https://github.com/2008hitch-afk/centrochange_core/issues/95#issuecomment-6067130422
GitHub non modificato, come richiesto dal mandato G2D.

## Sorgente e versioni effettive

- Commit: `e85fce588de6012a47da302710b9f9c615211279`; main remoto verificato identico prima/dopo.
- Tree applicativo accettato: `5eb8051fe36eabcf7a897e2f91d8a97e6918298c`.
- Archivio pulito da `git archive`, senza overlay; 575 file versionati ricontrollati byte per byte dopo le prove: nessun delta. I file host generati `__pycache__` non sono sorgente versionata; la parità nell’immagine è verificata separatamente su tutti i 239 file app.
- Immagine nuova: `centrochange-g2d:e85fce588de6-clean`; ID/manifest locale: `sha256:f8fe936c0b25c7855d266421fad0ae73679b3aa3173e91059e7c81a3fb20fc80`. Nessun push di immagine su registry.
- Frappe **16.31.0**, ERPNext **16.32.0**, Marley Healthcare **16.5.2** (`934d6c162868139dfbe80c23d6102adb7ec25adb`), Builder **1.33.0** (`41987c064da4650e6901b5da82b7c76add452ebf`).
- Base Frappe/ERPNext: `frappe/erpnext:v16.32.0@sha256:481168fa7ba34bb9803e80139dff6df80bc161352cc7b478ae90b0c0da814f90`.
- MariaDB **11.8.8**, digest `24e76fcec8c003a0362d0dd53f4806e7e79458d7fdeaf47437760e19496f5a9c`; Redis **8.6.5-alpine**, digest `cd218f4b106a332c5c992e38a9480bfb9d7e9f8f7b0ec9a0023bfa36d9a408f9`.
- Frappe/ERPNext nell'immagine ufficiale non contengono `.git`: versioni runtime e digest verificati, più confronto hash di 12 file upstream ufficiali ai commit `6a329d068416768ec47ccd3326b9cc95a8d7bf99` / `81a6f97566b83609c3917404a560b673050e907d` / pin Marley e Builder. Non viene dichiarata una lettura Git HEAD per le due app prive di `.git`.
- Playwright **1.58.2**, immagine base digest `6446946a1d9fd62d9ae501312a2d76a43ee688542b21622056a372959b65d63d`; QA tag esclusivo `centrochange-g2d-browser:e85fce588de6-pw1582`. Tabler Core **1.6.1** locale, incluso nella parità applicativa.

## Laboratorio e isolamento

- Progetto `centrochange-g2d-20261008`; site `g2d20261008.local`; frontend **127.0.0.1:8098**.
- Configurazione separata `compose.yaml`, esterna al repository; `docker compose config --format json` controllato PRIMA dello start. Risoluzione sanitizzata conservata in `compose-resolved-sanitized.json`.
- Rete esclusiva `centrochange-g2d-20261008-net`; volumi dedicati `-db-data`, `-sites`, `-redis-cache-data`, `-redis-queue-data`. Nessun mount di codice applicativo. Volumi log anonimi controllati come esclusivi dei rispettivi container G2D.
- Porta verificata libera prima dello start; nessun DB/Redis esposto sull'host. Credenziali nuove fuori Git, `runtime.env` 0600, directory 0700; nessuna credenziale degli ambienti preesistenti letta.
- Il QA browser usa network host solo per raggiungere la porta G2D; ogni `CC_BASE_URL` termina su 8098. Il nome browser `centrochange.local` viene risolto a loopback dal resolver del test; Nginx G2D inoltra il site header esclusivamente a `g2d20261008.local`. Questo non dirige richieste verso RC22, che rimane su 8082.
- Tutti i subprocess Docker delle suite sono controllati nel wrapper esterno: exec limitato al backend G2D, immagini QA nuove, target shared vietati. Nessuna chiamata ai provisioner `uat_candidate.py` o `mission97_lab.py`.

## Clean build, bootstrap e riproducibilità

- **PASS**: build `docker build --no-cache` dal Dockerfile esatto autorizzato, pin/tag/commit invariati, senza patch manuali.
- **PASS**: site nuovo su volumi vuoti; ERPNext setup, installazione Builder/Healthcare/Centro Change, migrate e scheduler tramite configuratore versionato. Solo il DB G2D è stato migrato.
- **PASS**: HTTP ping/login/Desk Administrator, asset nativi/custom/Builder/Healthcare, upgrade WebSocket 101, 2 worker e job reali su short/long, scheduler abilitato. Doctor e health verificati.
- **PASS**: 239 file app nell'immagine identici alla sorgente; sei servizi applicativi running con la stessa immagine. Manifest SHA256 app: `8c5cf4d2a83115c1e59647ced101871b869f6e79dff73003d21cb7f20226653d`.
- **PASS**: smoke Patient/Practitioner/Appointment con cleanup, bootstrap negative checks. Snapshot fresco ripetuto dopo fixture/cleanup identico: `3653dd933a2416e520e12e59dc17ecf6e5a98abb601895aa8a25f363694ccf7d`.
- **PASS**: seed UAT versionato su nuovo site; retry idempotente; validazione semantica `9e1a61146ce666e50f5bf78ccd9995989dbc302e9c2dc6f6942d370583a9c09a`.
- Una sola clean build immagine è stata eseguita: non si dichiara riproducibilità bit-per-bit di due build Docker. Il build Marley segnala assenza di un lockfile Yarn per una fase e risolve dipendenze transitive: pin applicativi/digest rispettati, immutabilità completa delle dipendenze frontend transitive non dimostrata. Nessun pin upstream è stato cambiato.

## Suite eseguite

Static/syntax **PASS**: 172 Python AST, 34 JS/CJS, test statico sei hook.

| Suite | Esito finale | Evidenza / nota |
|---|---|---|
| fresh-runtime | PASS | Harness originale reindirizzato esclusivamente a G2D. |
| direct-integration | PASS | Harness originale reindirizzato esclusivamente a G2D. |
| official-upstream-byte-parity | PASS | Harness originale reindirizzato esclusivamente a G2D. |
| security | PASS (retest) | Prima esecuzione FAIL: assert replay precedente alla conferma simulata; security-retest PASS. |
| finance | PASS | Harness originale reindirizzato esclusivamente a G2D. |
| receivables | PASS | Harness originale reindirizzato esclusivamente a G2D. |
| banking | PASS | Harness originale reindirizzato esclusivamente a G2D. |
| incoming | PASS | Harness originale reindirizzato esclusivamente a G2D. |
| professional | PASS | Harness originale reindirizzato esclusivamente a G2D. |
| reporting | PASS | Harness originale reindirizzato esclusivamente a G2D. |
| sdi | PASS | Harness originale reindirizzato esclusivamente a G2D. |
| ts | PASS | Harness originale reindirizzato esclusivamente a G2D. |
| browser | PASS (retest) | Flows PASS; public inizialmente FAIL su testo legacy; public-retest PASS con conferma simulata e worker Notification Log. |
| finance_browser | PASS (retest) | Prime esecuzioni FAIL su menu/logout mobile; finance-browser-final-retest PASS. |
| threshold-browser | PASS (retest) | Prime esecuzioni FAIL su select nascosto, label legacy e navigazione mobile; threshold-browser-final-retest PASS. |
| backend-review: 7 moduli / 240 controlli | PASS | Rollback; conteggi e SHA256 record canonici invariati. |
| mission97_hooks | PASS | Eseguita sul laboratorio G2D. |
| mission97_http | PASS | Eseguita sul laboratorio G2D. |
| browser-uat | PASS | Eseguita sul laboratorio G2D. |
| browser-professional | PASS | Eseguita sul laboratorio G2D. |
| browser-patient | PASS | Eseguita sul laboratorio G2D. |
| browser-expectations | PASS | Eseguita sul laboratorio G2D. |
| browser-ts_detail | PASS | Eseguita sul laboratorio G2D. |
| browser-confirmation | PASS | Eseguita sul laboratorio G2D. |
| browser-search | PASS | Eseguita sul laboratorio G2D. |
| browser-accounting | PASS | Eseguita sul laboratorio G2D. |
| browser-permissions | PASS | Eseguita sul laboratorio G2D. |
| browser-walkthrough | PASS | Eseguita sul laboratorio G2D. |
| browser-ui_v1 | PASS | Eseguita sul laboratorio G2D. |
| browser-print | PASS | Eseguita sul laboratorio G2D. |
| browser-states | PASS | Eseguita sul laboratorio G2D. |
| browser-agenda_geometry | PASS | Eseguita sul laboratorio G2D. |
| final-lab-health | PASS | Eseguita sul laboratorio G2D. |
| security.audit_view_acceptance | PASS | Fixture storica riprodotta nel solo G2D; mapping ID/date esterno. |
| scheduling.reopen_acceptance | PASS | Fixture storica riprodotta nel solo G2D; mapping ID/date esterno. |
| finance.expectation_ui_acceptance | PASS | Fixture storica riprodotta nel solo G2D; mapping ID/date esterno. |
| finance.bank_trace_acceptance | PASS | Fixture storica riprodotta nel solo G2D; mapping ID/date esterno. |
| browser-audit | PASS | Fixture storica riprodotta nel solo G2D; mapping ID/date esterno. |
| browser-bank_trace | PASS | Fixture storica riprodotta nel solo G2D; mapping ID/date esterno. |

Nessuna suite nella matrice è marcata PASS senza esecuzione. Le prove storiche non sono state saltate: quattro backend e due browser sono state riprodotte con identificativi G2D e fixture canoniche locali. Build/restore DR, performance sotto carico, produzione, provider reali e upgrade non sono in questo mandato e NON VERIFICATI.

## Sicurezza, browser e regressione

- **PASS**: 55 controlli HTTP dedicati ai before_request, oltre ai 240 backend e ai test HTTP/browser di ruolo. Sei hook presenti, in ordine e invocati davvero nel WSGI pinned; diagnostica riservata prima del denial delle note. Principal di servizio, utente disabilitato con sessione conservata, query/report/helper contabili, note private e Guest verificati.
- **PASS**: A/B/C, segreteria, Finance, Accountant e Direzione; cross-center, query/export, direct access, download privati no-store, stampa e payload senza private note. Nessun permission delta.
- **PASS**: booking/reschedule/cancel, collisioni/concorrenza, soglia DECISION-054, prezzi snapshot, note, lifecycle, pacchetti, fiscal simulated workers, fatture/incassi/crediti/correzioni, pagamenti fornitori, riconciliazione nativa, scadenze/differimenti e report/drill-down.
- **PASS**: stale-response operations/Finance, searchable-select positive/no-result/keyboard, shell/debranding/login/logout/403/404, controlli error/empty e stampa, mobile senza document overflow.
- **PASS**: Agenda 15 campioni desktop/tablet/mobile/resize/scroll, 8 track identici; max drift header/body **0 px**, differenza tra larghezze dei giorni al massimo **0,015625 px**, nessuna card nel giorno errato e nessun overflow documento. Screenshot desktop/mobile ispezionati anche visivamente; questo non costituisce Owner visual acceptance globale.

## Adattamenti harness e fallimenti iniziali

Nessun difetto applicativo o leakage rilevato. Nessun codice prodotto modificato. Tentativi iniziali FAIL conservati, distinti dai retest:

1. Security HTTP: assert replay legacy pretendeva solo name/replay, mentre il contratto attuale include confirmation. Wrapper verifica esattamente anche Simulated Sent + confirmation replay; retest PASS.
2. Public browser: frase precedente alla conferma simulata. Test esterno verifica risposta API Simulated Sent e testo italiano effettivo con data/ora e nessuna email reale; retest PASS.
3. Finance/threshold browser: shell mobile richiede apertura menu per logout/navigazione; practitioner usa combobox; condizione economica ora ha label italiana. Test esterni usano i controlli effettivi, mantengono invariato il valore canonico e gli assert di economia/permessi; retest PASS.
4. Prove storiche: ID documento e date/reason di vecchie azioni Owner non esistono in un DB nuovo. Fixture canoniche G2D riproducono threshold N1, override 40, previous_expectation e native reconciliation 60; test backend/browser adattati solo su riferimenti/date/reason. Retest PASS.
5. Un controllo diagnostico aggiuntivo assumeva il medesimo flag nel payload TS e SdI; corretto nel solo harness per verificare TS simulated=true e SdI profile=SYNTHETIC_UNVERIFIED con simulation_only=1. Nessun contratto applicativo modificato.

Diff dei test esterni in `harness-adaptations.diff`; wrapper e traduzioni conservati insieme al report. Nessuna attenuazione dei denial server-side o dei controlli contabili.

## Dataset finale G2D

Dataset nuovo sintetico, nessun reset degli ambienti esistenti. Dopo validazione del seed, scenari aggiuntivi espliciti producono: fattura fornitore annullata, Beta TS READY collegata alla precedente ELIGIBILITY_PENDING senza tentativi, riconoscimento manuale Alfa 40 con posizione sospesa/original_facts conservati, Beta pagata mediante riconciliazione canonica dei 60 residui. Theta conserva 100 di debito. Il seed iniziale non viene dichiarato immutato dopo questi scenari autorizzati nel lab; lo stato finale è coerente e tracciabile.

Verifica finale: 4 transazioni fiscali sintetiche, simulation_only=1, mute_emails=1, 0 Email Account outgoing abilitati e 0 Email Queue. Nessun SMTP/provider/SdI/TS reale. Riapertura/spostamento della prova backend rollback conserva la seduta originale chiusa al 28/09/2026.

## Ambienti preesistenti prima/dopo

- **PASS**: 20 container originali stessi ID, immagine, StartedAt, restart count, mount, reti, porte e progetto. Nessuna risorsa originaria sostituita; tutti i volumi, gli ID rete e le immagini/tag dell'inventario iniziale presenti alla fine.
- RC22: `centrochange-uat:goal02-20261008-rc22`, immagine `sha256:4ce7cbb0bcfbfb9062d4c086e5f0fb8ff51e5025647df4265b4d5630efd97b8c`, source label `f06acca4f6c2ac757dbd3e187709f94b18554b65`, HTTP 8082 **200 prima e dopo**.
- #97: `centrochange-m97:issue97-guards-v3`, immagine `sha256:7fc1313f42bada8df12848af9ac94b7e719e3a99265880bcd4239fc3a6c84888`, HTTP 8097 **200 prima e dopo**.
- Nessun exec, migrate, seed/reset, restart/stop/recreate sui container/DB preesistenti; nessuna modifica DB UAT. Si dimostra integrità delle identità/configurazioni osservate e assenza di comandi mutativi, non un confronto contenuti dei DB condivisi, che non sono stati letti.
- Checkout originale pulito e invariato `issue-97/before-request-guards` / `9d12f5e06df92ed35de843b882f3a40e82c02b19`; main remoto invariato.
- Nessun prune, cleanup globale, rimozione laboratorio, modifica GitHub o produzione.

## Evidenze e prossimo gate

Evidenze conservate fuori Git nella stessa directory: inventari, Compose sanitizzato, manifest parità, build/bootstrap, tutti i log e i JSON delle suite, screenshot. Credenziali escluse dal report, directory privata 0700. Laboratorio mantenuto acceso su 127.0.0.1:8098 per approfondimenti autorizzati.

Screenshot principali: `browser-agenda_geometry/geometry-desktop.png`, `geometry-mobile.png`, `geometry-owner-week.png`; UI matrix in `browser-ui_v1/summary.json`, permessi in `browser-permissions/summary.json`.

**Prossimo gate raccomandato:** review HITCH/Owner di questo evidence package e decisione separata sull'eventuale candidate/promotion. Nessun deploy di main su RC22, nessuna chiusura GOAL-02, nessun upgrade o GOAL-03 autorizzato da questo PASS.
