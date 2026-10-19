# Centro Change — cinque capability residue, DEV-FIRST — 19 ottobre 2026

## Esito

**DEV AGGIORNATO: SÌ. MVP: 44/46 PASS documentati. Cinque residue: 3/5 PASS, 1 PARTIAL, 1 BLOCKED.** Non è una dichiarazione di accettazione Owner né di completamento GOAL-02. Dei 44 PASS, 40 provengono dall'audit funzionale precedente e non sono stati ripetuti indiscriminatamente; CC-CAP-047 era già PASS live e tre capability sono passate in questa campagna. La matrice puntuale è `capability-matrix-completion.csv`.

L'unico aggiornamento cumulativo autorizzato ha installato il sorgente applicativo `17100e64bfbb178da4ef27278603cca6567037d5` sui sei servizi applicativi di `centrochange-dev`. Immagine attiva e verificata: `sha256:47d753955c81033b11317381b5fdc63aa5e438cec304e57e93a0b6c0215b6758`. Executor fissato dal commit locale `a5eb338` e SHA-256 `9aa6a2c3ff68ce710f5025f21b4290b11b7c051efd796828d8f52e9d428535e6`. Rapporto privato dell'installazione: `/home/empv26/.local/state/centrochange-single/issue139-install-runs/20261019T162921Z-3278557/report.json`, stato `DEV_UPDATED_WITH_GAPS`, essenziali `PASS`, nessun rollback. Gate privato registrato prima della mutazione: operazioni fino alle 20:29:10 UTC, recupero fino alle 21:29:10 UTC. Non è stata eseguita una seconda installazione.

## Matrice delle cinque residue

| Capability | Esito | Prova sul DEV attivo | Limite |
|---|---|---|---|
| CC-CAP-029 — italiano/export | **PASS** | Browser: CSV Finanza, Pazienti, Agenda, Professionisti, Libro giornale e Bilancio di verifica scaricati con 200 per ruoli autorizzati; 403 per Professionista sui report contabili. CSV professionisti: 13 righe, intestazioni italiane, date europee, nessuna data ISO. Bilancio: 7 righe, intestazioni italiane. Libro giornale nel browser e CSV con etichette tradotte. | Nessun invio fiscale reale. |
| SCOPE-DOC — allegati amministrativi | **PASS** | Browser form XML ricevuti: documento sintetico creato, PDF privato caricato e associato, visibile nel dettaglio, scaricabile e presente dopo refresh. Finance e Commercialista 200; Professionista 403. **8/8 controlli PASS**; cleanup esatto e impronta dati ripristinata. | Il parent fattura non è stato riprovato separatamente in questa campagna. |
| UAT-GLOBAL — salvataggi per ruolo/mobile | **PASS tecnico funzionale** | Chromium: Direzione crea prenotazione su desktop e la ritrova dopo refresh; Segreteria salva nota organizzativa su mobile e la ritrova; Professionista Alfa salva nota riservata su desktop e la ritrova. Beta e Gamma ricevono 403 sul Patient diretto. Finance salva l'allegato; Commercialista lo consulta in lettura. Fixture non finanziaria recuperata esattamente. | La review visiva Owner resta separata. |
| CC-CAP-050 — suite/fixture | **PARTIAL** | 38/38 controlli HTTP di sicurezza PASS, cleanup PASS, dati e servizi invariati; 11 test locali mirati PASS; 30 controlli critici read-only e precedenti 189 controlli integrati restano evidenza valida. | La fixture finanziaria/POS non ha ancora un cleanup affidabile e non è stata eseguita. |
| CC-CAP-042 — carta/POS | **BLOCKED** | Implementazione locale e test offline presenti, ma nessun pagamento live creato in questa campagna. | Il cleanup contabile nativo richiede `Accounts Settings.delete_linked_ledger_entries=true`, mentre il DEV lo ha `false` e la policy Owner conserva ledger e audit. Un precedente `MySQLdb.OperationalError 1020` durante `native_accounting_cleanup` non è spiegato con sufficiente certezza. Un pagamento di prova mutativo non è sicuro con l'attuale fixture. |

## Test, sicurezza e integrità

- Preflight: nove servizi attivi, database e due Redis healthy; sei hook di sicurezza invariati; HTTP pronto. Backup cifrato e checkpoint verificati dall'executor prima dell'installazione. Centro A operativo e Centro B inattivo secondo il gate essenziale dell'executor.
- Asset, Socket.IO, autenticazione e permessi essenziali: PASS nell'installazione. La suite `infra/security_acceptance.py --with-booking --with-operations` ha eseguito **38/38** controlli sul runtime aggiornato con Python `-I`, fixture sintetiche e cleanup esatto. Il runner è stato corretto per importare `fixture_command` anche con Python isolato; test preventivo aggiunto.
- La prova browser degli allegati è **8/8 PASS**. La prova browser dei salvataggi è **5/5 PASS** dopo aver corretto il runner per gestire un `select` centro nascosto; i primi due tentativi di collaudo non hanno prodotto residui: entrambi cleanup `PASS` e impronta iniziale ripristinata.
- Impronta finale applicativa `3e5d431eb9cb4ed37f500e52f654cf1fbc7d75907286313dcfda70102fccaef6`, identica al checkpoint pre-installazione; Communication `a13e25cf97b4bfa76856038614ec3e99380c086fc83c322db0958490ff19ac81`; permessi `97af394ec1d9b4fe18b551282c2ecec40b5b70558e0d4968dfadf341ec66b52c`. Nove servizi e immagine attiva riconfermati dopo i test.
- Evidenze private: `browser-evidence/mvp-devfirst-3429f7d-targeted/` (nome della directory ereditato; i risultati recenti attestano l'immagine `17100e6`), `browser-evidence/issue137-fixture-20261019T163503Z/` e `browser-evidence/mvp-devfirst-role-saves/run-20261019T164150Z-9da7/` sotto `/home/empv26/.local/state/centrochange-single/`. Screenshot e risultati esistenti sono preservati. Nessuna credenziale è stata aggiunta a Git.

## Problema concreto residuo

Per dimostrare Carta/POS occorre una fixture contabile che non cancelli ledger confermati e che isoli la condizione MariaDB 1020. La prova di sicurezza attuale è fail-closed; non è stata indebolita per ottenere un PASS. Di conseguenza anche la readiness integrata CC-CAP-050 resta PARTIAL. Il DEV rimane aggiornato e accessibile.

Accesso Owner invariato: `ssh -N -L 8082:127.0.0.1:8082 empv26@srv2033673`, poi `http://127.0.0.1:8082/app/cc-unified-desk?cc_view=agenda`. Usare le credenziali demo già condivise nel canale privato. PR #141 resta DRAFT; nessun merge, pubblicazione GitHub, produzione o GOAL-03.
