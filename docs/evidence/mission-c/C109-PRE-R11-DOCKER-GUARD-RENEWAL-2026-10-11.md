# Missione C #109 — prova Docker dei guard, correzione offline pre-r11

**Esito:** `C109_PRE_R11_GUARD_READY` per l'harness offline. La UI non è stata collaudata sulla candidata r10 e `MISSION-C: READY_FOR_OWNER_UAT` resta **NO**. Nessuna nuova attivazione C109 è stata eseguita.

## Causa e confine

Il rapporto [r10](C109-R10-GUARD-STOP-2026-10-11.md) ha dimostrato uno stop corretto del gate prima della creazione dei container applicativi: la prova Docker del guard eventi aveva oltre 30 secondi dopo la copia seriale dei volumi. I quattro processi avevano verificato Docker solo all'avvio; heartbeat recenti e stop per marker `stale` non dimostrano una perdita reale di accesso al socket. La soglia di 30 secondi resta invariata.

## Correzione versionata

- `infra/c109_guard_access.py`: ciascuno scope mantiene il medesimo PID per il proprio loop di sorveglianza e per un thread locale di rinnovo. Il thread, ogni 8 secondi, ripete **dal processo del guard** la verifica del socket, del gruppo effettivo, di `DOCKER_HOST`, del contesto/endpoint e delle API Docker; per eventi verifica anche la sottoscrizione live. Controlla PID/start ticks, UID/EUID/EGID/gruppi, heartbeat e che il marker non sia stato modificato durante la verifica. Solo dopo pubblica il nuovo marker con sostituzione atomica, file regolare privato `0600`. L'handler non accetta prove future, scadute o con identità/contesto diverso. Dopo la pubblicazione controlla anche la continuità degli altri scope quando il manifest degli scope è presente.
- Un fallimento crea un alert privato e tenta lo stop mirato del solo progetto dell'attivazione; il processo guard termina. Gli altri guard e il gate rilevano l'alert o la perdita dello scope. La scadenza automatica e il monitor indipendente RC22 restano attivi. La prova Docker non può essere rinnovata da un processo esterno al guard.
- `infra/c109_compose_gate.py` e launcher correlati: il solo nuovo nome progetto `centrochange-c109-gated-r11` è ammesso nei gate già esistenti; conserva otto servizi, 2 GiB runtime, QA 512 MiB, swap zero e il controllo RC22. Il nome QA r11 è distinto. Non sono stati modificati limiti PSI/OOM/I/O, permessi Docker globali, policy applicative o immagini.

## Prove offline

`PYTHONPATH=infra python3 -m unittest -q infra.test_c109_guard_access infra.test_c109_compose_gate infra.test_c109_rc22_monitor infra.test_c109_r7_safety_prepare infra.test_c109_r9_activation infra.test_c109_monitored_step infra.test_c109_gated_frontend_update infra.test_c109_protected_inventory infra.test_c109_checkpoint_launcher`: **52/52 PASS**. `python3 -m py_compile` sui moduli cambiati e `git diff --check`: **PASS**. Tutti i comandi sono offline; test con mock/fake, nessun container avviato.

I test discriminanti coprono preparazione simulata di 72 secondi con nove rinnovi consecutivi, rinnovo da ciascuno dei quattro guard nello stesso PID, perdita Docker/API o stream eventi, prova scaduta, PID/start ticks differenti, heartbeat mancante/scaduto, contesto cambiato, marker manomesso/non privato, alert, stop mirato del progetto r11 e impossibilità di estendere la vita del marker oltre 30 secondi. Il gate r11 richiede esplicitamente il quarto guard RC22. Le regressioni dell'orchestrazione di checkpoint, monitor RC22, Compose, preparazione watchdog e passaggi monitorati restano verdi.

## Candidata e limiti

La candidata applicativa r10 `e2fd728ecf6acdb0e0ab26379820df6905dd5521`, immagine OCI `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00`, è ancora presente (inspect read-only). I cinque volumi clonati r10 risultano presenti (list read-only). Non sono stati avviati, letti nei contenuti, modificati o rimossi. La PR #107 resta una dipendenza DRAFT; la PR #112 resta DRAFT.

L'esecuzione reale del rinnovo durante una copia lunga, la salute dei quattro scope con la nuova tecnica `runpy` e la UI sull'immagine effettiva **non sono ancora verificati nel runtime**. Se Docker stesso non risponde, nessun guard può garantire che lo stop mirato completi finché l'API non torna disponibile: il processo fallisce chiuso e gli altri scope/expiry continuano a tentare la protezione. Questo è un rischio operativo da osservare nel prossimo preflight.

## Unico prossimo gate

Per r11 serve una **nuova singola autorizzazione Owner** con finestra finita, massimo sei ore di collaudo e un'ora di arresto/recupero, progetto e risorse r11 isolati, eventuale sola deroga PSI I/O espressamente rinnovata, immagine pinned e recupero verificato. Prima del workload: preflight RC22, spazio/RAM/OOM, guard in scope, prova Docker rinnovata durante la preparazione, heartbeat e stop automatico; al primo safety event, arresto senza retry. Solo dopo possono essere eseguite le 24 aree e i controlli di ruolo. Nessuna autorizzazione r10 è riutilizzabile.
