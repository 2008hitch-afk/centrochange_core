# Missione B #99 — rehearsal interrotta dal safety gate

**MISSION-B-REHEARSAL: BLOCKED**

## Autorità e sorgente

Attivazione autorizzata dal commento Owner 6069834579, registrata nel commit `db9e630cfc99729c9264be1ee2939686b866cf84` sul branch `issue-99/isolated-upgrade-rehearsal`. Main non modificato. Sorgente applicativa `e85fce588de6012a47da302710b9f9c615211279` estratta senza modifiche. CAP037 snapshot `df8adf3551a234bb7edb23a9f8e546ee71b1e19f`, 11/11 blob verificati.

CURRENT: immagine G2D preservata `sha256:f8fe936c0b25c7855d266421fad0ae73679b3aa3173e91059e7c81a3fb20fc80` (baseline documentata Frappe16.31/ERPNext16.32/Marley16.5.2/Builder1.33). Avviato soltanto bootstrap nuovo site CURRENT; inventario site completo non raggiunto. TARGET Frappe/ERPNext16.50, Marley16.6.1, Builder1.35.1 pinned nel manifesto: NON costruito o provato.

## Controlli e arresto

Baseline memoria 60 secondi, lease Docker esclusiva e monitor/supervisore attivi. Risorse nuove esclusivamente `centrochange-b99-rehearsal`, rete interna, volumi esclusivi, nessun bind sorgente. Bootstrap one-shot1536MiB + DB384MiB + Redis64MiB =1984MiB, swap disabilitata tramite cap. Nessun carico build o browser.

Durante bootstrap CURRENT e archiviazione streaming delle immagini CURRENT/QA, PSI full avg10 ha superato1% per tre campioni consecutivi (picco2.97%); PSI some picco6.50%. Il supervisore ha applicato la condizione di stop approvata e arrestato soltanto i quattro container B99. Archiviatore e figli identificati tramite file di destinazione della missione sono stati terminati. Nessun kill globale.

Minimo MemAvailable5.143GiB; picco B99 campionato421.66MiB; zero OOM host/container, nessuno swap. Queste misure NON provano sufficienza TARGET. Causa del trigger verificata, causa sottostante della pressione non dimostrata; simultaneità dell'archiviazione è una correlazione, non prova causale.

Bootstrap exit1 con Lost connection to server durante new-site, coerente con lo stop controllato del DB; non classificato come incompatibilità ERPNext. Archivio immagini parziale2,953,838,592byte conservato privatamente, NON valido come checkpoint e NON dichiarato preservazione offline PASS. Checkpoint DB/file/config non acquisito. Non eseguiti build TARGET, migrate TARGET,39suite, rollback reale: tutti NON VERIFICATI.

## Stato finale

Quattro container B99 fermi, quattro volumi conservati; nessuna cancellazione. Immagini CURRENT/QA originali conservate. UAT RC229servizi attivi; ping/login/centrochange HTTP200. ID/immagini/timestamp/restart/mount/reti/porte delle30risorse protette identici al baseline. #97/G2D restano spenti. Nessuna modifica a main/prodotto/UAT/DB condivisi/cron/Docker globale; nessun provider reale.

Disco libero dopo archivio interrotto circa41.46GiB: consumo rispetto all'osservazione44.52GiB circa3.06GiB, inclusi archivio parziale, DB nuovo e metadati; nessuna prune.

## Azione successiva

Nessun riavvio automatico: sessione operativa terminata BLOCKED. Proposta per review Owner: serializzare archiviazione immagini e bootstrap, mantenendo tutte le soglie e i limiti, monitorare l'overhead host non incluso nei cgroup; nuova esecuzione solo con capacità/finestra sufficienti e autorizzazione coerente. Non allentare PSI autonomamente. Il rollback non è applicabile come restore verificato in questa esecuzione: CURRENT non completato, nessun checkpoint e nessuna migrazione TARGET avviata.

Verifica di stabilizzazione post-stop per60secondi: tutte le risposte RC22 HTTP200, PSI avg10 finale some/full0.00%, MemAvailable finale5.57GiB.
