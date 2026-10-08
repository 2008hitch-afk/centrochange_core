# Centro Change — Review HITCH tecnica della PR #98 (#97)

**Data:** 2026-10-08  
**Scope:** review statica GitHub + evidenze di test registrate da Codex, nessun test runtime aggiuntivo eseguito da ChatGPT.  
**Esito:** **TECHNICAL REVIEW: PASS WITH RECORDED LIMITATIONS / READY FOR OWNER DECISION**. NON e' Owner acceptance, NON e' merge authorization, NON e' nuovo candidato UAT.

## Evidenze controllate su GitHub

- [PR #98](https://github.com/2008hitch-afk/centrochange_core/pull/98): **OPEN/DRAFT**, base `issue-75/final-client-ux-review` a `84e9df1ebf80aab9905cdfc08df598a07bef0f3a`, head `9d12f5e06df92ed35de843b882f3a40e82c02b19`, metadata mergeable clean.
- [Report esecutivo #97](https://github.com/2008hitch-afk/centrochange_core/blob/9d12f5e06df92ed35de843b882f3a40e82c02b19/docs/evidence/mission97/REPORT.md): prima/dopo, riproducibilita', ruoli, hashes, limiti della fixture.
- **Unica modifica di codice applicativo:** `app/centrochange_core/centrochange_core/hooks.py`. Nel diff PR #98 la riga `before_request = ["centrochange_core.operations.website_brand.client_language"]` diventa `before_request.append("centrochange_core.operations.website_brand.client_language")`; i quattro guard originari sono mantenuti, la lingua e il login sono aggiunti dopo. Nessun modulo business/DocType/ruolo modificato. Le altre modifiche della PR sono documentazione/evidenza/test/infrastruttura laboratorio.
- Test versionato `infra/test_before_request_hooks.py` usa `runpy` sul modulo reale per richiedere esattamente i sei hook senza duplicati. `infra/mission97_hooks.py` prova readback e invocazioni WSGI reali con wrapper temporanei, preservando gli originali. `infra/mission97_http.py` usa richieste socket HTTP verso laboratorio isolato.

## Valutazione puntuale

| Verifica | Risultato / limite |
|---|---|
| Difetto prima del fix | **CONFIRMED_RUNTIME_GAP**: i quattro hook originari risultavano assenti dal valore effettivo; un report inesistente raggiungeva il dispatcher HTTP invece di essere bloccato dall'early guard. Nessun dato finanziario interrogato e nessuna fuga dimostrata. |
| Correzione minima | **PASS**: una sola istruzione nel file app, senza cambiare i guard stessi. |
| Ordine/composizione | **PASS da evidenza**: sei hook risolti e invocati in ordine nel WSGI pinned, nessun duplicato. |
| HTTP / accesso diretto | **PASS da evidenza**: `http-after.json` indica 55 controlli; dopo fix non-Manager riceve 403 per route nativa bloccata, Manager raggiunge 404 per report fittizio. Negazione note private e retained disabled account. |
| Backend | **PASS da evidenza**: `backend.json` contiene 240 checks in 7 suite (189 + 8 + 6 + 11 + 11 + 10 + 5); hash/counters persistent invariati per rollback. |
| Browser/permessi | **PASS da report**: #77, Agenda/geometry, Finance, Patient/Professional, sito pubblico/login, report/export/print e stati UI. |
| Isolamento | **PASS da report**: laboratorio Compose `centrochange-m97-lab`, site `mission97.local`, porta 8097, volumi/credenziali separati. |
| Non-interferenza UAT | **PASS da evidenza**: `noninterference.json` hash dati Owner e container IDs/start/restart/mount prima/dopo invariati. RC22 resta port8082. |
| Parita' immagine | **PASS da evidenza**: `parity.json`, product source `ee0573a42d631d97ccd5a77567ae3961de6a926c`, 239 file, 6 servizi, nessun overlay. |
| Test storici Owner | **NOT APPLICABLE** su fixture fresca, esplicitamente dichiarati nel report: audit Oct6/7, appointment132/133, invoice81, riga contabilita' cancellata. La copertura equivalente generica non dimostra replica esatta dello storico Owner. Non falsare le statistiche. |
| GitHub CI / Owner review | PR ancora **DRAFT**, la validazione del runtime e' registrata, non equivale ad approvazione Owner e non autorizza merge/deploy. |

## Condizioni obbligatorie prima di qualunque integrazione

1. Owner decide separatamente di autorizzare il **merge della correzione #98 nella catena #94** oppure una procedura di integrazione equivalente che preservi gli SHA e la tracciabilita'.
2. Owner UAT visuale dell'Agenda RC22 in [#75](https://github.com/2008hitch-afk/centrochange_core/issues/75) rimane **PENDING**; questo test tecnico non la sostituisce.
3. Non sostituire il runtime UAT RC22 con il laboratorio #97 senza autorizzazione specifica e test riferiti al dataset originale.
4. Prima di integrare la catena in `main`, preservare i **sei commit di main divergenti** che non sono nel branch UAT; eseguire trial isolato e prova di tree parity. La nuova PR #98 porta il totale della catena a **35 PR prodotto**, rispetto alle precedenti 34.
5. Nessun upgrade Frappe/ERPNext 16.50 o migrazione Desk in questa PR. `GOAL-03` non autorizzato.

**Raccomandazione HITCH:** **ACCETTARE L'ESITO TECNICO** e proporre il consolidamento di #98 in #94 come primo step della Missione A, **solo dopo autorizzazione Owner**. Non chiudere #97 fino alla review/registrazione dell'accettazione e allo stato di integrazione corretto; nessuna approvazione automatica del merge.

## Perimetro della review

La presente e' una review tecnica dei file e dei JSON/versioned report **in GitHub**. La prova di esecuzione e' quella registrata da Codex; ChatGPT non ha connesso direttamente un browser all'host di laboratorio per ripetere i test. Il risultato "PASS" si riferisce al codice, alla coerenza delle evidenze e ai test documentati, non a una nuova prova live indipendente.
