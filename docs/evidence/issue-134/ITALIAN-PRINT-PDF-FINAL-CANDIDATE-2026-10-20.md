# Issue #134 — candidato finale italiano e PDF

**Stato: READY_FOR_SINGLE_DEPLOY.** Nessuna modifica al DEV condiviso in questa fase. La generazione della fattura PDF reale resta **non verificata sul candidato installato** fino al singolo aggiornamento Owner.

## Baseline e candidato

| Elemento | Valore |
| --- | --- |
| Baseline DEV | source `0e6299d8a5507cc5d7dde46336870c0cd6667718`; immagine `sha256:a681d9a22a8198cec60469564e4a3c919a1318d824a16e53010b33d4879719d5` |
| Source applicativo candidato | `1b7ffc465ff699de163f9536ab04d4dde4da54e3` |
| Tag candidato | `centrochange-single:issue134-final-1b7ffc4` |
| Executor | `infra/issue134_final_install.py`; SHA-256 `e361d77e8a29e6040726c746be0533bbf387611940fb05c104e0acf2af204676` |
| Overlay | `infra/compose.issue134_final.yaml`; SHA-256 `e144cbc8005e6d6944059e0016efdcfb9de08b366f6db3877677a8ef9fb26c03`; sei servizi applicativi, nessun volume/port publishing aggiunto |
| Template | `infra/issue134_frontend_pdf.conf.template`; SHA-256 `04804a9674a97dbdca1a01003b39536030bb9d858447d5a0d32e4a19f8a4c116`; stesso proxy e controllo Origin del template #139 |

## Difetti, cause, correzioni

| Difetto | Causa dimostrata | Correzione | Prova |
| --- | --- | --- | --- |
| PDF fattura HTTP 500 | `wkhtmltopdf` nel backend richiede asset su `centrochange.local:80` e `:8082`; frontend Docker serviva solo la 8080. Il nome è già risolvibile; le due porte rifiutavano la connessione. | Stesso Nginx del frontend in ascolto anche su 80/8082 **solo nella rete Docker**; host publishing privato invariato. | `issue134_pdf_network_rehearsal.sh`: accesso CSS 80/8080/8082 e PDF `%PDF-` con wkhtmltopdf pinned: PASS. `nginx -t` con utente runtime: PASS. Il PDF Frappe reale richiede collaudo post-deploy. |
| `Last Edited By Administrator` | Frappe 16.50 usa `Last Edited By {0}`, non la sola chiave `Last Edited By`. | Chiavi parametrizzate esatte nel catalogo `it.csv`. | Catalogo CSV senza duplicati: PASS; verifica browser live dopo deploy. |
| Stampa fattura in inglese | Il print format attivo è **Sales Invoice Modern with Images**; contiene heading in Custom HTML e campi builder. Il precedente hook mirava a selettori di un altro formato. | Etichette localizzate nei soli nodi label/header/Custom HTML della stampa `Sales Invoice`; importo in lettere EUR ricalcolato solo per la presentazione con `num2words` già pinned; nessuna modifica all'importo salvato. | 5 test nel runtime Python pinned: PASS; formato attivo identificato con query read-only. |
| PDF non localizzato durante chiamata API | `get_print()` rende `printview` dentro la richiesta `/api/method/...`; la condizione precedente controllava solo il path HTTP `/printview`. | Hook guidato da `values.doctype`, mantenendo la permission validation nativa. Prova browser usa parametro Frappe 16.50 `language=it`. | Test API-context: PASS; prova reale post-deploy obbligatoria. |
| Orario `HH:mm:ss` nei Form nativi | `Language.it.time_format` è vuoto e `System Settings.time_format=HH:mm:ss`; Frappe `ControlTime` usa `bootinfo.sysdefaults.time_format`. | Hook nativo `boot_session` imposta `HH:mm` solo nei profili cliente, senza cambiare DB, API o Administrator. | Test ruoli cliente/Administrator: PASS; verifica Agenda screenshot e Form live dopo deploy. |

I file e i dati Agenda restano invariati. La stampa annullata che dà 403 continua a usare i permessi Frappe; nessun bypass di `validate_print_permission`.

## Verifiche eseguite senza mutare il DEV

- Preflight executor `--dry-run`: **PASS**, 9 servizi, 2 sedi, fingerprint Owner `82dc3825e195bbcd9300f0a6787c043b9f105db324752f06ea3aae23afec7ecd`.
- Build derivata dalla baseline con sole 3 modifiche applicative; Nginx template verificato nell'immagine isolata: **PASS**. Tag di controllo rimosso.
- Unit test installer/catalogo: **8/8 PASS**. Unit test stampa e ruoli in Python dell'immagine pinned: **5/5 PASS**.
- Rehearsal di rete isolata senza Site/DB/volumi condivisi: **PASS** per 80, 8080, 8082 e `wkhtmltopdf` reale. Un messaggio Fontconfig relativo alla cache non scrivibile non ha impedito il PDF; non è stato cambiato alcun permesso globale.
- Nessun asset, schema, dato contabile, permesso, guard di sicurezza o sorgente Agenda cambiato. Le 46 capability MVP sono evidenza precedente, non rieseguite.

## Singolo gate Owner e collaudo successivo

Occorre una **nuova autorizzazione specifica** per il candidato e lo SHA-256 finale dell'executor. Quella della precedente installazione #134 è consumata e il nuovo executor la rifiuta. Il gate privato richiede inizio UTC effettivo, fino a 4 ore operative e 1 ora di recupero. L'executor eredita preflight fail-closed, checkpoint, backup cifrato verificato, aggiornamento dei soli sei servizi, controlli di integrità e un rollback; l'immagine di prova non viene installata autonomamente.

Dopo l'installazione: verificare con Chromium Finance e Direzione una fattura contabilizzata autorizzata in `printview` e `download_pdf?language=it`; controllare intestazioni, importo in lettere, servizi, date e orari, risposta `%PDF-`, numero di pagine e testo estratto. Verificare diniego su documento non autorizzato, Form Finance/Commercialista e Administrator, 22 Form nativi desktop/mobile mirati, schermate cliente, e confronto Agenda desktop/mobile con la baseline #75. Confrontare prima/dopo fingerprint Owner, Communication, schema, permessi, guard e salute 9/9. Non segnare PDF PASS se il file reale non viene generato.

Nessun merge, GOAL-03, produzione o accesso pubblico al DEV.
