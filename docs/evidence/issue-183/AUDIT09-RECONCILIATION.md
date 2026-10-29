# AUDIT-09 — Archivi: riconciliazione tecnica

Issue #183; PR DRAFT #184. Esecuzione 29/10/2026 UTC sul codice candidato `5836d2618c25accb5dc2a25019620e5d2f0bc9c8`. Il rapporto di fase e la HEAD definitiva sono registrati nella Issue e nel tracker #156 dopo le CI della PR.

## Perimetro verificato

| Archivio | Lista, ricerca server-side, scheda Chromium desktop/mobile | Scrittura approvata sul clone |
| --- | --- | --- |
| Pazienti | PASS | Modifica con commit, lettura, idempotenza, 409 stale, audit |
| Professionisti | PASS | Modifica con commit, lettura, audit |
| Articoli | PASS | Modifica nome con commit e lettura; creazione standalone vietata |
| Tariffe | PASS | Creazione/modifica con commit, lettura, duplicato respinto |
| Tipi seduta | PASS | Creazione/modifica con commit e lettura |
| Servizi del centro | PASS | Creazione/modifica stato con commit e lettura |
| Modelli pacchetto | PASS | Creazione/modifica con commit e lettura |
| Fatture pazienti | PASS | Proiezione sola lettura; anteprima nativa |
| Fatture professionisti | PASS | Proiezione sola lettura; anteprima nativa |
| Pagamenti | PASS | Proiezione sola lettura; anteprima nativa; allocazione diretta vietata |
| Movimenti bancari | PASS | Proiezione sola lettura |

La ricerca è applicata dal server prima della paginazione. Sales Invoice, Purchase Invoice e Bank Transaction sono stati verificati con 525 righe sintetiche ciascuno, offset 500 e ricerca della riga 520. Il browser non filtra nuovamente la pagina restituita dal server. La suite prova permessi positivi e negativi via funzione Frappe diretta per Manager, Segreteria, tre Professionisti, Finance, Accountant e Guest, inclusi tentativi cross-center; le CI offline coprono anche i contratti API/React.

## Prove riproducibili fuori VPS

- [CI offline](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40845454786): SUCCESS; 177 test Python (1 skip), 228 test Playwright generali (8 skip), 36 test Playwright scoped; typecheck, build React e parità sorgente/manifesto PASS.
- [Clone Frappe/MariaDB e Chromium](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40845454789): SUCCESS; bootstrap autonomo su runner GitHub temporaneo, 11 contratti lista/scheda e ricerche, salvataggi nativi con lettura dopo commit, paginazione oltre 500, RBAC/IDOR, anteprime HTML, 11 drawer desktop e 11 mobile PASS. Pulizia di container, rete e volume del clone verificata dal job.
- 31 screenshot sintetici prodotti dal browser reale sono in questa directory. L'[artifact del runner](https://github.com/2008hitch-afk/centrochange_core/actions/runs/40845454789) conserva gli originali del job.

I limiti sono espliciti nella matrice: `CC-EXT-021` è PASS nel perimetro degli 11 Archivi, PARTIAL come completezza globale per il limite di 500 servizi nella proiezione catalogo e la finestra di 366 giorni dei pagamenti. `CC-EXT-022` è PASS per le proiezioni read-only di Archivi, PARTIAL rispetto alla scheda contabile completa riservata ad AUDIT-12/13. `CC-CAP-034` e `CC-CAP-038` rimangono PARTIAL a livello trasversale; le prove AUDIT-09 non li promuovono globalmente.

Nessun clone, database o laboratorio Docker è stato creato sul VPS applicativo. Nessuna installazione DEV, merge o modifica di produzione è stata eseguita. Le modifiche locali AUDIT-06 sono rimaste nel loro worktree.
