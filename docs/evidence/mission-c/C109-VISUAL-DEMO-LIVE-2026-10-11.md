# Missione C #109 — demo Desk visiva disponibile

**Esito tecnico: `READY_FOR_OWNER_VISUAL_DEMO`; `READY_FOR_OWNER_UAT: NO`.** Owner authorization [registrata prima dell'avvio](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6107633856). Finestra corretta e [registrata prima delle mutazioni](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6107660093): 2026-10-11 **09:39–13:39 UTC** (11:39–15:39 italiane), con cutoff mutazioni alle 13:29 UTC e margine di recupero fino alle 14:09 UTC. Nessun merge né cutover.

## Build e isolamento

- Branch PR DRAFT #112 `issue-109/unified-desk-prototype`; HEAD operativa `7a78e08ee3ed3916668fa3735e7d53d094bf4dda`; revisione UI effettiva `6c83704262e090d2b50c2df5362da710c50bfe52`.
- OCI delta privato verificato: manifest e image ID `sha256:cc97a65c8fdd4d2cb8fd9c15fb861123bb0d3201cbbb204b4acd2352a84ada25`, label revisione `6c83704`; i 27 layer di base corrispondono all'immagine C109 già disponibile e l'archivio contiene un solo nuovo layer. Import eseguito una volta sotto guard, senza build completa.
- Progetto isolato `centrochange-c109-gated-r4`, otto servizi, cinque volumi/due reti esclusivamente C109, porta **solo** `127.0.0.1:8109`. Limite Compose aggregato 2 GiB e swap zero; ogni servizio è passato dal gate PID/cgroup prima del rilascio. QA/Chromium **non avviati** (budget QA 512 MiB conservato).
- Il preflight ha verificato inventario Docker completo, writer lock esclusivo, RC22 HTTP 200/nove ID, cgroup v2, porta libera, RAM disponibile 5.838.929.920 byte, disco libero 46.846.070.784 byte, PSI full memoria 0,00%/I/O 0,02%, OOM host 7 invariato. Soglie e controlli preesistenti non sono stati allentati.

## Guard e verifica di accesso

- `c109_guard_access.py preflight` ha verificato l'API Docker e lo stream eventi nei tre scope utente effettivi. I guard storici *events* e *watchdog* e lo stop automatico *expiry* sono attivi in tre scope indipendenti, con marker PID/start-time validi e heartbeat freschi. Nessun alert PSI/OOM, eventi protetti o perdita scope all'avvio.
- `c109_gated_start.py` ha completato **8/8** rilasci dopo verifica cap/cgroup. C109 `/api/method/ping` → **200**; accesso anonimo al Desk → login; login sintetico autorizzato → **200** con sessione non Guest; `/app/cc-unified-desk` autenticato → **200** senza redirect al login. `Page/cc-unified-desk` esiste. Hash JS/CSS della pagina nell'immagine in esecuzione identici al sorgente versionato.
- RC22 al termine del controllo: stessi **9/9** container ID e HTTP **200**. Nessuna modifica al suo dataset o ai servizi. La demo usa soltanto dati sintetici.

## Accesso Owner e limiti

Da Windows, aprire un tunnel SSH separato verso il server già usato per RC22, con forwarding `8109:127.0.0.1:8109`; quindi aprire `http://localhost:8109/app/cc-unified-desk` e accedere con l'account demo sintetico autorizzato. La password resta esclusivamente nel canale privato dell'Owner; non è riportata in GitHub.

La dashboard italiana offre link per ruolo ad Agenda, Pazienti, Disponibilità, Notifiche, Finanza/Banca, SdI e TS simulate, report e liste native pertinenti. Questo è un controllo leggero di raggiungibilità/autenticazione, **non** il collaudo browser delle 24 aree, né UAT finale. Lo stop automatico è previsto alle 13:39 UTC; watchdog e monitor eventi restano attivi fino allo stop. Al primo evento di sicurezza la demo deve fermarsi senza retry.
