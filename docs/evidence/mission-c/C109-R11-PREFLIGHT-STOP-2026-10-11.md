# Missione C #109 — R11 interrotta al preflight

**Esito:** `MISSION-C: PARTIAL`; `READY_FOR_OWNER_UAT: NO`. L'unica attivazione R11 autorizzata è stata chiusa. Nessun secondo tentativo, nessun container applicativo/QA avviato o creato.

## Identità e finestra

- PR #112 DRAFT HEAD iniziale `03009b2c2197c6c1c636a8d36a876b59e6191e47`; dipendenza PR #107 DRAFT `d50299f8d9ad32640259ff1c3a1fded47db5c447`.
- Immagine locale verificata read-only `sha256:ac25b74321da6de7e669e75e9a5ee23494bc6fc672d3b82498aaca73b7225d00`, label applicativa `e2fd728ecf6acdb0e0ab26379820df6905dd5521`. **Non eseguita in R11.**
- [Autorizzazione e attivazione](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6113363777): progetto `centrochange-c109-gated-r11`, 2026-10-11 20:24:20–2026-10-12 02:24:20 UTC per mutazioni/collaudo, hard stop 03:24:20 UTC. Solo deroga temporanea allo stop host PSI I/O; telemetria conservata.

## Preflight e fix dei guard

Git clean alla HEAD attesa. RC22: nove container, HTTP 200; C109 attivi zero. MemAvailable circa 5,4 GiB, disco libero circa 43 GiB, swap host zero e PSI I/O/memoria full avg10 0% al preflight. Nessun writer Docker concorrente rilevato. Compose r11 verificato staticamente: otto servizi, 2 GiB RAM/swap zero aggregati, cinque volumi e due reti con soli nomi r11, frontend `127.0.0.1:8111`. Risorse r10 e immagini non sono state alterate.

I quattro scope `rc22`, `events`, `watchdog`, `expiry` sono stati avviati senza container. La prova Docker iniziale e i heartbeat erano validi; i marker sono stati osservati rinnovati dagli stessi PID. Esempio discriminante: prima verifica RC22 21:05:47 UTC, ultimo rinnovo 21:06:35 UTC; gli altri tre marker hanno raggiunto 21:06:30 UTC senza alert. Il fix offline `03009b2` ha quindi mostrato **rinnovi reali oltre 30 secondi**, ma non è stato provato durante una copia di volume o un workload applicativo.

## Stop verificato

Il primo controllo di sicurezza invocato da un wrapper di preparazione ha passato a `c109_gated_start.guard()` i nove ID RC22 **completi (64 caratteri)** letti da `rc22-before.json`. Questa funzione confronta invece l'output di `docker ps -q`, cioè ID **brevi (12 caratteri)**, come fa il proprio `main()`. Il wrapper ha quindi ricevuto `RuntimeError: RC22 container identity changed` **prima di creare volumi o reti**. Questa è una discrepanza di formato nel wrapper operativo preparato per R11, non un cambiamento reale di RC22: un confronto separato con `docker ps -q --no-trunc` ha confermato tutti e nove gli ID completi invariati. Non è un difetto applicativo né una perdita di accesso Docker.

La condizione è stata trattata come stop del gate: `stop_only_ours` ha scritto `monitor-finish`; tutti e quattro i processi di sorveglianza sono terminati. Nessuna nuova invocazione del wrapper o del launcher, nessun retry. Lo stato privato r11 è conservato per diagnosi. Non è stato modificato `main`, il codice applicativo, RC22 o la configurazione Docker globale.

## Esiti sulla candidata R11

| # | Area GOAL-02 | Esito R11 |
|---|---|---|
| 1 | Agenda | NOT TESTED |
| 2 | Prenota/sposta/cancella | NOT TESTED |
| 3 | Sedute, storico e note | NOT TESTED |
| 4 | Pazienti | NOT TESTED |
| 5 | Professionisti | NOT TESTED |
| 6 | Disponibilità | NOT TESTED |
| 7 | Catalogo, prezzi e pacchetti | NOT TESTED |
| 8 | Contabilità e registri | NOT TESTED |
| 9 | Fatture | NOT TESTED |
| 10 | Incassi e pagamenti | NOT TESTED |
| 11 | Banca e riconciliazione | NOT TESTED |
| 12 | Report Centro/Pazienti/Professionisti | NOT TESTED |
| 13 | Report ERPNext e confini | NOT TESTED |
| 14 | SdI simulato | NOT TESTED |
| 15 | Sistema TS simulato | NOT TESTED |
| 16 | Audit | NOT TESTED |
| 17 | Accessi, ruoli e centri | NOT TESTED |
| 18 | Compensi e coda | NOT TESTED |
| 19 | Notifiche e job | NOT TESTED |
| 20 | Login e logout | NOT TESTED |
| 21 | Primo incontro pubblico | NOT TESTED |
| 22 | Stampa ed export | NOT TESTED |
| 23 | Esclusione superfici DEV | NOT TESTED |
| 24 | Identità Centro Change e C3 | NOT TESTED; RC22 baseline versionata disponibile, parità nuova UI UNKNOWN |

Sette ruoli cliente, Guest e Administrator: **NOT TESTED** sulla candidata R11. Nessun browser avviato, screenshot R11 o test mutativo eseguito. I risultati r8/r9 e i 73 test offline non vengono attribuiti alla nuova immagine in esecuzione.

## Stato finale e singolo impedimento

RC22: stessi nove ID completi prima/dopo, HTTP 200; nessuna interazione funzionale o sui dati. R11: zero container, zero volumi, zero reti e nessun QA; quattro guard terminati e `monitor-finish` presente. Immagine R10 e cinque volumi clonati R10 restano presenti; non è stato eseguito cleanup. RAM e disco finali sostanzialmente invariati. Nessun merge, cutover, produzione o provider reale.

**Correzione minima per una futura attivazione distinta:** il wrapper deve passare a `guard()` la baseline breve prodotta da `docker ps -q`, come fa `c109_gated_start.main()`, e conservare separatamente il confronto a 64 caratteri per il monitor RC22. Un test offline deve verificare esplicitamente i due formati prima dell'avvio. L'attivazione R11 è consumata e non può essere riutilizzata; serve nuova decisione Owner per un successivo tentativo. Nessuna ulteriore attività runtime viene svolta su R11.
