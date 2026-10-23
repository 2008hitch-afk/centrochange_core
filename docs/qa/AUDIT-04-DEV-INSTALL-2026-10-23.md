# AUDIT-04 #167 — installazione DEV e collaudo tecnico

**Esito:** `DEV_INSTALLED_READY_FOR_OWNER_UAT`. Owner acceptance e merge: **PENDING**. Questo rapporto aggiorna le fotografie preinstallazione in [review tecnica](AUDIT-04-PATIENTS-TECHNICAL-REVIEW.md) e [remediation UX](AUDIT-04-UX-REMEDIATION.md), senza cancellarne la cronologia.

## Sorgente e runtime

- PR DRAFT [#168](https://github.com/2008hitch-afk/centrochange_core/pull/168) incorpora il ramo della PR DRAFT [#169](https://github.com/2008hitch-afk/centrochange_core/pull/169) tramite il merge commit `45303b815040f55636fc713b41a981276303d0a8`. Nessun merge verso `main`.
- Commit **applicativo installato**: `373e6ccfa26ec86572c17c202b19c7ee2097fc02`. Immagine immutabile: `sha256:be800b7e2a72dc8e0d75b6d5fce205243cb0d8f2939b43d985dd7ef0247fe496`. Label `centrochange.source` e verifica integrale di manifest, app pinned, asset e hook: **PASS**.
- GitHub Actions `Offline premerge` [run 40026944194](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40026944194) sul commit applicativo: `backend-offline` e `frontend-synthetic` **SUCCESS**. Verifiche locali: 79 test Python offline, test hook, 138 Playwright Premium PASS / 8 SKIP, 30 Playwright API PASS, typecheck/build/manifest PASS.
- Reviewer indipendente sul codice `373e6cc`: nessun finding Critical o Important; il fix finale dell'etichetta professionista nel pacchetto è stato poi verificato anche su clone reale e con screenshot.
- Unico progetto Compose `centrochange-dev`, Site `centrochange.local`, database applicativo e volumi preesistenti. I sei container applicativi usano l'immagine nuova; i tre container MariaDB/Redis hanno mantenuto esattamente ID e immagine. `cc_premium_primary=1`; gli alias cliente `/app/` e `/desk/` conducono a Premium. Nessun `bench migrate`, cambio schema, DocPerm, ruolo o configurazione fiscale.

## Gate e risultati

| Controllo | Prova | Esito |
|---|---|---|
| Checkpoint | Nuovo backup cifrato a 6 componenti, 55 entry del Site; SHA-256 archivio `710fe7f66510b38027be737b46972193eac5dfe2d0ff732f427b96250cfe0526`. Backup precedenti e chiavi restano privati, fuori Git. | PASS |
| Restore | Site/DB/volumi/rete temporanei isolati; 929 tabelle, schema, indici, conteggi e hash critici identici al DEV prima dello switch. | PASS_RESTORE reale |
| Rollback | Vecchia immagine `sha256:540f8f87c2802cd35fa85ecdbe48f38037a5611fb3e3f4d0fdae5b861fde267c` conservata; script privato validato con `ROLLBACK_READY`, limita il cambio ai sei servizi e verifica gli ID MariaDB/Redis. Non eseguito perché i gate successivi sono PASS. | READY |
| Clone funzionale | Frappe/ERPNext/Marley e MariaDB reali, sette ruoli più Guest, due centri, fixture esclusivamente sintetiche; `patients.live.spec.ts`: **21 PASS, 17 SKIP** (casi desktop-only). Inclusi API, IDOR, CSRF, note, assegnazioni, pacchetti, concorrenza, idempotenza, browser desktop/mobile. | PASS |
| Routing clone | 24/24 accessi diretti dei sette ruoli cliente e Guest sul commit finale. La prova precedente 27/27, con tecnico dedicato e Manager misto, resta valida per il routing invariato dalla sola correzione UI successiva. | PASS; tecnico/misto non ripetuti sull'ultima immagine |
| Pulizia clone | 10 risorse temporanee del collaudo e 7 del confronto post-login rimosse per ID, label, rete e mount verificati. Nessuna risorsa DEV condivisa rimossa. | PASS |
| DEV reale | Login sette ruoli sintetici, Guest negato, ricerca Pazienti, IDOR A/B, pagina desktop/mobile, 21 redirect da alias cliente, Agenda/F5, note e pacchetti in lettura, logout. Nessuna scrittura applicativa di test sul DEV. | PASS |
| Asset e dominio | `app.js` e `app.css` serviti dalla porta 8082 coincidono per SHA-256 col sorgente; l'asset HTTPS pubblico coincide con 8082. Nginx abilitato inoltra `centro-uat.empv.it` a `127.0.0.1:8082`. | PASS |
| Integrità finale | 929 tabelle, colonne, indici e hash clinici/contabili invariati. Sono cresciute solo `tabSessions` e `tabActivity Log`; confronto del `tabUser` con restore isolato: sette righe modificate esclusivamente in `last_login` e `last_active`. Nessuna fixture del clone nei quattro tipi di record controllati sul DEV. | PASS |

Gli SKIP sono casi definiti per un solo viewport, non test falliti. I test con scritture sono stati eseguiti solo nel clone; i controlli sul DEV sono stati di navigazione e lettura, salvo i normali metadati prodotti dal login.

## Interfaccia e limiti

- [Pacchetti sul clone, desktop](../evidence/audit-04-dev-final/clone-package-desktop.png) e [mobile](../evidence/audit-04-dev-final/clone-package-mobile.png): professionista leggibile nella scheda senza esporre l'ID tecnico; i test coprono anche i plurali `1 seduta` e `1 unità disponibile`.
- [Scheda sul DEV, desktop](../evidence/audit-04-dev-final/dev-patient-desktop.png) e [mobile](../evidence/audit-04-dev-final/dev-patient-mobile.png): asset distribuiti e vista reale. Il record UAT storico ha un `first_name` tecnico e manca del cognome: il titolo segnala correttamente «Anagrafica da completare», mentre il campo dati mostra il valore originale, senza inventare un nome personale. Un Patient con nome reale è stato verificato nel clone.
- Paginazione oltre le ultime 100 sedute e alcune superfici trasversali di report/export restano negli stati `PARTIAL` della matrice. Non sono state ampliate regole cliniche, finanziarie o autorizzazioni.
- URL Owner: <https://centro-uat.empv.it/premium/#Pazienti>. Usare gli account UAT sintetici già forniti con canale privato. Verificare ricerca e scheda nel centro, pacchetti/note, passaggio A/B e ritorno all'Agenda. Per provare modifiche persistenti sul DEV serve un gate separato; la prova tecnica mutativa è già PASS nel clone.

**Decisione successiva:** l'Owner valuta l'interfaccia. PR #168 e #169 restano DRAFT e non integrate; `OWNER_ACCEPTED` non è dichiarato. L'eventuale commit di sole evidenze dopo `373e6cc` non cambia i byte applicativi dell'immagine installata.
