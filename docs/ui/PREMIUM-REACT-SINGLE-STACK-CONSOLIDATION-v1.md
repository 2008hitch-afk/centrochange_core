# Centro Change — Single-Stack React Consolidation (issue #148)

**Data:** 21/10/2026  
**Stato del TARGET:** `OWNER_APPROVED` — **NON** `CURRENT`, `RELEASED` o `OWNER_ACCEPTED`  
**Stato dell'implementazione:** `PARTIAL / RUNTIME_GATE_BLOCKED`  
**Decisione canonica approvata:** [HC-0005 DECISION-062](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-062-single-stack-react-consolidation.md).  
**Decisioni collegate:** [DECISION-060](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-060-premium-react-frontend-architecture.md) (React + backend canonico), [DECISION-061](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-061-authorize-premium-react-frontend-macro-goal.md) (soli lavoro di sviluppo e test isolati già autorizzati).  
**Issue coordinatrice:** [#148](https://github.com/2008hitch-afk/centrochange_core/issues/148); [PR DRAFT React #150](https://github.com/2008hitch-afk/centrochange_core/pull/150); [issue single-stack #124](https://github.com/2008hitch-afk/centrochange_core/issues/124).

## 1. Target finale esplicito

Il risultato del **medesimo macro-goal #148** diventa **un'unica webapp Centro Change funzionante sull'attuale server**: frontend **React premium** come UI operativa primaria per tutti i compiti ordinari **nel perimetro MVP già approvato**, con Frappe, ERPNext, Marley Healthcare e `centrochange_core` come **solo backend e fonte autorevole** per account, dati, clinica, finanza, permessi, audit e processi.

Stato finale desiderato:
- **1 server esistente**, **1 deployment persistente Centro Change**, **1 Bench logico Frappe**, **1 Site**, **1 DB applicativo del Site**, oltre agli usuali servizi tecnici worker/Redis/MariaDB/websocket; **nessun laboratorio permanente** o backend/frontend parallelo concorrente.
- React = ingresso clienti/operatori; Agenda come home autorizzata, navigation e task per ruolo, ricerche rapide e interfaccia coerente; schermate tecniche ERPNext/Frappe solo per manutenzione specialistica *esplicitamente definita*, mai soluzione di default per le attività quotidiane.
- App **realmente verificata** con Frappe e fixture sintetiche, ruoli/permessi server, API, 11 list+11 form, browser desktop/mobile, i18n italiano, timezone Europe/Rome, prestazioni e recuperabilità.
- Eliminazione controllata **solo** di risorse storiche provate inutili dopo identificazione, backup e specifico gate Owner. Backup/archivi necessari per recovery sono **da preservare**, non sono deploy permanenti.

Questo **integra** l'obiettivo tecnico `READY_FOR_OWNER_VISUAL_UAT` con la destinazione **single-stack consolidata**. Stati da non confondere: `BUILT` → `VERIFIED` → `READY_FOR_OWNER_VISUAL_UAT` → `OWNER_ACCEPTED` → eventuale `RELEASED` → `SINGLE_STACK_CLEANUP_CONFIRMED`. Nessuno stato successivo è implicitamente approvato.

## 2. Current verified / known limitations

- PR [#150](https://github.com/2008hitch-afk/centrochange_core/pull/150) **DRAFT e PARTIAL**; il candidato React e i test browser **su API simulate** esistono, ma **non** provano integrazione server. Recuperare HEAD e `git status` attuali prima di procedere; non usare hash riportati qui come certezza di HEAD.
- Preflight [EXISTING-LAB-REUSE-PREFLIGHT-2026-10-21](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/EXISTING-LAB-REUSE-PREFLIGHT-2026-10-21.md): sul server **solo `centrochange-dev` risulta Compose attivo**; G2D/M97 e altri laboratori erano già stati dismessi. Non c'è alcun vecchio Site completo da riutilizzare. Gli asset storici e volumi non attribuiti non sono automaticamente eliminabili.
- Lo stack temporaneo proposto `centrochange-premium-148` (**10 container, 11 volumi**) è una **variante NON autorizzata e sospesa**, non va avviato/creato come side effect.
- Il precedente limite cgroup `CAP_NOT_ENFORCED`, 2 vCPU, circa 5.1GiB MemAvailable e zero swap (misura storica del 21/10) impediscono di presumere che test runtime aggiuntivi siano innocui; ogni piano deve includere rischi CPU/RAM/disco/PSI e verifica di caps prima di qualsiasi intervento.
- I 45 test sintetici React PASS e 1 SKIP documentati non sostituiscono test live per 7 ruoli+Guest, 128 route×ruolo×viewport, 38 security e 22 liste/form; l'assenza di suite live lascia il candidato `PARTIAL`.
- La [matrice NATIVE-ROUTE-DISPOSITION](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/NATIVE-ROUTE-DISPOSITION.md) indica alcuni editor master ancora `UI_MISSING` (Catalogo/Item/Item Price/Appointment Type/CC Center Service/Package Template, gestione completa anagrafiche, Payment Entry). Non chiamare `completo` il prodotto prima della copertura autorizzata.

## 3. Workstream già autorizzato a Codex — senza micropassaggi ordinari

Senza attendere la futura autorizzazione runtime, Codex può continuare **sulla stessa issue #148 e PR DRAFT #150** a:
1. verificare branch/HEAD/worktree e riusare il codice esistente preservando non-committed changes, senza `reset`, `clean`, secondo `AGENTS.md`;
2. completare interfaccia React, componenti, navigazione e workflow ordinari in scope e gli editor master necessari a compiti quotidiani, *entro API/permessi/business rules già approvati*;
3. per API di scrittura oggi mancanti o permessi materiali, produrre **contratto di dominio + threat model/permission matrix + test negativi proposti**, senza assumere che l'autorizzazione UI autorizzi automaticamente la nuova API;
4. completare report di gap, parity chart, UI tests e test offline/sintetici; non ripetere senza ragione suite identiche già dimostrate, ma eseguire il nuovo candidato quando cambiano aree pertinenti;
5. predisporre **un unico piano di intervento** sul `centrochange-dev` esistente (non ancora eseguito), con inventario/preflight, backup verificabile + restore realizzato prima dell'intervento, esatta base/image/commit/DB, impatto/downtime, fingerprint, procedure controllate, prove server reali con ruoli, criteri di abort/rollback, cleanup e gestione dei vincoli cgroup;
6. predisporre le alternative *senza* introdurre runtime: (A) intervento unico sul DEV esistente solo dopo safety gate completo, (B) eventuale prova temporanea separata solo con **ulteriore** autorizzazione tecnica/rischio, (C) stop motivato se sicurezza non dimostrabile.

Queste attività sono interne all'unico macro-goal; nessun nuovo goal/PR prodotto parallelo o nuova webapp native-first #139.

## 4. Gate Owner obbligatorio prima della prima mutazione sul server

Un **UNICO pacchetto decisionale operativo** dovrà fornire:
- **Risorse nominali e ownership:** ID di container, immagini, volumi, site/DB, network, directory e archivi coinvolti, mutazioni e whitelist, cosa preservare, cosa eventualmente dismettere. Niente glob/prune/reset.
- **Current/proposed:** versioni pinned e app revision, confronto Frappe/ERPNext/Marley/Builder, source HEAD della PR #150, image SHA-256, stato asset CSS/JS e compatibilità API.
- **Rischi e sequenza:** disponibilità risorse live, CPU/RAM/PSI/OOM/cgroup verificati, spazio e tempo indicativi a misura reale, esposizione privata, concorrenza, sicurezza e dipendenze. Non riutilizzare un gate di precedenti deploy #139.
- **Recupero:** backup DB/site/file pubblici-privati/config cifrato e **restore rehearsal dimostrata in contesto realmente isolato** prima della prima scrittura sul DEV; retention locale/offserver ove compatibile; fingerprint prima/dopo, fallimenti fail-closed e un rollback controllato, senza tentativi illimitati.
- **Collaudo:** login/CSRF/same-origin, schema, worker, API/roles (positivi/negativi), centri A/B, note private, 11+11, Agenda, Finanza, catalogo, stampa/campi fiscali, CSV/export, pubblico Guest, performance e visual QA.
- **Pulizia:** oggetti esatti candidati, prove di non-utilizzo, beneficio reale in disco/RAM, archivi indispensabili da salvare, cleanup solo al gate esplicito con verify e abort.
- **Consegna:** report `PASS/PARTIAL/BLOCKED`, dataset sintetico, URL privato accessibile all'Owner solo dopo gate, niente promozione automatica a `OWNER_ACCEPTED`.

**DECISION-062 NON autorizza adesso** deploy/migrate/riavvii/scritture su `centrochange-dev`, creazione di lab temporanei, operazioni Docker mutative, cancellazioni, merge delle PR di prodotto, cutover, GOAL-03, produzione, dati reali, licenze a pagamento, invii provider reali o nuove regole/permessi.

## 5. Collegamenti e scope

- Autorità superiore: governance HITCH e decisioni HC-0005 approvate.
- Stage cliente `ITERATIVE_BUILD_INTEGRATION`, ACTIVE CASE `CASE-001`, ACTIVE RUN `IMPLEMENTATION-001`; GOAL-02 è `AUTHORIZED_ACTIVE` nel manifest nonostante issue #23 `closed`; GOAL-03 `NOT_AUTHORIZED`. Non cambiare implicitamente.
- [#124](https://github.com/2008hitch-afk/centrochange_core/issues/124) documenta precedente TARGET single-stack, che resta coerente con DECISION-062.
- [#139](https://github.com/2008hitch-afk/centrochange_core/issues/139) conserva storia e regression evidence, non equivale a autorizzare terza installazione né a svolgere due UI finali.
- PR [#149](https://github.com/2008hitch-afk/centrochange_core/pull/149) contiene mandato/skill preparatori; PR [#150](https://github.com/2008hitch-afk/centrochange_core/pull/150) codice React. Non effettuare merge impliciti per leggere/riusare la documentazione.

**Obiettivo pratico:** un solo Centro Change realmente funzionante sul server attuale, con UI React premium e backend canonico, collaudo e pulizia governati da gate espliciti; non un server che accumula laboratori.
