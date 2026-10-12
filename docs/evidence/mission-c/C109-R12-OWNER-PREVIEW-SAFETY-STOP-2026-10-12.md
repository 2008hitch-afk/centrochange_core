# C109 R12 — avvio reale e stop di sicurezza prima dell'anteprima Owner

**Esito:** `MISSION-C: PARTIAL`; `OWNER_PREVIEW_AVAILABLE: NO`. L'unica attivazione R12 autorizzata è stata consumata. Non è consentito un retry nella stessa autorizzazione.

## Identità e finestra

PR #112 DRAFT, harness `90a7a39d62abc3f20a9a76ed52c5015f4a87795b`, applicazione `e2fd728ecf6acdb0e0ab26379820df6905dd5521`, immagine eseguita `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00`. Progetto isolato `centrochange-c109-gated-r12`, frontend privato `127.0.0.1:8112`. Autorizzazione e finestra registrate nella [issue #109](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6114591757): inizio 2026-10-11 22:27:24 UTC, fine mutazioni 2026-10-12 04:27:24 UTC, hard stop 05:27:24 UTC. Lo stop automatico è avvenuto alle 01:47:08 UTC, prima della scadenza.

## Esecuzione dimostrata

- Preflight: HEAD e worktree corretti, manifest integro, OCI con label applicativa corretta, nove container RC22 attivi e HTTP 200, RAM disponibile circa 5,5 GiB, disco libero circa 43 GiB, swap zero. Nessun C109 precedente in esecuzione o risorsa R12 preesistente.
- Root privata e Compose normalizzata: otto servizi, cinque volumi R12 nuovi, due reti dedicate, porta frontend vincolata a `127.0.0.1:8112`. Le sorgenti sono le copie sintetiche R10; originali e copie R10 non sono stati sovrascritti.
- Ingresso runtime unico: `python3 infra/c109_r12_preflight.py PRIVATE_ACTIVATION_ROOT`. I quattro guard hanno prodotto heartbeat e rinnovi Docker oltre 30 secondi; la lease del writer indipendente è stata verificata. La copia seriale dei cinque volumi, l'integrità, l'attestazione e il precreate gate sono stati superati. Otto servizi hanno raggiunto lo stato running e `/login` su R12 ha risposto HTTP 200.
- QA isolato: un container da 512 MiB con swap zero e cgroup verificato. Un browser Chromium reale, con utente sintetico Direzione, ha aperto **Home**. Titolo `Centro Change · Inizio`, menu cliente presente, nessun errore JavaScript, nessun overflow desktop. Screenshot: [Home sintetica](r12/home-manager-synthetic.png). Le altre cinque sezioni richieste non sono state verificate prima dello stop.
- RC22: nove ID completi uguali alla baseline prima/dopo; ping HTTP 200 dopo lo stop. Nessun login, test funzionale o mutazione su RC22.

## Stop obbligatorio

Il watchdog ha scritto `safety-stop.json = ["PSI"]`: **pressione memoria host**, non PSI I/O. Negli ultimi tre campioni a cinque secondi, PSI memoria full è stato 1,44%, 5,12%, 2,81%; il guard ha fermato R12 al terzo campione. La deroga Owner riguardava esclusivamente lo stop per PSI I/O host e non si applica. Durante R12 il contatore OOM host è rimasto 7→7, `MemAvailable` minimo circa 4,61 GiB, uso cgroup aggregato massimo circa 1,01 GiB su cap 2,5 GiB. Questi dati **non dimostrano** quale processo dell'host abbia causato la pressione. Il PSI I/O full massimo misurato è stato 8,97%, registrato sotto la deroga temporanea.

Il watchdog ha fermato tutti gli otto container applicativi R12 e il QA; nessuno è stato riavviato. `monitor-finish` conferma la chiusura alle 01:47:08 UTC. La deroga I/O è terminata con l'attivazione. I cinque volumi R12, le due reti, i container fermi, l'immagine e i log privati sono conservati per analisi/recupero; nessun cleanup è stato eseguito. RC22 risponde ancora HTTP 200.

## Copertura e limite

| Verifica R12 | Esito |
|---|---|
| Preflight, guard Docker, lock, copia, integrità, startup otto servizi | PASS |
| HTTP login, asset/Desk Home, browser Direzione desktop | PASS limitato alla Home |
| Agenda, Pazienti, Professionisti, Finanza, Report | NOT TESTED in R12 |
| Sette ruoli, Guest, Administrator, API/direct/export/print | NOT TESTED in R12 |
| 24 aree GOAL-02, confronto C3 completo e Owner access live | NOT TESTED / non disponibile |
| Isolamento RC22 e stop mirato R12 | PASS osservato |

Non è stato comunicato un URL Owner perché l'ambiente si è fermato prima del completamento dello smoke minimo delle sei sezioni. La sola Home verificata e lo screenshot non costituiscono una preview navigabile. I PASS delle immagini precedenti non sono attribuiti alla R12.

**Azione minima successiva:** valutare con evidenza la sorgente della pressione memoria host, senza cambiare soglie o attribuirla automaticamente a C109; poi serve una distinta autorizzazione Owner per un'eventuale nuova attivazione. Nessun merge, cutover, upgrade UAT o accettazione Owner.
