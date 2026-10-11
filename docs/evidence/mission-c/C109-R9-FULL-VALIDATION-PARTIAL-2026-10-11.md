# Missione C #109 — collaudo isolato r9

**Esito:** `MISSION-C: PARTIAL`; `READY_FOR_OWNER_UAT: NO`. Una sola attivazione r9, [registrata prima della mutazione](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6112643758). Nessun safety stop e nessun secondo avvio. PR #112 resta DRAFT; RC22 resta la UI primaria.

## Identità, fixture e protezioni

- Prodotto realmente collaudato: commit `0c96104673bfb437c9fd5350a386a4da2874f52d`, immagine OCI `sha256:6443a1139dca9456b7464844b32a42a79d028b80afe4ba704dd9abf6c56684dd`. Harness r9 da `b440b7e`, 62/62 test offline PASS. PR #107 resta dipendenza DRAFT.
- Progetto esclusivo `centrochange-c109-gated-r9`, site sintetico `b99.local`, porta locale 8109; volumi/rete solo C109 già esistenti. Otto servizi con 2 GiB aggregati, swap zero; QA 512 MiB, swap zero. Rilascio sequenziale dopo controllo HostConfig e cgroup. Deroga temporanea limitata allo **stop PSI I/O**; telemetria I/O continua, monitor RC22 indipendente e watchdog/guard memoria, OOM, disco, scadenza ed eventi protetti attivi.
- Finestra 2026-10-11 19:10:04–2026-10-12 01:10:04 UTC; hard stop 02:10:04 UTC. Arresto anticipato e mirato dopo le prove. RC22: nove ID identici prima/dopo, HTTP 200; 446 campioni indipendenti, zero alert, latenza massima 0,188 s. Watchdog: 186 campioni, PSI I/O full massimo 0,72%, PSI memoria full massimo 0%, MemAvailable minimo 4,56 GB, OOM host 7→7. C109/QA: zero container running; deroga terminata. Disco libero finale 46,46 GB.
- I log grezzi e le credenziali restano privati fuori Git in `/home/empv26/.local/state/centrochange-c109-final-r9-20261011/`. Qui sono conservati solo risultati sanitizzati e screenshot sintetici.

## Theta e qualità del fixture

Lettura iniziale **read-only**: la Sales Invoice sintetica Theta era submitted, EUR 100, outstanding **0**, status Paid; un Payment Entry submitted da EUR 100, associato a Bank Transaction sintetica del 9 ottobre, la saldava. `patient_view` come Segreteria via HTTP restituiva coerentemente fatturato 100, incassato 100, residuo 0. Il FAIL r8 `outstanding > 0` era quindi **deriva del fixture C109**, non un'incoerenza della proiezione.

Solo in C109, dopo verifica dell'esatta catena Bank Transaction → Payment Entry → Sales Invoice, il ruolo Direzione ha usato il servizio versionato `finance.banking.cancel` con motivo sintetico esplicito. Il movimento e il Payment Entry sono conservati come annullati, con audit `BANK_MOVEMENT_CANCELLED`; la fattura resta submitted, outstanding EUR 100, status Overdue. `patient_view` restituisce fatturato 100, incassato 0, residuo/scaduto 100, una fattura aperta. `finance.patient_report_acceptance.run` e `finance.professional_view_acceptance.run` **PASS**, con rollback dei loro probe. Nessun dato RC22 è stato toccato. Il ripristino funzionale del movimento, se mai richiesto, richiede un nuovo movimento sintetico tracciato tramite servizio; non si riscrive l'evento annullato.

La validazione globale `uat.demo.validate` resta **FAIL per un'altra deriva preesistente**: la fattura etichettata nel manifesto come “Alfa bozza” è ora submitted/paid, mentre il manifesto la richiede draft. Il test `audit_view_acceptance` richiede due eventi Owner di RC22 assenti dal clone C109; `expectation_ui_acceptance` richiede una seduta con ID RC22 non presente in C109. Questi ultimi due test sono **fixture-specifici, non portabili**; non sono stati conteggiati come PASS o come difetti prodotto. Nessuna assertion è stata indebolita.

## Risultati discriminanti sulla build r9

- Browser reale, un Chromium alla volta: shell Centro Change e menu per **m/s/f/t/a/b/c**, List native Patient/Practitioner/Item/Audit e Form native Patient/Practitioner/Sales Invoice/Payment Entry; nessun errore JS o overflow nei percorsi provati. Agenda 7 giorni, 9 sedute Segreteria, A 8, B 1, C 0 nel periodo 28/09–04/10. Dettaglio Seduta/Storico/Note e dialog Prenota aprono. Prenotazione Alfa negata correttamente dal blocco economico; scenario positivo con Gamma: **prenota → sposta → cancella** via browser PASS, con record canonico sintetico. Mobile Agenda senza document overflow.
- Finance: nove viste Riepilogo, Fatture pazienti, XML ricevuti, Fatture fornitori, Banca, Professionisti, Coda amministrativa, SdI e TS renderizzate con righe/dati coerenti e nessun errore JS; desktop/mobile senza overflow. Questo prova lettura/navigazione, non i salvataggi Finance via browser.
- Report browser: Theta 28/09–31/10 mostra una fattura emessa, aperta e scaduta; drill-down fatturato contiene un record. Professional View Alfa: “Sedute: 10 record” coincide con 10 righe; periodo visibile. Backend Patient/Professional acceptance PASS. `security.final_review_acceptance`, `desk_boundary_acceptance`, ricerca scoped e gate privato UAT PASS.
- HTTP diretto: Guest, sette ruoli, Builder, Patient, Sales Invoice, private note, Patient View/export, centro estraneo, reportview/query e print. Builder 403 per ogni ruolo cliente; A può leggere il proprio Patient/private note e non quelli di B; B vede soltanto Zeta; C senza associazioni riceve 403. Professionisti non accedono a fatture/report economici. Finance/Accountant non accedono a Patient clinico; Direzione/Segreteria accedono secondo policy. Guest nega API interne; login/logout 200 e post-logout Finance 403. `primo_incontro` Guest 200; 404 corretto. Audit r9 visibile alla sola Direzione (1 evento di annullamento riconciliato), 403 agli altri.
- Asset, backend, frontend, websocket, worker, scheduler, MariaDB e Redis attivi durante il test; ping e asset Desk 200. Le 189 prove backend, otto suite Finance/fiscali e sei hook r8 restano evidenze **della stessa immagine immutabile**, ma non sono spacciate per riesecuzioni r9.

## Matrice finale delle 24 aree sulla build effettivamente provata

| # | Area | Esito r9 | Evidenza / gap |
| --- | --- | --- | --- |
| 1 | Agenda | PARTIAL | Browser A/B/C/Segreteria, 7 giorni e mobile; geometria misurata in r8 sulla stessa immagine, non rimisurata in r9 |
| 2 | Prenota/sposta/cancella | PASS | Browser Gamma, tre POST canonici e record conservato; Alfa bloccata correttamente |
| 3 | Seduta/storico/note | PARTIAL | Tab browser e guard backend; salvataggio note browser non eseguito |
| 4 | Pazienti | PARTIAL | List/Form native e API scoped; Form ha etichette inglesi visibili |
| 5 | Professionisti | PARTIAL | Form nativa e separazione A/B/C; traduzione completa da verificare |
| 6 | Disponibilità | PARTIAL | Servizio nella suite backend r8; modifica browser non eseguita r9 |
| 7 | Catalogo/tariffe/pacchetti | PARTIAL | List Item nativa e backend r8; Form/prezzi/pacchetti browser non completi |
| 8 | Contabilità/registri | PARTIAL | Native Form/Finance e guard; etichette tecniche nella Form |
| 9 | Fatture | PARTIAL | Native Sales Invoice, browser lettura, suite r8; form cliente non conforme |
| 10 | Incassi/pagamenti | PARTIAL | Payment Entry Form e suite r8; creazione browser non eseguita |
| 11 | Banca/riconciliazione | PARTIAL | Vista Banca con record e suite r8; riconciliazione browser non eseguita |
| 12 | Report Centro/Professionisti/Pazienti | PASS | Browser Centro/Patient/Professional, KPI e drill-down; acceptance backend r9 PASS |
| 13 | Report ERPNext generici | PARTIAL | Builder/query 403; generici contabili completi non collaudati |
| 14 | SdI simulato | PARTIAL | Vista con record e suite r8 PASS; tentativo browser non eseguito r9 |
| 15 | TS simulato | PARTIAL | Vista con record e suite r8 PASS; versione/correzione browser non eseguite r9 |
| 16 | Audit | PARTIAL | Evento r9 e 403 ruoli non manager; export/browser audit completo non eseguito |
| 17 | Accessi/centri | PASS | Final-review 7 ruoli + Guest, revoche in rollback, foreign-center negative HTTP |
| 18 | Compensi | PARTIAL | Professional View e suite r8; override browser non eseguito r9 |
| 19 | Notifiche/job | PARTIAL | Worker/scheduler attivi e backend r8; retry browser non eseguito r9 |
| 20 | Login/logout | PARTIAL | Sette login browser, Guest e logout HTTP; Administrator tecnico non collaudato nel browser r9 |
| 21 | Primo incontro pubblico | PARTIAL | Guest HTTP 200; invio form pubblico non eseguito r9 |
| 22 | Stampa/export | PARTIAL | HTTP positive/negative per print/export e query; download browser non eseguiti |
| 23 | Validazione DEV | NOT TESTED | Superficie tecnica esclusa dal menu cliente; esclusione browser non verificata r9 |
| 24 | Identità e confronto C3 | FAIL | Form native mostrano etichette inglesi e campi tecnici; confronto RC22 funzionale completo non concluso |

## Gap visivo e delta offline successivo

La [Form Patient](r9/native-patient-form-gap.png) mostra “Patient Demographics”, “Medical History” e “Middle Name”; la [Form Sales Invoice](r9/native-invoice-form-gap.png) mostra “Request Fingerprint”, “Idempotency Key” e un avviso in inglese. È un gap reale di conformità Centro Change. Una correzione **solo offline, non presente nell'immagine r9** aggiunge traduzioni italiane CSV supportate da Frappe e cela i due campi tecnici di richiesta solo nella presentazione dei ruoli cliente. Il server e i dati canonici restano invariati. La [documentazione ufficiale Frappe sulle traduzioni custom](https://docs.frappe.io/framework/user/en/guides/basics/translations) conferma l'uso di file CSV nell'app; la resa delle specifiche Form native richiede comunque una nuova build e prova browser. L'harness di copia OCI ora include il CSV. Static/syntax, CSV univoco e 62 test harness PASS. **Nessun PASS runtime è attribuito a questo delta offline.**

Screenshot aggiuntivi: [Agenda mobile](r9/agenda-workflow-mobile.png), [Finance desktop](r9/finance-desktop.png), [Finance mobile](r9/finance-mobile.png), [Patient Report](r9/patient-report.png). Sono sintetici. Nessun screenshot r9 contiene dati reali.

## Confronto C3 e decisione operativa

RC22 è rimasto sano e invariato; la sua baseline GOAL-02 e le prove r8 sulla stessa immagine guidano il confronto. R9 dimostra che Agenda e report principali funzionano nel Desk, ma la resa native Form è ancora meno uniforme dell'app RC22. Le credenziali del fixture C109 non sono valide in RC22 (401) e non sono state cercate o modificate credenziali RC22: **nessuna parità record-per-record o walkthrough RC22 è stata inventata**. C3 è PARTIAL. Le prove r9 non autorizzano Owner UAT finale, cutover o merge.

**Prossimo gate unico:** completare offline la conformità delle Form/List native e i workflow browser ancora PARTIAL, poi chiedere una nuova singola finestra isolata per verificare l'immagine con quel delta. Prima di tale finestra il fixture C109 va confrontato con il manifesto demo: “Alfa bozza” è un dato divergente e deve essere trattato con procedura sintetica tracciata, senza reset implicito né modifica di RC22.
