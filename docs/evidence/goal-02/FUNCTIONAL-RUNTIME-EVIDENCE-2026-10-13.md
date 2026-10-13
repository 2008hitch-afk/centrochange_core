# GOAL-02 — collaudo funzionale dell'unico DEV

**Esito: `GOAL-02: FUNCTIONAL_RUNTIME_EVIDENCE_READY` — PASS tecnico nel perimetro sotto.** Non è `GOAL-02 OWNER PASS`: gli UAT Owner delle issue aperte e la review visiva #75 restano distinti. Nessun merge, GOAL-03, Missione C o dato reale.

## Runtime e deploy effettivo

- Target verificato: un solo progetto Docker `centrochange-dev`, nove servizi, Site `centrochange.local`, unico DB applicativo del Site, quattro volumi esistenti. Frappe/ERPNext 16.50.0, Healthcare 16.6.1, Builder 1.35.1. Nessun nuovo Site, DB o laboratorio.
- HEAD prima della mutazione: PR #127 DRAFT `d1892e038d0fc83ad0e4454742835099b064c4e7`; PR #126 DRAFT `dbb02b389e83f2cff0b05dde2689793797fe3e6f`. #125 e #112 restavano DRAFT. Working tree pulito; nessuna HEAD concorrente osservata.
- Sei servizi applicativi preesistenti usavano `sha256:b60c11e382127a47ce8638953334c1684dba25807a9b60a5363bcd67cce77171`. Il file `security/dev_acceptance.py` dentro il backend aveva SHA-256 `30413214c48a40c81bc8b324fa9cb9bf2fa8f9a14719283647c74dedaee23057`, identico al parent di #127. `scheduling/public_booking.py` coincideva byte per byte con il repository. Compatibilità del delta confermata prima del deploy.
- `infra/Dockerfile.goal02_fixture` deriva **solo** dall'immagine precedente e copia **solo** `security/dev_acceptance.py`; `infra/security_acceptance.py` viene eseguito dal checkout host, senza patch manuale nei container. Nessun asset, hook, schema, permesso o modulo contabile ricostruito. Build locale `--pull=false` sopra il digest verificato. Immagine distribuita ai soli sei servizi app: `centrochange-single:goal02-fixture-d1892e0`, ID `sha256:f38215267771e4db2e42af9312211931dc039b07ff17b69953c10f50026c6285`. Il file distribuito ha SHA-256 `a8314e3659fa24b60a6177d76309fbe35294d762285802d311fe46da67306112`, identico al file versionato.
- Commit del delta applicativo: `d1892e0` (#127); ricetta immagine `fcf6992`. Il codice applicativo restante è quello dell'immagine precedente PR #126 `dbb02b3`; non è stato distribuito un nuovo build della catena DRAFT. Compose ha ricreato solo backend, frontend, websocket, due worker e scheduler con `--no-build --no-deps`; DB e Redis sono rimasti attivi. `CC_UAT_IMAGE` privato aggiornato atomicamente, permessi `0600`.

## Dati sintetici prima e dopo

| Doctype / risorsa | Prima | Dopo |
|---|---:|---:|
| Patient | 8 | 8 |
| Patient Appointment | 10 | 10 |
| Sales Invoice | 4 | 4 |
| Purchase Invoice | 1 | 1 |
| Payment Entry | 2 | 2 |
| Bank Transaction | 2 | 2 |
| CC Fiscal Transaction | 3 | 3 |
| CC Public Booking Route | 1 | 1 |

Prima e dopo: `infra/uat_demo.py validate` PASS, 8 controlli, hash semantico identico `9e1a61146ce666e50f5bf78ccd9995989dbc302e9c2dc6f6942d370583a9c09a`. La sola route persistente è sempre `Marco`, abilitata e associata al centro demo originario. Il fixture ha quindi usato l'alias libero `Francesca` e lo ha eliminato durante il cleanup; nessuna route preesistente è stata sovrascritta. Ogni suite HTTP mutativa ha restituito `cleanup: PASS`; il runner backend usa rollback e verifica hash dei record canonici prima/dopo.

## Test realmente eseguiti

| Suite | Risultato | Copertura discriminante |
|---|---|---|
| `infra/security_acceptance.py --with-booking --with-operations` | **PASS, 38 controlli; cleanup PASS** | REST/list/query/export, A/B/C, segreteria, note private, reassignment/offboarding, prenotazione concorrente, pacchetto, Guest primo incontro, replay, route disabilitata e non autorizzata. |
| `centrochange_core.scheduling.dev_acceptance.run` | **PASS, 42 controlli; rollback** | Disponibilità, collisione, snapshot prezzo/durata, booking e reschedule con replay, accesso professionista/centro. |
| `infra/finance_acceptance.py` | **PASS, 24 controlli; cleanup PASS** | Manager/Segreteria/Finance/Commercialista, sorgenti economiche, mapping idempotente e dinieghi clinici/contabili. |
| `infra/banking_acceptance.py` | **PASS, 16 controlli; cleanup PASS** | Incasso, movimento, suggerimenti, riconciliazione/reversal, scadenza, blocco, override autorizzato, audit e read-only Commercialista. |
| `infra/professional_acceptance.py` | **PASS, 18 controlli; cleanup PASS** | XML ricevuto, fattura fornitore, compensi/soglia, atteso-ricevuto, pagamenti, coda, permessi e revoca centro. |
| `infra/sdi_acceptance.py` | **PASS, 6 gruppi; cleanup PASS** | SdI solo simulato, worker reale, retry/limite, correzione, XML privato, ruoli/cross-center. Nessun invio esterno. |
| `infra/ts_acceptance.py` | **PASS, 8 gruppi; cleanup PASS** | TS solo simulato, input espliciti/opposizione, worker, retry, correzione, payload e permessi. Nessun invio esterno. |
| `infra/goal02_targeted_regression.py` | **PASS, 213 controlli dei moduli + 2 eventi audit + 7 dinieghi; rollback e hash record invariato** | Integrazione, conferma primo incontro, ricerca pazienti, matrice finale sette ruoli/Guest, Registro modifiche sui record del seed attuale. |
| `infra/uat_runtime_health.py` | **PASS** | HTTP/assets, WebSocket 101, due worker, job nuovi short/long terminati, scheduler abilitato, nove servizi. Non deduce l'esecuzione periodica dal solo stato scheduler. |

`infra/remediation_acceptance.py` storico **non** ha prodotto PASS complessivo: `security.audit_view_acceptance` cercava due eventi UAT-06 di RC22 assenti dal database ricostruito. Una prova del vecchio `scheduling.reopen_acceptance` cercava l'ID RC22 `HLC-APP-2026-00133`, assente dal seed nuovo. Sono precondizioni obsolete dei test, non errori osservati nelle funzioni audit/prenotazione. Il runner versionato mirato testa il Registro sul seed corrente; `scheduling.dev_acceptance` verifica lo spostamento ordinario. **Il caso specifico di seduta riaperta #78 resta per il nuovo UAT Owner**, senza attribuirgli un PASS retroattivo. Nessuna delle due prove fallite ha cambiato l'hash del dataset.

## Checklist Owner: verifica funzionale distinta dalla rifinitura UI

1. **#62 — Banca:** aprire un movimento riconciliato; controllare che documento, soggetto, Payment Entry e importo allocato restino leggibili dopo il match.
2. **#71 — Registro modifiche:** Direzione trova un evento noto con prima/dopo e motivo; gli altri ruoli non ottengono l'audit via UI o API diretta.
3. **#72 — TS simulato:** aprire versione originale e revisionata; verificare opposizione, eligibilità, importo, codice, stato e collegamento di correzione. Nessun invio reale.
4. **#73 — Primo incontro:** provare una prenotazione sintetica controllata; verificare conferma locale immediata, replay senza doppione e nessuna email reale.
5. **#74 — Ricerca pazienti:** cercare nome e UID esatto con ruoli autorizzati; A/B/C vedono soltanto i pazienti assegnati.
6. **#78 — Seduta riaperta:** su un caso sintetico concordato, verificare che Sposta funzioni solo dopo riapertura autorizzata, conservando snapshot e audit. È il caso storico non replicato sul nuovo seed.
7. **#79 e #81 — Selettori e fattura professionista:** scegliere paziente/professionista e snapshot attesi per nome/data/importo; controllare i riferimenti canonici e il mismatch senza creazione automatica di debito.
8. **#77 — Matrice ruoli:** rivedere sette profili, Guest e Administrator tecnico; ripetere almeno un accesso diretto negato per ruolo.

**Può attendere il pass UI/UX #75:** uniformità estetica, transizioni, densità e terminologia italiana #80, purché l'Owner confermi che le azioni contabili restano comprensibili per l'UAT funzionale. #63, #66 e #68 hanno già accettazione Owner e non vengono riaperte.

## Accesso e prossimo gate

DEV privato invariato: `ssh -N -L 8082:127.0.0.1:8082 empv26@179.198.222.100`, poi `http://127.0.0.1:8082/login`. Credenziali solo nel file Owner privato `/home/empv26/.local/state/centrochange-single/demo-owner.json`, non in GitHub. Ambiente persistente, nessuna scadenza automatica; tunnel valido finché resta attiva la sessione SSH.

**Prossima decisione HITCH:** registrare l'esito degli UAT funzionali Owner sopra sul DEV corrente, inclusa la prova specifica #78; poi eseguire la review finale #75 e decidere formalmente l'accettazione GOAL-02. Nessun difetto funzionale di prodotto nuovo è stato dimostrato da questi test. Le vecchie suite vincolate a record RC22 vanno riallineate prima di riutilizzarle come gate generale. Nessun merge, GOAL-03, produzione o traffico reale è implicito nel presente PASS tecnico.
