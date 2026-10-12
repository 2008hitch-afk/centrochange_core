# Missione C #109 — stop della singola attivazione demo visiva

**Esito: `MISSION-C: PARTIAL`; `READY_FOR_OWNER_VISUAL_DEMO: NO`.** Autorizzazione Owner per una singola nuova attivazione [registrata prima delle mutazioni](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6107543334). La PR #112 resta DRAFT. Nessun merge, cutover o modifica a RC22.

## Preflight e preparazione

- Branch `issue-109/unified-desk-prototype` pulito; HEAD iniziale `14992151636f2c03dda0007adf693b0a1b3233c9`. Prodotto UI `6c83704262e090d2b50c2df5362da710c50bfe52`; delta OCI privato da 81.920 byte con manifest `sha256:cc97a65c8fdd4d2cb8fd9c15fb861123bb0d3201cbbb204b4acd2352a84ada25`, verificato offline ma **non importato** in Docker.
- RC22 HTTP 200/nove container; C109 running zero; progetto nuovo `centrochange-c109-gated-r4` privo di container; porta `127.0.0.1:8109` libera. MemAvailable 5.840.527.360 byte, disco 46.848.897.024 byte, PSI full memoria/I/O sotto 1%, writer Docker libero. Config Compose isolata: otto servizi, cap 2 GiB complessivo e swap zero, cinque volumi/due reti soltanto C109.
- Finestra UTC prevista 09:30–13:30, recupero fino alle 14:00. Un timer systemd utente per lo stop alle 13:30 è stato creato e verificato `active` prima dell'attivazione.
- Il codice dell'orchestratore ha aggiunto soltanto l'identificativo del progetto demo isolato e uno stop mirato a scadenza; test statici C109 37/37 PASS. Non sono stati toccati servizi o limiti RC22.

## Primo evento di sicurezza

Prima del primo `docker load` o `docker create`, i due monitor sono stati avviati come unità systemd **utente**. Il monitor eventi ha perso immediatamente lo stream Docker e ha scritto `EVENT_STREAM_LOST`; il watchdog ha scritto `PROTECTED_EVENT_MONITOR`. Il journal delle unità mostra **`permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`**. In questa sessione shell `docker ps` funziona; il contesto delle unità systemd utente non eredita il medesimo accesso al socket. Questa è la causa verificata dello stop, non PSI/OOM.

La condizione di guard ha consumato l'unica attivazione autorizzata. **Nessun retry.** Non sono stati importati l'immagine demo, creati container R4, rilasciati workload, avviati Chromium o eseguiti test UI. Il timer di scadenza è stato disattivato dopo lo stop, perché non esiste alcun workload demo da arrestare. Stato finale: C109 running **0**, R4 created **0**, RC22 HTTP **200** con **9/9** container invariati. Volumi, immagini, dati sintetici e checkpoint preesistenti conservati. Nessun URL demo disponibile.

## Singolo gate successivo

Per una futura attivazione serve prima una prova **read-only** che watchdog, monitor eventi **e** timer di scadenza possano leggere Docker dal loro contesto effettivo e che il timer sappia arrestare soltanto il progetto C109; non basta `docker ps` dalla shell interattiva. La correzione minima è eseguire le unità nel contesto con il gruppo Docker effettivo oppure usare un servizio utente la cui appartenenza a quel gruppo sia verificata, senza modificare permessi globali del socket. Dopo la prova serve una nuova autorizzazione Owner per **una** finestra di demo: l'attuale tentativo è consumato. Non riavviare C109 con il monitor non funzionante.
