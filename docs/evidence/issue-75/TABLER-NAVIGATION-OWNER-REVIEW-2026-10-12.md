# Issue #75 — Navigazione unica Tabler per GOAL-02

> **Review Owner successiva: NON ACCETTATA.** Gli otto difetti sono registrati nella issue #75. Questo rapporto conserva l'esito tecnico storico della prima versione; l'intervento correttivo e il nuovo collaudo sono in [TABLER-UI-CORRECTION-OWNER-RETEST-2026-10-12.md](TABLER-UI-CORRECTION-OWNER-RETEST-2026-10-12.md). Nessun `OWNER VISUAL PASS` è attribuito alla PR #126.

**Esito: `CENTROCHANGE_TABLER_NAVIGATION_READY_FOR_OWNER_REVIEW` (2026-10-12, 13:10 UTC).** Review visiva Owner e accettazione finale GOAL-02 ancora aperte. Branch `issue-75/tabler-navigation` stacked su PR DRAFT #125, che conserva PR DRAFT #112/#107; nessun merge.

## Delta

La vecchia barra orizzontale globale, la seconda barra Unified Desk e la Home con molti duplicati sono sostituite da una sola sidebar persistente e una navbar essenziale. La sidebar compare anche su Patient e Healthcare Practitioner nativi. La navbar mostra identità Centro Change, contesto, notifiche consentite, utente/ruolo e uscita. I gruppi Amministrazione e Gestione sono sottomenu richiudibili; la sidebar desktop si riduce a icone e quella tablet/telefono si apre con tastiera o click. La Home mostra tre accessi rapidi operativi per ruolo, senza KPI inventati.

Componenti `.navbar.navbar-vertical`, `.nav-link`, `.card` e `.card-body`, icone Tabler locali e Tabler Core **1.6.1** pinned seguono [il design system approvato](../../ui/CENTROCHANGE-UI-DESIGN-SYSTEM-v1.md) e la [guida ufficiale Tabler ai layout](https://docs.tabler.io/ui/layout/page-layouts). Nel Desk, il foglio ufficiale è caricato nel layer CSS `cc-tabler` a priorità bassa: i CSS nativi Frappe restano prevalenti sulle proprie List/Form. Colore primario `#12665F`. Nessun CDN, React, upgrade o nuova dipendenza.

I link preesistenti restano raggiungibili nel menu organizzato; i controlli e la navigazione contestuali delle singole viste restano nelle viste. `#navigation` e `#logout` interni a Unified Desk sono mantenuti nel DOM per i moduli operativi esistenti ma non costituiscono una seconda barra visibile. Nessun cambiamento a schema, DB, API, permessi, prenotazioni, contabilità, note, SdI/TS o workflow. L'Administrator tecnico continua a saltare la shell cliente.

## Runtime e deploy

È stato usato soltanto il progetto `centrochange-dev` della issue #124 sullo stesso server: un Bench logico, Site `centrochange.local`, DB applicativo `_4f614b4543aa5230`, nove servizi attivi e un configurator one-shot terminato. Nessun reset, seed, clone di DB o laboratorio parallelo. Immagine base #124 verificata `sha256:8822eee88b37d1659d94c8eb95c8bc737f75edb605042f96809eda2f9199e1b2`; `infra/Dockerfile.issue75` copia solo i quattro asset sorgente UI modificati e ricostruisce gli asset. Immagine installata `sha256:64411134578d655f7829495959693c6ea12b53e25a54050215edd607029aaaf8`. Frappe/ERPNext 16.50.0, Builder 1.35.1, Healthcare 16.6.1 invariati.

Deployment sul progetto esistente: build derivata, aggiornamento del solo `CC_UAT_IMAGE` nella env privata 0600, `docker compose ... up -d --no-deps backend frontend websocket queue-short queue-long scheduler`, poi `bench --site centrochange.local clear-cache`. Il volume Site contiene un link a `assets` dell'immagine; il clear-cache invalida il manifest bundle precedente. Gli asset CSS Desk e Tabler pinned rispondono HTTP 200. I container DB/Redis e i volumi non sono stati ricreati.

## Test

Browser plugin non disponibile in questa sessione: Playwright Chromium pinned in container QA temporaneo da 512 MiB. `infra/browser/issue75_navigation.cjs` prova i sette account demo `m,s,a,b,c,f,t` a 1440×900, 768×900 e 390×844: una sola sidebar, nessuna routebar, menu attesi/assenti, tre accessi rapidi Home, Tabler locale, link Agenda o Finanza, passaggio Manager custom→Patient nativo→custom, sottomenu e sidebar tramite tastiera, account/uscita, nessun overflow e nessun errore JavaScript. **PASS 7/7**. `infra/browser/issue75_six.cjs` prova Home, Agenda, Pazienti, Professionisti, Finanza e Report con dati visibili: **PASS 6/6**, errori JavaScript zero.

Controlli server: `infra/issue75_role_api.py` **PASS** su tutti e sette i ruoli con chiamate HTTP dirette, inclusi A/B/C (6/1/0 pazienti in scope e `patient_history` di un paziente altrui = 403), finance/invoice e audit; nessuna mutazione. `security.desk_boundary_acceptance.run` **PASS** sui sette ruoli e mantiene Administrator separato. `infra/uat_runtime_health.py` **PASS** (nove servizi, web, WebSocket, worker, scheduler). `infra/uat_demo.py validate` **PASS** con hash semantico invariato `9e1a61146ce666e50f5bf78ccd9995989dbc302e9c2dc6f6942d370583a9c09a`. Python compilation, JavaScript syntax e `git diff --check`: PASS.

## Evidenze visive

Prima: [Home #124](../issue-124/screenshots/issue124-home.png) mostra due barre e molte card duplicative. Dopo: [Direzione](screenshots/issue75-m-desktop.png), [Segreteria](screenshots/issue75-s-desktop.png), [Professionista A](screenshots/issue75-a-desktop.png), [Professionista B](screenshots/issue75-b-desktop.png), [Professionista C](screenshots/issue75-c-desktop.png), [Finance](screenshots/issue75-f-desktop.png), [Commercialista](screenshots/issue75-t-desktop.png), [tablet](screenshots/issue75-m-tablet.png), [telefono](screenshots/issue75-a-phone.png), [Patient nativo](screenshots/issue75-m-native-patient.png), [Agenda](screenshots/issue75-six-agenda.png), [Finanza](screenshots/issue75-six-finanza.png), [Report](screenshots/issue75-six-report.png). Immagini da Chromium reale con soli dati sintetici.

Confronto visivo: una sidebar anziché due barre; navbar senza menu duplicato; Home 3 card anziché elenco completo; teal istituzionale e Tabler Icons coerenti; layout desktop e mobile senza overflow. Nessun asset illustrativo è necessario per questa navigazione applicativa.

## Accesso Owner e residui

Tunnel privato invariato: `ssh -N -L 8082:127.0.0.1:8082 empv26@179.198.222.100`; URL `http://127.0.0.1:8082/login`. Credenziali demo nel file privato 0600 `/home/empv26/.local/state/centrochange-single/demo-owner.json`, trasferibile via SCP; `users.m` per Direzione. Nessun segreto in GitHub. DEV persistente, senza scadenza automatica.

Residui precisi per la final UI/UX #75: le List/Form native mostrano ancora identificativi sintetici `CC-HTTP-UAT...` e alcune etichette tecniche/inglesi; i breadcrumb preesistenti di Finanza/Report sono densi; alcuni link di catalogo aprono le superfici tecniche native già permesse, in attesa della decisione visuale Owner sulla loro collocazione. La suite generale `infra/security_acceptance.py` resta non idempotente sul seed persistente (#124); il test HTTP read-only qui copre i limiti richiesti per la revisione di navigazione. Il crash Chromium osservato in un primo smoke dopo una settima navigazione con QA da 512 MiB non si è ripetuto nei due test finali; nessun crash dei servizi applicativi.

**`READY_FOR_OWNER_UAT` e final GOAL-02 acceptance non sono dichiarati.** Serve review visiva Owner e chiusura/rinvio esplicito dei residui #75. Nessuna attività GOAL-03.
