# Issue #75 — Native-first UI pronta per nuova review Owner

**Esito tecnico:** `CENTROCHANGE_NATIVE_FIRST_UI_READY_FOR_OWNER_REVIEW`. Non equivale a `OWNER VISUAL PASS` né alla chiusura di GOAL-02. La precedente review Owner della PR #126 resta **NOT ACCEPTED — CORRECTION REQUIRED** fino alla nuova verifica.

## Perimetro e versione servita

- Unico progetto operativo: `centrochange-dev`; un Bench, Site `centrochange.local` e database applicativo `_4f614b4543aa5230`. Nove servizi del progetto attivi, inclusi i sei servizi applicativi con la medesima immagine.
- Base single-stack issue #124; Frappe/ERPNext `16.50.0`, Healthcare `16.6.1`, Builder `1.35.1`. Codice applicativo sulla PR DRAFT #126, derivata dalla PR #125. Nessun merge.
- Immagine effettivamente servita: `sha256:123adc6f65217b449942f158a63e9541bf1228d4e4047fc33d67e74f3e1297a5` (`centrochange-single:issue75-native-first`). Dockerfile versionato: `infra/Dockerfile.issue75`.
- Il Site esistente è stato migrato per applicare un unico Property Setter presentazionale; non è stato ripristinato, resettato o ripopolato. Hash semantico dei dati demo invariato: `9e1a61146ce666e50f5bf78ccd9995989dbc302e9c2dc6f6942d370583a9c09a`.

## Scelta tecnica e modifiche

La [matrice delle schermate](../../ui/ISSUE-75-NATIVE-FIRST-SCREEN-MATRIX-2026-10-12.md) classifica 18 aree come `NATIVE_CUSTOMIZE`, `NATIVE_WITH_CLIENT_PRESENTATION` o `DEDICATED_FRAPPE_PAGE`, con motivazione, riuso e manutenzione. Sono stati riutilizzati il Desk Frappe, le List/Form native, le Page operative Centro Change, le API e i controlli server esistenti.

1. Shell cliente circoscritta: sidebar unica per ruolo attraverso Page e List/Form di moduli diversi, navbar essenziale, senza barra duplicata. La navigazione ordinaria usa `page-change`; l'observer controlla solo la sostituzione del figlio diretto del `body`. Collasso volontario senza persistenza indesiderata. L'Administrator tecnico mantiene il Desk Frappe nativo.
2. Nelle viste native, `doctype_list_js`, `doctype_js`, traduzioni e un Property Setter puntuale sostituiscono la riscrittura globale dei testi nel DOM. Pazienti, professionisti, catalogo, tariffe, fatture e movimenti bancari mostrano nomi umani dove supportati; i valori canonici restano nei documenti.
3. La Home è stata ridotta ad azioni frequenti e conteggi ricavati dalle API autorizzate già presenti. Le tre azioni di Ricerca pazienti sono compatte e conservano i callback originali. Il Registro modifiche usa la vista dedicata, sola lettura, già implementata.
4. Il filtro standard `Healthcare Practitioner.department` provocava una richiesta a `Medical Department` respinta per il Manager. Il filtro non necessario è disabilitato tramite patch idempotente; il campo Link e la policy restano. Il test diretto dell'API conferma ancora HTTP 403. Nel form cliente, il Link vuoto è nascosto; il form tecnico Administrator resta integro.
5. Tabler Core non è caricato nella shell Desk cliente. I file vendorizzati restano perché il website/login esistente li usa; le Tabler Icons locali restano icone. Nessun framework o permesso nuovo.

## Collaudo sulla versione distribuita

| Verifica | Risultato |
|---|---|
| Browser Chromium: Home → Agenda → Ricerca pazienti → Anagrafica pazienti → Professionisti → Catalogo → Finanza → Report → Registro → Home; avanti/indietro, refresh, errori JS, geometria e brand | PASS |
| Sette account `m,s,a,b,c,f,t`, desktop 1440 px, tablet 768 px, smartphone 390 px; menu per ruolo e navigazione | PASS |
| Nove liste native, form Patient, layout tablet/telefono | PASS |
| Form Practitioner e filtro Medical Department; Administrator separato | PASS |
| API dirette per sette ruoli, assegnazioni pazienti `6/1/0`, divieti e Medical Department HTTP 403 | PASS |
| Runtime: nove servizi, frontend, WebSocket, due worker e scheduler | PASS |
| Dati demo: hash semantico invariato; quattro test generazione frammenti Desk | PASS |

Script riproducibili: `infra/browser/issue75_native_first.cjs`, `issue75_native_roles.cjs`, `issue75_native_surfaces_v2.cjs`, `issue75_medical_department.cjs`, `issue75_admin_boundary.cjs`, `infra/issue75_role_api.py`, `infra/uat_runtime_health.py`, `infra/uat_demo.py`, `infra/test_c109_desk_fragments.py`. Chromium è stato eseguito nel container QA limitato a 512 MiB; i test HTTP sono stati eseguiti contro il DEV distribuito. I dati demo non sono stati mutati.

## Evidenze visive reali

Le immagini in [`native-first-screenshots/`](native-first-screenshots/) provengono da sessioni Chromium effettive sull'immagine sopra. Contengono il percorso completo, nove liste native, form, sette ruoli desktop, tablet e telefono. [`issue75-native-first-visual.json`](native-first-screenshots/issue75-native-first-visual.json) registra misure geometriche, presenza della sidebar, overflow e rilevamento del branding durante la navigazione. Confronto di riferimento: `TABLER-NAVIGATION-OWNER-REVIEW-2026-10-12.md` e commenti Owner della issue #75.

## Difetti e limiti ancora aperti

- Alcuni valori canonici sintetici e testi nativi upstream restano nei campi editabili o nelle viste tecniche, per esempio il sesso `Female` nel form Patient e metadati Frappe. I formatter presentano il nome umano nelle liste, ma non riscrivono i dati salvati.
- La Home usa solo i conteggi già disponibili; eventuali KPI aggiuntivi richiedono una decisione separata sui servizi backend.
- La review visiva finale dell'Owner è necessaria. Nessun `OWNER VISUAL PASS` è dichiarato.

## Accesso Owner

Sul computer dell'Owner: `ssh -N -L 8082:127.0.0.1:8082 empv26@179.198.222.100`, poi aprire `http://127.0.0.1:8082/login`. L'account demo Direzione è `m`; le credenziali restano fuori Git nel file privato del server `/home/empv26/.local/state/centrochange-single/demo-owner.json` (permessi 0600), da condividere tramite canale sicuro. Ambiente DEV persistente, senza scadenza automatica.
