# Missione C #109 — preparazione offline della correzione I/O

**Esito:** `C109_IO_REMEDIATION_READY` per revisione e **nuova autorizzazione operativa**. Nessuna attivazione C109 svolta in questa fase; i due precedenti stop restano nella cronologia. `MISSION-C: READY_FOR_OWNER_UAT` resta **NO**.

## Causa osservata e limite dell'attribuzione

Docker, i cinque volumi C109 e gli archivi privati risiedono sull'ext4 di `/dev/sda1`, disco padre `/dev/sda`; i contatori C109 `io.stat` riportano il dispositivo `8:0`. Il guard misura invece PSI I/O **dell'intero host**. La distinzione è decisiva: i byte del container sono misurati, la loro quota causale del PSI host no.

| Attivazione | Fase e finestra | I/O C109 osservato | PSI I/O full host | Altri carichi |
| --- | --- | --- | --- | --- |
| r4, [report precedente](C109-FULL-VALIDATION-SAFETY-STOP-2026-10-11.md) | Primo Chromium, Segreteria, campioni 10:42:35–10:42:40 UTC | QA: +224.501.760 byte letti, +2.134.016 scritti su `8:0` | 1,26% | Nessuna traccia storica per processo host; altri cgroup C109 già fermati nel campione finale |
| r5, [report precedente](C109-LIGHT-BROWSER-SAFETY-STOP-2026-10-11.md) | Bootstrap del solo DB, 15:25:53–15:25:58 UTC; browser mai avviato | DB: 72.970.240 byte letti, 28.672 scritti; PSI full locale 0,36% | 1,25% | Nessuna traccia storica per processo host o per RC22 nello stesso intervallo |

In entrambi i casi memoria PSI full 0%, OOM host 7→7, nessun evento protetto. Il journal accessibile non contiene un job Docker alternativo identificabile al momento del secondo stop; i timer di manutenzione visibili non provano quale processo producesse I/O. I campioni `sar` non hanno risoluzione per-processo nel secondo del guard. **Causa accertata:** letture di avvio C109 sul disco condiviso coincidenti con la pressione host e stop corretto del guard. **Ipotesi motivata, non accertata come causa esclusiva:** burst di letture C109 contribuisce al superamento; I/O contemporaneo di RC22, Docker o processi host non è quantificabile dai campioni raccolti. Le percentuali PSI locale e host non sono additive. Nessun difetto dell'applicazione è dimostrato.

## Correzione preparata nel solo harness

Il progetto isolato **`centrochange-c109-gated-r6`** riusa la stessa immagine immutabile e gli stessi volumi sintetici C109, lasciando intatti i container fermati r4/r5. `infra/c109_io_gate.py` risolve il disco padre con Docker root, mount table e volume metadata, rifiuta mount diversi o ambigui, e richiede per ogni servizio e per QA un limite Docker **4 MiB/s lettura, 2 MiB/s scrittura** sul dispositivo effettivo. È un profilo iniziale prudenziale derivato dalle letture misurate e dal precedente launcher checkpoint; **non è una velocità già provata sicura sul runtime**.

Compose incorpora il profilo nei suoi otto servizi. Il bootstrap con PID inerte verifica prima del rilascio: dispositivo autorizzato ancora valido, Compose normalizzato, Docker HostConfig, PID/cgroup v2 effettivo, `memory.max`, `memory.swap.max=0` e `io.max` finito sul dispositivo `8:0`. Se il cap manca, è illimitato, è sul device errato o supera il profilo, il workload non viene rilasciato. Il QA separato riceve gli stessi limiti I/O più RAM 512 MiB/swap zero, e li verifica prima di Chromium. Si attende il ritorno di PSI I/O full <0,1% su tre campioni tra i servizi; il watchdog continua ad arrestare immediatamente a **1%**, senza retry. I timeout del solo harness sono compatibili con l'I/O limitato; il test browser conserva JS, CSS, login e navigazione reali. Nessuna modifica a codice prodotto, ruoli, dati o configurazione globale Docker.

Il kernel documenta `io.max` come limite BPS per dispositivo, con possibili burst, e la [documentazione Docker Compose](https://docs.docker.com/reference/compose-file/services/#blkio_config) specifica `blkio_config.device_read_bps`/`device_write_bps`. Il [manuale Docker Engine](https://docs.docker.com/engine/containers/run/#block-io-bandwidth-blkio-constraint) descrive i relativi cap per device. PSI `full` misura il tempo in cui tutti i task non inattivi sono bloccati: [documentazione Linux PSI](https://docs.kernel.org/accounting/psi.html). Un cap cgroup può a sua volta generare attesa I/O; perciò il guard host non è stato allentato.

## Verifica offline e rischio residuo

- **42 test mirati PASS**, inclusi `io.max` assente/illimitato, device errato, rate eccessivo, HostConfig/Compose errati, path cgroup falso, guard PSI/OOM/RC22 e launcher checkpoint esistente. Syntax Python/Node e `git diff --check` PASS.
- `docker compose config` sul Compose C109 esistente e sull'override r6 preparato **senza creare container**: otto servizi, cap RAM aggregato 2 GiB, swap zero, `blkio_config` 4/2 MiB/s su `/dev/sda` per tutti. Risoluzione read-only sul server: `/dev/sda`, `8:0`.
- RC22 continua a rispondere HTTP 200; nessun C109 running. Nessuna build, copia, migrazione o prova browser.

**Rischi aperti:** l'applicazione effettiva di `io.max` ai nuovi container r6 non è dimostrabile offline; il prossimo avvio deve verificarla prima di ogni rilascio. Il cap può rallentare login/test o aumentare PSI per throttling, mentre l'I/O di processi host esterni non è limitato. Se PSI host raggiunge ancora 1%, lo stop resta obbligatorio: non aumentare la soglia né riprovare nella stessa attivazione. Il checkpoint integrale C109 interrotto resta invalido; il collaudo usa soltanto dati sintetici e l'immagine/versione già preservate.

## Procedura minima per la prossima autorizzazione

1. Autorizzare **una nuova singola attivazione r6** con finestra finita e tempo di recupero, senza riattivare r4/r5. Registrare immagine, sorgente, RC22, otto servizi, volumi/reti, device, RAM/disco/PSI/OOM, writer Docker esclusivo e disponibilità delle immagini di recupero. Non serve ricostruire l'immagine né ricopiare volumi.
2. Avviare monitor eventi, watchdog e expiry prima di Docker create. Con C109 fermo, verificare il Compose r6; avviare ogni servizio inertemente e rilasciarlo **solo dopo** i controlli live di RAM/swap, HostConfig e `io.max`. Attendere stabilizzazione I/O tra i servizi. Al primo guardrail, fermare solo C109 e non ritentare.
3. Avviare QA inerte con 512 MiB e `io.max` verificati, poi un solo Chromium alleggerito. Se resta stabile, proseguire con le **24 aree GOAL-02**, sette ruoli più Guest/Administrator, API/direct/query/export/print e confronto C3 con RC22 senza modificarlo. Attribuire ogni PASS all'immagine effettivamente collaudata; conservare campioni host/cgroup e risultati sanitizzati.

Questa preparazione non è una prova runtime del rimedio e non autorizza da sola il nuovo avvio. PR #112 resta DRAFT, nessun merge o cutover.
