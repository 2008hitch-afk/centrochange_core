# Missione C #109 — r8, validazione UI finale interrotta

**Esito:** `MISSION-C: PARTIAL`; `READY_FOR_OWNER_UAT: NO`. Una sola attivazione r8, autorizzata dall'Owner e [registrata prima della mutazione Docker](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6112402837). Finestra 2026-10-11 18:44:16–2026-10-12 00:44:16 UTC, hard stop 01:44:16 UTC. Arresto anticipato alle 18:51 UTC dopo un test funzionale non riuscito; nessun riavvio o secondo tentativo.

## Identità e sicurezza

- Codice prodotto e harness testati: `0c96104673bfb437c9fd5350a386a4da2874f52d`, PR DRAFT #112 stacked sulla PR DRAFT #107. Immagine OCI COPY finale `sha256:6443a1139dca9456b7464844b32a42a79d028b80afe4ba704dd9abf6c56684dd`; label revisione, backend/frontend e hash HTTP dei due asset client corrispondono alla revisione. La copia OCI ha superato il confronto byte per byte dei file applicativi modificati.
- Progetto esclusivo `centrochange-c109-gated-r8`: otto servizi rilasciati in sequenza dopo verifica HostConfig/cgroup; 2 GiB aggregati, swap zero. QA 512 MiB, swap zero, un browser Chromium alla volta. Il watchdog registrava PSI I/O senza arresto sul solo indicatore temporaneamente derogato; RAM, OOM, cgroup, disco, eventi protetti, scadenza e monitor indipendente RC22 erano attivi.
- RC22 prima/dopo: **nove ID identici, HTTP 200**, 179 campioni indipendenti senza alert, latenza massima 0,177 s. Watchdog: 75 campioni, PSI I/O full massimo 1,64%, PSI memoria full massimo 0%, MemAvailable minimo 4,77 GB, OOM host 7→7. Nessun safety stop. Disco finale libero 46,52 GB. R8 e QA: **zero container running**; `monitor-finish` presente, scope terminati, deroga non persistente. Volumi, immagini e fixture sintetiche conservati.

## Prove effettive sulla build r8

- Static/offline: 57 test harness PASS, shell simulata per sette profili PASS, JavaScript syntax e diff check PASS. Compose statico: otto servizi, 2 GiB/swap zero, nessun limite artificiale r6 e sole reti/volumi C109.
- Browser reale: Lista Patient nativa come Direzione → titolo **Pazienti · Centro Change**, menu cliente, asset Desk caricato, zero JS error, zero document overflow; la sidebar tecnica Frappe non è visibile. Agenda Segreteria: Centro A, 28/09–04/10, sette intestazioni, due professionisti, nove sedute, dettaglio Seduta/Storico/Note e dialog Prenota; zero error/overflow. Professionisti A/B/C: rispettivamente 8/1/0 sedute; A/B disgiunti nel fixture. La Direzione era preimpostata su Centro B (0 sedute nella settimana), quindi il conteggio vuoto non è stato trattato come difetto. [Screenshot Agenda sintetica della build r8](r8/agenda-desktop-synthetic.png).
- Backend: `operations.integration_acceptance.run` **189 PASS**, fixture con rollback; `security.desk_boundary_acceptance.run` PASS; `finance.dev_acceptance`, `receivables`, `banking`, `incoming`, `professional`, `reporting`, `sdi` e `ts` hanno restituito **PASS** con rollback. Sono prove sulla stessa immagine r8, ma non sostituiscono i workflow browser o le verifiche dirette per ogni ruolo.
- `finance.patient_report_acceptance.run` **FAIL**: la precondizione `theta['totals']['outstanding'] > 0` non era soddisfatta nel dataset sintetico C109. L'asserzione avviene prima del savepoint mutativo del test. Il successivo `NameError` nel log è il fallback di `bench execute` dopo l'`AssertionError`, non la causa primaria. Non è dimostrato se il debito manchi nel fixture, se vi sia deriva dei dati C109 o un difetto della proiezione; serve una lettura canonica read-only nella prossima finestra autorizzata. `professional_view_acceptance` non è stato eseguito.

Il wrapper r8 `c109_monitored_step.py` arrestava C109 anche per un exit code di test diverso da zero, pur senza evento di sicurezza. Questo ha consumato la singola attivazione r8 prima degli altri test. Non è stato aggirato il comportamento fail-closed né riavviato il laboratorio. **Dopo l'arresto**, un delta solo offline introduce `--test` limitato a `docker exec` del progetto attivo: ricontrolla tutti i guard dopo il processo e registra il FAIL senza arrestare il laboratorio soltanto se i guard restano GREEN. Ogni evento di sicurezza, timeout o comando ordinario continua ad arrestare C109. Tre nuovi test positivi/negativi e la suite harness complessiva **60/60 PASS**. Il delta non è stato usato durante r8 e richiede prova runtime nella prossima attivazione.

## Matrice GOAL-02 sulla build r8

`PARTIAL` significa che una parte della funzione è stata provata sulla build r8; `NOT TESTED` non eredita i PASS r7.

| # | Area | Esito r8 | Prova e limite |
| --- | --- | --- | --- |
| 1 | Agenda | PARTIAL | Griglia e 7 giorni Segreteria/A/B, screenshot; resize/mobile non eseguiti |
| 2 | Prenota/sposta/cancella | PARTIAL | Servizi nei 189 backend, dialog Prenota aperto; submit browser non eseguito |
| 3 | Seduta/storico/note | PARTIAL | Tre tab browser e guard backend; salvataggi browser non eseguiti |
| 4 | Pazienti | PARTIAL | List nativa Direzione e titolo italiano; Form/direct/export non eseguiti |
| 5 | Professionisti | PARTIAL | Agenda A/B/C; List/Form nativa non eseguita |
| 6 | Disponibilità | PARTIAL | Suite 189 backend; editor browser non eseguito |
| 7 | Catalogo/prezzi/pacchetti | PARTIAL | Suite 189 backend; List/Form browser non eseguite |
| 8 | Contabilità/registri | PARTIAL | Finance backend PASS; List/Form browser non eseguite |
| 9 | Fatture | PARTIAL | Receivables backend PASS; UI/print non eseguiti |
| 10 | Incassi/pagamenti | PARTIAL | Finance/backend PASS; UI non eseguita |
| 11 | Banca/riconciliazione | PARTIAL | Banking backend PASS; UI non eseguita |
| 12 | Report Centro/Professionisti/Pazienti | PARTIAL | Reporting backend PASS; Patient Report acceptance FAIL sul fixture Theta |
| 13 | Report ERPNext generici | NOT TESTED | Negative direct/export non eseguiti r8 |
| 14 | SdI simulato | PARTIAL | Suite backend PASS, nessun provider; UI non eseguita |
| 15 | TS simulato | PARTIAL | Suite backend PASS, nessun provider; UI non eseguita |
| 16 | Audit | PARTIAL | Boundary/backend, UI/export non eseguiti |
| 17 | Accessi/centri | PARTIAL | Boundary Desk PASS; direct/API per tutti i ruoli non completi |
| 18 | Compensi | PARTIAL | Professional backend PASS; UI non eseguita |
| 19 | Notifiche/job | PARTIAL | Suite 189 backend; UI/worker dedicati non eseguiti |
| 20 | Login/logout | PARTIAL | Login m/s/a/b/c; Finance/Accountant/logout/Guest non eseguiti |
| 21 | Primo incontro pubblico | NOT TESTED | Guest flow non eseguito |
| 22 | Stampa/export | PARTIAL | Guard backend integrati; output browser non eseguiti |
| 23 | Validazione DEV | NOT TESTED | Superficie tecnica fuori navigazione cliente; esclusione da verificare |
| 24 | Identità e confronto C3 | PARTIAL | Menu/titoli e geometria desktop migliorati; mobile, native Form e confronto funzionale RC22 non completati |

## Passo necessario

Prima di un'eventuale nuova attivazione: accertare la precondizione sintetica del test Theta e, se necessario, preparare un caso reversibile indipendente dalla deriva del fixture. Alla prossima finestra autorizzata, leggere la fonte ERPNext e `patient_view` per Theta prima di proseguire. Il collaudo restante (sette ruoli più Guest/Administrator, native List/Form, mobile, booking UI, API/direct/query/export/print, C3) richiede una nuova autorizzazione operativa; nessun merge, cutover o cambio di UI primaria è giustificato da r8.
