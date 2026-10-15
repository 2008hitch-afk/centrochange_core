# CENTROCHANGE-MVP-LIVE-FUNCTIONAL-VALIDATION-REPORT

**Esito installazione:** `ROLLED_BACK`  
**DEV aggiornato:** NO — il candidato non è rimasto installato. Il DEV è tornato alla baseline precedente, con rollback verificato.  
**MVP dimostrato in questa esecuzione:** 40/46 PASS storici dell’audit del 14 ottobre; 6/46 restano PARTIAL. Non si rivendica un nuovo 46/46.  
**Sei lacune corrette e verificate live:** 0/6 completamente verificate.  
**Regressioni:** PARTIAL.  
**Centro Change accessibile sulla baseline ripristinata:** SÌ.

Data: 15 ottobre 2026 UTC. Nessun merge, produzione o GOAL-03.

## Baseline, candidato e rollback

- Branch: `audit/mvp-functional-completion`.
- HEAD sorgente applicativo candidato: `d41ac305c6c5f86c37fd0b64e4e588255c467478`.
- HEAD locale con executor aggiornato: `c1c8b98e519442539894fab50c4499b528f02014`.
- Immagine candidata costruita: `sha256:176791e2c6a04f54f4a4221b599d8dc38e028ab8e7c84a6d5bb90c3dc2784e47`.
- Run privato: `/home/empv26/.local/state/centrochange-single/issue139-install-runs/20261015T065956Z-3872744/report.json`.
- Esito: `ROLLED_BACK`; il campo `rollback_failure` è nullo.
- Baseline verificata dopo il rollback: fingerprint dati `c5960487397a020e0cc17319be19778c2b7b1a6240adc6d70eb73edd9f8a8873`; fingerprint Communication `b38c7b6334fd4010251e7258a593c49d5f4efd02c677b41860c2d08055e8c7e2`.
- Runtime: nove servizi presenti e avviati; DB e Redis riportano stato healthy. I sei servizi applicativi sono tornati all’immagine baseline verificata `sha256:2054c8d2ffe887e56bfd0a5a2a867449286e97bee76380119d3c6fcdb9e68cbc` (tag Compose: `centrochange-single:issue139-realtime-v2`).
- Il rollback ha verificato fingerprint runtime, schema/configurazione, permessi, hook e immagini prima di chiudere il run. Il cleanup del fixture finance ha riportato `cleanup: PASS`.

Non sono state cancellate, reseminate o ripristinate le fixture Owner. L’installazione ha creato un backup cifrato privato verificato prima del cambio immagine; nessun segreto o dato demo è incluso in questo report.

## Test live eseguiti

| Area | Esito | Evidenza |
|---|---|---|
| Matrice browser sola lettura, sette ruoli, desktop/mobile | PASS — 128/128 route checks | report privato del run; evidenze Chromium sotto il percorso privato indicato più avanti |
| Liste e schede native | PASS — 22/22 verifiche sulle 11 coppie List/Form | screenshot desktop 1440 e mobile 390 del run |
| Superficie Administrator | PASS | report privato del run |
| Asset serviti e mapping | PASS — 3 asset diretti verificati, 69 mapping manifest | report privato del run |
| Proxy realtime Socket.IO | PASS — origini canonica/tunnel 200; origini estranee/mismatch 403; porta browser 8082 → frontend interno 8080 | report privato del run |
| Fixture/preparazione POS | FAIL tecnico del test harness; cleanup PASS | il comando `centrochange_core.finance.receivables_acceptance.prepare_browser_invoice` restituisce non-zero |
| Flusso pagamento POS nel browser | BLOCKED — non iniziato | il runner si è fermato durante la creazione della fattura sintetica, prima di lanciare Playwright |
| Report GL/TB, export, allegati, suite sicurezza/operazioni e regressione mirata | BLOCKED — non eseguiti in questo run | sequenza abortita al fixture finance; non vengono conteggiati come PASS |
| Integrità dopo il rollback | PASS | fingerprint dati e Communication identici al checkpoint; esito rollback senza failure |

Screenshot e output browser risiedono fuori dal repository in `/home/empv26/.local/state/centrochange-single/browser-evidence/issue139-20261015T065956Z-3872744/`. L’output privato `finance-pos/runner.log` attesta il cleanup PASS e la stack del wrapper. Non contiene l’errore originale di `bench execute`.

## Diagnosi del blocco

La causa prossima è certa: il fixture Frappe `prepare_browser_invoice` è terminato con codice non-zero prima dell’avvio del test POS. Il wrapper `infra/finance_browser_acceptance.py::execute()` cattura stdout/stderr del comando Docker/Bench ma, in caso d’errore, solleva un’eccezione generica con il nome del metodo; il log acquisito pertanto non conserva la specifica eccezione o validazione Frappe. Non attribuiamo il fallimento alla funzione POS né a una regressione applicativa senza quella prova.

La funzione che fallisce prepara una fattura sintetica e un metodo di pagamento ERPNext per il test; non è stato dimostrato quale passaggio interno abbia fallito. Il fixture generale è stato ripulito con la routine esatta e `cleanup: PASS`, quindi il rollback finale ha ripristinato i dati al fingerprint iniziale. Non è stato effettuato un secondo tentativo.

## Stato delle 46 capability

La matrice completa dell’audit originale rimane preservata. La baseline dell’audit era 40 PASS / 6 PARTIAL. Le sei lacune originali restano PARTIAL perché il candidato è stato ripristinato e le verifiche funzionali live non si sono completate:

| Capability | Implementazione nel candidato | Esito live aggiornato |
|---|---|---|
| CC-CAP-029 — export/localizzazione | Implementata nel candidato | BLOCKED: il test export non è stato raggiunto |
| CC-CAP-042 — pagamento singolo carta/POS | Implementata nel candidato | BLOCKED: fixture fattura fallita prima dell’azione POS |
| CC-CAP-047 — Libro giornale/Bilancio di verifica | Implementata nel candidato | BLOCKED: runner report non raggiunto; le schermate native verificate non provano l’esecuzione dei report |
| CC-CAP-050 — fixture/test obsoleti | Aggiornamenti implementati nel candidato | BLOCKED: suite Frappe di sicurezza/operazioni non eseguita |
| SCOPE-DOC — allegati amministrativi | Implementata nel candidato | BLOCKED: upload/download/permessi non eseguiti |
| UAT-GLOBAL — localizzazione/mobile | Correzioni incluse nel candidato | PARTIAL: 128 route e 22 List/Form passano a desktop/mobile, ma i comportamenti specifici di export e multi-select non sono verificati |

I 40 PASS sono quelli già attribuiti dall’audit del 14 ottobre; questa esecuzione ha verificato nuovamente il sottoinsieme route/native indicato sopra, non tutte le 40 capability end-to-end.

## File ed evidenze versionate

- `capability-matrix-completion.csv` aggiornata per distinguere i controlli live passati da quelli bloccati.
- Questo report registra l’esito del singolo aggiornamento e il rollback.
- Report di completamento offline e audit originale restano conservati.
- L’esecuzione non ha modificato il checkout `~/src/centrochange_core` della linea #78 né i dati del DEV dopo il rollback.

Il runner ha bisogno di una correzione diagnostica versionata che conservi un errore Frappe sicuro e limitato (classe e messaggio sanitizzato) quando `bench execute` fallisce. Tale causa va identificata e testata prima di proporre qualsiasi altra installazione. Questo report non autorizza né avvia un nuovo tentativo.
