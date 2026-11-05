# Orchestrazione C109

Script host eseguiti e conservati per audit. Non sono un comando di riavvio autorizzato: dopo C2-STOP.json richiedono nuova attivazione controllata.

prepare_lab.py legge i metadati Compose e runtime.env privato R5; valida nomi/porte/memory/resource collision prima dell'avvio. Gli input privati non sono versionati. start_lab.py richiede monitor heartbeat, carica il delta OCI con base già presente, copia tre volumi R5 spenti read-only in C109 e avvia solo C. update_page.py applica nuove immagini dai commit; sync_page.py sincronizza Page/Sidebar nel clone sintetico. safety.py/protected-events.py proteggono RC22 e tutti i container preesistenti e arrestano solo C109.

run_browser.py usa QA pinned in network namespace del frontend C,512MiB, fixture privata e screenshot fuori dalle credenziali. qa-comparison.cjs conservato con correzione del centro per FUTURA ripresa, non eseguita dopo OOM; i risultati observed non sono alterati. verify_security.py non stampa password e usa i sette principal reali della fixture.

Per riproduzione futura servono gli input R5 privati preservati, i volumi sintetici R5 o il checkpoint documentato, base immagine/blob OCI e QA pinned. Nessuna dipendenza manuale da file modificati nei container. Non avviare questi script senza rivedere attivazione/deadline e stato corrente.
