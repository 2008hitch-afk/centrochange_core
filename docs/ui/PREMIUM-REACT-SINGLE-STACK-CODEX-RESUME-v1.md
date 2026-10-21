# Codex — riprendi #148 / PR #150: Single-Stack React (DECISION-062)

**Da inviare nella STESSA sessione Codex** dopo pubblicazione della DECISION-062 e del presente addendum. Non richiede un nuovo `/goal`.

## Prompt

```text
Riprendi il macro-goal ESISTENTE CENTROCHANGE-PREMIUM-FRONTEND-REBUILD, issue #148, dalla HEAD reale corrente della PR DRAFT #150 (branch issue-148/premium-react-frontend); NON ricominciare e NON creare un nuovo goal.

DECISIONE OWNER FORMALMENTE APPROVATA 21/10/2026: HC-0005 DECISION-062, target Single-Stack React Consolidation, integra DECISION-060/061 e la precedente issue #124. Leggi prima i testi canonici su HITCH GitHub e docs/ui/PREMIUM-REACT-SINGLE-STACK-CONSOLIDATION-v1.md su centrochange_core main. Leggi anche PR DRAFT #149 (mandato/skill) e la tua PR #150 (completion report, capability/route/API/roles/quality/brand), AGENTS.md, #139 e rapporto preflight riuso lab. Verifica branch/HEAD/status/fixture modifiche non committate e preserva rigorosamente tutto il lavoro presente.

RISULTATO FINALE TARGET: sul SERVER ESISTENTE una SOLA webapp Centro Change funzionante, React premium quale unica UI per le operazioni quotidiane, con UN solo deployment persistente, UN Bench logico Frappe, UN Site, UN database applicativo, backend canonico Frappe+ERPNext+Marley+centrochange_core, senza laboratori permanenti o webapp parallele. Il target è APPROVATO, ma non è autorizzato alcun intervento runtime, cambio del DEV condiviso, cleanup o cutover in questa sessione.

Continua AUTONOMAMENTE ciò che rientra nel mandato già autorizzato: codice React sullo stesso worktree/PR #150, design system, Agenda-first, catalogo e gestione ordinaria di servizi/tariffe/pacchetti, anagrafiche, Finanza, documenti e stampa/report (solo funzioni già previste), API contract matrix, test sintetici desktop/mobile, permessi e documentazione. Riusa test e componenti esistenti senza ripetere inutilmente suite già PASS. Verifica con source pinned che le API siano corrette. Per nuove API di dominio in scrittura, nuove regole o modifiche materiali di ruoli/Doctype/sicurezza prepara spec e permission design: FERMA quella modifica al gate Owner, senza usare CRUD generico o indebolire permessi.

La variante di ambiente temporaneo 'centrochange-premium-148' della PR #150 NON è approvata: non crearla, non eseguire Docker build/run/compose su host, non installare né sostituire il DEV attuale. Inventario read-only del 21/10 ha rilevato un solo Compose attivo 'centrochange-dev', nessun vecchio Site/DB riutilizzabile, risorse 2CPU, ~5.1GiB MemAvailable, zero swap e rischio storico cgroup. Non trattare questi numeri come misure live odierne.

PREPARA in parallelo al lavoro offline UN SOLO piano esecutivo di consolidamento sul DEV ESISTENTE, da sottoporre all'Owner: whitelist precisa di risorse/ID/porte/volumi/immagini/DB/Site da preservare/modificare/eliminare, prove di ownership, pin/SHAs, verifica RAM/cgroup/PSI/disk, backup cifrato e restore rehearsal PRIMA della prima mutazione, recovery/rollback, sequenza upgrade e test login/CSRF/API, 7 ruoli+Guest, 128 route, 38 security, 11 list+11 form, finanza, catalogo, p50/p95, italiano GG/MM/AAAA HH:mm Europe/Rome, intervento reversibile, possibili impatti/downtime, pulizia dopo prova di non-utilizzo e risultato Owner. Evidenzia se un test temporaneo separato sia tecnicamente indispensabile e chiedi un gate specifico invece di predisporre un secondo stack non autorizzato.

NON effettuare: deploy/migrate/restart/write su centrochange-dev, clone/site temporanei, modifiche host, build Docker runtime non approvata, cancellazioni/prune/reset, segreti/provider reali, dati reali, licenze a pagamento, GOAL-03, produzione, nuove regole cliniche/contabili, merge delle PR di prodotto, cutover o dichiarazione Owner PASS. Non modificare altri clienti o repo system con dati Centro Change. Un accesso sudo non amplia il mandato.

Output: aggiorna PR DRAFT #150 con i progressi offline, conserva evidenze e report sanitizzati, indica BUILD/PASS sintetici separatamente dai test Frappe reali NOT_VERIFIED, scegli READY_FOR_OWNER_VISUAL_UAT solo dopo runtime/QA reale PASS (non ora), oppure PARTIAL/BLOCKED con UN SOLO gate Owner operativo con piano esatto. Non avviare un nuovo goal e non chiedere microconferme per codice/test già autorizzati.
```

## Nota di applicazione

Il testo è coerente con DECISION-062 ma non autorizza operazioni runtime. **Il target finale non è sinonimo di permesso di sostituire il server.** Qualsiasi dubbio materiale sui limiti di risorse, cambio sicurezza, copy di dati o nuovo runtime esige un gate.
