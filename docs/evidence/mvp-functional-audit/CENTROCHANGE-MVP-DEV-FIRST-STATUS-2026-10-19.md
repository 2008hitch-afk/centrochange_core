# CENTROCHANGE-MVP-DEV-FIRST-STATUS — 19 ottobre 2026

## Esito

**DEV_UPDATED_WITH_GAPS.** Il DEV condiviso conserva il candidato `a14ab5db70aadcff13bf7028dd06c7063f7ccdd9`, immagine `sha256:32b51999b850a119cb853b4b1b46f3f111d5b76407eb90bb2016e93bee182910`. I nove servizi sono attivi; database e Redis risultano healthy. Nessuna reinstallazione, migrazione, rollback o fixture mutativa è stata eseguita durante questa ripresa.

Il report privato dell'installazione `20261019T094449Z-2969968` registra `installation_essential_status: PASS`, `status: DEV_UPDATED_WITH_GAPS`, nessun failure e nessun rollback. Una verifica successiva in sola lettura conferma la stessa impronta dati del checkpoint (`caba48b14430cd975213fde6273aada780aecd6e6604ad4fbb5ccda8bfc4eae0`), gli stessi schemi, permessi, configurazione, overlay e sei hook di sicurezza. I sette screenshot dei ruoli demo sono conservati nella directory privata `browser-evidence/issue139-20261019T094449Z-2969968/readonly-resumed/` sotto lo state directory del single-stack.

## Conteggio MVP

L'audit originale delle 46 voci rimane **40 PASS / 6 PARTIAL**. I 40 PASS sono evidenze funzionali dell'audit precedente: questa ripresa non ha rieseguito ciascun processo né li presenta come 40 nuove certificazioni live. Nessuna delle sei voci residue raggiunge ancora un PASS funzionale completo. Pertanto il massimo conteggio supportato è **40/46 PASS storici; 0/6 lacune chiuse**. Una dichiarazione 46/46 sarebbe infondata.

| Voce | Esito attuale | Prova completata | Evidenza ancora necessaria |
|---|---|---|---|
| CC-CAP-029 — italiano/export | PARTIAL | CSV Libro giornale scaricato da Finance e Commercialista: HTTP 200, intestazione italiana, data europea; professionista HTTP 403 | Export degli altri moduli e formati dopo salvataggio |
| CC-CAP-042 — carta/POS | BLOCKED | Implementazione e test offline presenti; nessuna scrittura contabile in questa ripresa | Fattura nuova → pagamento parziale → saldo/ledger/replay con cleanup contabile affidabile |
| CC-CAP-047 — report contabili | FAIL | Libro giornale HTTP 200, 13 righe per ruoli autorizzati; CSV HTTP 200. Bilancio di verifica HTTP 417 | Distribuire e collaudare la correzione locale del filtro centro di costo; filtri e export completi |
| CC-CAP-050 — fixture/test | PARTIAL | 95/95 test offline e 30/30 controlli critici read-only PASS | 38 controlli di sicurezza mutativi e cleanup fixture finance non eseguiti |
| SCOPE-DOC — allegati | FAIL | Fattura sintetica esistente trovata; lista autorizzata HTTP 500 `OperationalError`; professionista HTTP 403 | Distribuire la correzione locale; upload privato, lettura/download, persistenza e cleanup sicuro |
| UAT-GLOBAL — ruoli/mobile/salvataggi | PARTIAL | Sette shell e screenshot reali, 30 controlli read-only; 128 route e 22 List/Form già superati nella campagna precedente | Salvataggi, refresh e persistenza per ruolo; review visiva Owner separata |

## Cause confermate e correzioni locali

1. **Bilancio di verifica.** Il wrapper Centro Change passa a ERPNext un centro di costo come stringa JSON. La funzione pinned di Trial Balance cerca quel valore come nome letterale e genera `ValidationError` perché non esiste. General Ledger, invece, richiede il filtro JSON. `finance/native_reports.py` ora passa una lista nativa soltanto a Trial Balance. Il test offline controlla entrambi i contratti. Una chiamata diretta read-only a Trial Balance sulla versione ERPNext installata con il filtro corretto ha restituito 10 colonne e 6 righe; la correzione non è installata sul DEV.
2. **Allegati amministrativi.** Frappe 16.50 espone `File.is_remote_file` come proprietà calcolata, non come colonna SQL. `attachments.list_for_document` la usava in `frappe.get_all`, causando HTTP 500 anche su una fattura esistente. La correzione locale filtra con `is_private=1` e `file_url LIKE '/private/files/%'`, coerente con la [documentazione ufficiale degli allegati Frappe](https://docs.frappe.io/framework-git/desk/attachments) e con il sorgente pinned `frappe/core/doctype/file/file.py`. La query corretta è stata eseguita in sola lettura sul Site installato senza errore. Nessun upload è stato provato.
3. **Runner browser read-only.** Il selettore login precedente cercava un pulsante inesistente; ora usa «Continua». Il controllo CSV ora specifica Libro giornale anziché ereditare il precedente report selezionato. Lo script di resume ha eseguito soltanto la parte read-only dopo aver verificato candidato, servizi, immagine, fingerprint, hook e configurazione. La dipendenza hash dell'executor è aggiornata.

## Controlli e limiti

- `python3 -I -m unittest discover -s infra/tests -p 'test_*.py'`: **95/95 PASS**.
- `node --check` dei tre runner browser read-only e `git diff --check`: **PASS**.
- Chromium sul DEV: **30/30** controlli essenziali read-only PASS, sette sessioni demo e screenshot reali. Ruoli non autorizzati ricevono 403 sugli endpoint provati.
- Integrità dopo i test: **PASS** per dati, Communication, schema, permessi, hook, configurazione e nove servizi.
- I **38 controlli di sicurezza mutativi** e le prove contabili di POS/allegati/salvataggio restano **BLOCKED**, non PASS. La policy ERPNext conserva le tracce ledger e il precedente errore MariaDB 1020 durante il cleanup non è stato risolto; una cancellazione indiscriminata non sarebbe un cleanup affidabile. L'attuale mandato vieta nuove fixture mutative e un nuovo aggiornamento DEV.

Le evidenze grezze restano private fuori Git: `issue139-install-runs/20261019T094449Z-2969968/report.json`, `browser-evidence/issue139-20261019T094449Z-2969968/readonly-resumed/devfirst-readonly.json` e `readonly-remaining/{remaining-readonly,attachment-readonly}.json` sotto `/home/empv26/.local/state/centrochange-single/`. Il report di ottobre precedente descrive un altro tentativo terminato con rollback e rimane conservato come documento storico.

**Nessuna modifica al DEV o pubblicazione GitHub in questa ripresa.** Le correzioni locali non vanno attribuite all'immagine attualmente servita.
