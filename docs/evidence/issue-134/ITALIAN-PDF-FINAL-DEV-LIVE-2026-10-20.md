# Issue #134 — installazione finale italiano/PDF, collaudo DEV

**Esito: DEV aggiornato; PDF funzionale PASS; localizzazione PARTIAL.** Non è stata eseguita una seconda installazione. La valutazione visiva Owner e l'accettazione cliente restano aperte.

## Installazione autorizzata

- Autorizzazione Owner: PR #145, commento `6292032024`.
- PR DRAFT HEAD approvata al gate: `0f5b7bdd474aa760447b54abc76835df666f0c9a`; source applicativo `1b7ffc465ff699de163f9536ab04d4dde4da54e3`.
- Executor `infra/issue134_final_install.py` SHA-256 `e361d77e8a29e6040726c746be0533bbf387611940fb05c104e0acf2af204676`; overlay e template corrispondevano ai digest autorizzati. Dry-run immediato: `DRY_RUN_PASS`, nove servizi, fingerprint `82dc3825e195bbcd9300f0a6787c043b9f105db324752f06ea3aae23afec7ecd`.
- Gate privato avviato `2026-10-20T13:36:22Z`; scadenza operativa `17:36:22Z`, recupero `18:36:22Z`. Checkpoint privato `issue134-final-install-runs/20261020T133631Z-63248` con quattro backup cifrati e hash verificati. Nessun segreto o dump è stato copiato nel repository.
- Immagine precedente `sha256:a681d9a22a8198cec60469564e4a3c919a1318d824a16e53010b33d4879719d5`; immagine installata `sha256:d7315cb85d3d51ed6510b9d0f6f1b9b2be639cb2d637f67a57790136f5e55257`. Executor: `DEV_UPDATED_WITH_GAPS`, `failure=null`, `rollback_failure=null`; nessun rollback. Nove servizi attivi. Frontend pubblica solo `127.0.0.1:8082` sull'host; Nginx `-t` PASS. Socket.IO: Origin canonico 200, Origin estraneo 403.

## Prove live

| Verifica | Esito | Evidenza |
|---|---|---|
| PDF Frappe della fattura sintetica contabilizzata | **PASS funzionale** | Account Finance; `download_pdf?language=it` HTTP 200, `application/pdf`, firma `%PDF-`, 19.217 byte, 1 pagina, 503 caratteri estraibili, risorse CSS applicate; SHA-256 privato `72272faee9ab27f75d0ca5b636bc938694fd90f14f713958b72ebfa55d83550f`. Nessun errore `wkhtmltopdf`. |
| Autorizzazione stampa | **PASS** | Direzione, Finance, Commercialista: HTTP 200; Guest e Professionista: HTTP 403. Nessun bypass. |
| Testo principale fattura | **PARTIAL** | Nel PDF: «Fattura paziente», «Intestatario», «Subtotale», «Totale», `29/09/2026`, «Cento euro e zero centesimi». Nel titolo della scheda resta «Sales Invoice»; nel corpo restano `Session`, `Nos`, `Italy` e un codice dimostrativo dominante. |
| Form nativi | **22/22 aperture PASS** | 11 Form desktop/mobile, 0 errori JS, 0 match delle 46 stringhe mirate; screenshot sintetici [Paziente](live-final/patient-desktop.png), [Professionista mobile](live-final/practitioner-mobile.png). |
| Navigazione multiruolo | **128/128 PASS** | Sette ruoli, desktop/mobile, 0 errori JS e 0 etichette del vocabolario inglese mirato nelle superfici controllate. |
| `Last Edited By {0}` | **PASS nel secondo sweep mirato** | 11 Form, 0 corrispondenze `Last Edited By`, `Created By`, `Edited By`, `Assigned To`; catalogo versione installata coerente. |
| Orari 24 ore | **PARTIAL** | Nessun AM/PM nel sweep; il campo nativo di sola lettura `posting_time` di Purchase Invoice mostra ancora `11:05:49`. La preferenza boot `HH:mm` non formatta quel controllo nativo. |
| Agenda | **PASS invariata** | Screenshot desktop/mobile post-installazione identici byte per byte alla baseline approvata: desktop SHA-256 `02f69ccc4c4ad0c7c6509e52a542dc811275c52258e2d32fb2ac7820b405f40e`, mobile `d73f959fa1cd431da1b56507ca99b5af6d55d999c0cb04c865f349082da7357a`. Due righe professionisti, sette colonne giorno, una voce attiva. |
| Integrità | **PASS** | Fingerprint dati Owner/Communication, schema e permessi identici prima/dopo anche dopo le letture PDF e browser. Centro A attivo, Centro B inattivo. |

La prova PDF ha usato il percorso Frappe reale e il documento sintetico già presente; non ha creato o modificato fatture. Gli screenshot della stampa sono in [invoice-print.png](live-final/invoice-print.png). Le evidenze JSON complete e il PDF restano nello stato privato del server, fuori Git.

## Causa dei residui e correzione locale preparata

L'invoice print builder di ERPNext 16.50 rende i nomi dei servizi in `.cell-line--primary` e `.ql-snow`, non nelle celle `td[data-fieldname="item_name"]` coperte dal candidato installato. Il titolo browser proviene da `www/printview.py` e `www/printview.html` pinned. Per questi casi è pronta una correzione circoscritta in `website_brand.py`: traduzione presentazionale dei soli valori demo sintetici, `Nos` e `Italy`, più il titolo della fattura; sette test offline PASS nella versione pinned. Nessun valore canonico, ruolo, documento o saldo viene cambiato. Il test Chromium documentale ora riconosce `Subtotal` come parola intera: prima classificava erroneamente «Subtotale» come inglese.

**Questa correzione locale NON è installata.** Il singolo aggiornamento autorizzato è stato consumato. Un eventuale nuovo deploy richiede un gate Owner distinto. Anche `posting_time` con secondi e la validazione interattiva degli errori/formati restano da verificare/correggere; non sono dichiarati PASS.

## Stato demo e limiti

- MVP 46/46 PASS: evidenza storica documentata; non rieseguita in questo intervento.
- Percorsi demo: i 12 scenari restano coperti dal runbook/evidenze precedenti; **non** sono stati ripercorsi funzionalmente oggi. Nuove prove mirate: stampa/PDF, 22 Form e 128 navigazioni.
- Suite finanziaria mutativa e 38 controlli mutativi di sicurezza: `BLOCKED` dall'executor in questa installazione di localizzazione; i controlli essenziali read-only e i permessi di stampa hanno passato. Non trasformati in PASS.
- `CLIENT_DEMO_READY_FOR_OWNER_REVIEW = NO` per i residui visibili nella stampa fattura e l'orario con secondi. Il DEV resta aggiornato, accessibile tramite tunnel privato e integro.
