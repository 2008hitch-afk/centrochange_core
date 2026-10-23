# AUDIT-04 #167 — Pazienti Premium React: rapporto tecnico

> Aggiornamento 23/10/2026: la successiva versione riconciliata con la PR #169 è stata installata sul DEV. Questo rapporto documenta il candidato precedente; [esito e prove finali](AUDIT-04-DEV-INSTALL-2026-10-23.md).

**Data:** 23/10/2026. **Baseline:** `main` `fa4ea4033e95301c25271d88d7d8c008b035f5c0`. **Branch:** `issue-167/patients-audit`. **Commit applicativo collaudato:** `c07b2c72eed7901abb51b0aac48e043df4b06c1f`. **Stato:** verifiche tecniche isolate `PASS`; Owner `PENDING`; DEV condiviso `NOT_TESTED` per questo candidato. Nessun merge o deploy DEV.

## Perimetro e modifiche

L'oracle indipendente è in [AUDIT-04-PATIENTS-UAT.md](AUDIT-04-PATIENTS-UAT.md). L'interfaccia `/#Pazienti` usa il Patient Marley canonico, assegnazioni, note, package e audit Centro Change; non crea una seconda anagrafica. La ricerca resta server-side e centrata sul centro autorizzato. La scheda presenta anagrafica e modifica versionata Manager, sedute/eventi, assegnazioni e revoche, note organizzative e private per il professionista assegnato, pacchetti, saldo, emissione e rettifica. Gli ID canonici restano nelle API.

Correzioni principali: autorizzazione Manager vincolata al centro e al record; consultazione storica dopo l'ultima revoca solo per Manager del centro, con scritture ordinarie bloccate; riassegnazione protetta da controllo stale; nota privata non accessibile a ruoli estranei; contesto verificato per `packages.adjust`; concorrenza/idempotenza di `packages.issue` con retry limitato dopo deadlock MariaDB 1020; aggiornamento UI in seguito a modifica. Non sono stati modificati schema, DocPerm, definizioni ruoli o core Frappe/ERPNext/Marley.

## Prove eseguite

| Ambito | Evidenza | Esito |
|---|---|---|
| Build Python/React | 72 test Python offline; `infra/verify_full_single_stack.py --source`; React typecheck/build | PASS |
| Browser sintetico | Playwright mock: 132 PASS, 8 SKIP preesistenti | PASS, non equivale a Frappe reale |
| Backup e restore | Checkpoint cifrato a sei componenti; restore su Site/DB/volumi/rete isolati; 55 entry Site e 929 tabelle; confronto schema, conteggi e hash critici al baseline | PASS_RESTORE isolato |
| Immagine | `cc167-patients:c07b2c7`, ID `sha256:46c8859ee0b7ed982a3b5320b1fe2b5d72d0bf302ba7321d5b2981b1bbd47da8`; etichetta sorgente `c07b2c72eed7901abb51b0aac48e043df4b06c1f`; manifest e asset verificati | PASS; solo clone isolato |
| Browser/API Frappe + MariaDB reali | Playwright `patients.live.spec.ts`: 17 PASS, 15 SKIP per casi API desktop-only su 32 casi, 1440×900 e 390×844 | PASS_ISOLATED_REAL |
| CI GitHub su HEAD documentale finale | Da verificare dopo pubblicazione PR | NOT_TESTED |
| Reviewer indipendente su HEAD finale | Revisione statica applicativa `c07b2c7` e test/documenti senza finding Critical/Important; attestazione sull'ultima HEAD nella PR | PARTIAL fino alla verifica dell'ultima HEAD |
| Cleanup clone per ID e fingerprint finale DEV | Rimossi per ID verificato 7 container, 2 volumi nominati e 1 rete della sola fixture #167; zero risorse label `issue167` residue; digest e conteggi di 31 DocType DEV identici prima/dopo | PASS |

La suite reale copre sette ruoli più Guest, due centri sintetici A/B, ricerca e profilo, edit/version conflict, CSRF, accessi diretti IDOR, note private e rettifiche append-only, API dirette `get_list/get/export_query`, assegnazione/revoca/riassegnazione, storico Manager dopo revoca, storico di 101 sedute con avviso esplicito del limite, pacchetti e ledger, replay della chiave, due sessioni concorrenti dello stesso Manager con un solo GRANT e un solo evento audit, riserva/rilascio e cancellazione tardiva. La Segreteria ha percorso positivo proprio. Il browser verifica la scheda desktop/mobile, la validazione, il salvataggio e i messaggi italiani. I test precedenti AUDIT-01/02/03 restano separati; le regressioni sintetiche comuni sono incluse nella suite Playwright mock.

Un test live inizialmente non era ripetibile perché riutilizzava un pacchetto sintetico consumato da altre prove. Il test ora emette un proprio pacchetto e cancella la sua prenotazione anche se una successiva asserzione fallisce. L'esecuzione completa dopo la correzione è PASS; i fallimenti intermedi non sono evidenza del candidato finale.

Il clone aveva un Site omonimo in un volume separato, DB separato, rete separata e solo record di test inventariati. L'inventario di teardown ha confermato esattamente sette container con label `issue167` (uno già spento), due volumi nominati con la stessa label e una rete posseduta; la rimozione è stata limitata ai loro ID. Il checkpoint cifrato, la verifica restore e i log privati rimangono fuori Git. Il fingerprint canonico del DEV, letto senza mutazioni immediatamente prima e dopo il teardown, ha hash e conteggi identici per 31 DocType. Nel confronto precedente con il baseline si erano mossi soltanto `tabSessions`, `tabScheduled Job Log`, `tabActivity Log` e il digest di `tabUser`, compatibili con attività concorrente del runtime: non sono prova di una mutazione #167. Schema, conteggi e hash delle tabelle Pazienti/Agenda/Finanza tracciate non erano cambiati.

## Schermate e review visiva

Screenshot da browser reale sul clone, con soli dati sintetici: [desktop](../evidence/audit-04-patients/pazienti-desktop.png), [mobile](../evidence/audit-04-patients/pazienti-mobile.png), [modifica e note](../evidence/audit-04-patients/pazienti-modifica-note.png), [storico](../evidence/audit-04-patients/pazienti-storico.png), [storico dopo revoca](../evidence/audit-04-patients/pazienti-storico-revoca.png). Controllati leggibilità, header/drawer, assenza di overflow orizzontale, focus e date italiane. Alcune sedute duplicate negli screenshot sono fixture di più esecuzioni nel clone, non dati DEV.

## Confini e rischi residui

- `patient_history` restituisce le ultime 100 sedute e la UI dichiara il troncamento. La paginazione di record più antichi non fa parte di questo contratto; `CC-CAP-006.c` resta `PARTIAL` nella matrice trasversale.
- Altri report/export e la superficie Agenda per le note private non sono stati esercitati in questo audit; `CC-CAP-018` resta `PARTIAL`. `get/list/export_query` diretti sono stati negati ai ruoli non autorizzati nel clone.
- Creazione standalone Patient, Customer fiscale arbitrario, regole cliniche/contabili nuove e riattivazione del centro storico sono fuori dalle decisioni approvate.
- La copia isolata è prova reale di codice/API e browser, ma **non** prova che il candidato sia installato sul DEV condiviso. Il DEV conserva la sua immagine precedente. Un collaudo Owner sul DEV richiede il gate `DEV_INSTALL_ALLOWED` specifico della Issue #167.
- Il tracker #156 restituisce GET 404 / WRITE 422 nell'identità corrente, come già registrato nella Issue; stato tracciato in #167 e nella PR, senza dichiarare un aggiornamento inesistente.

## Walkthrough Owner dopo eventuale gate DEV

Aprire `/premium/#Pazienti` con utenti UAT sintetici autorizzati. Cercare il paziente del centro, aprire la scheda e verificare anagrafica, modifica Manager con motivo, sedute/eventi, assegnazioni, note e pacchetti. Ripetere con Segreteria e Professionista per confrontare le azioni visibili; verificare che la nota privata non compaia a Manager/Segreteria. Il cambio centro non deve mostrare il paziente dell'altro centro. Prima dell'installazione controllata, questi passaggi restano **NOT_TESTED sul DEV corrente**.
