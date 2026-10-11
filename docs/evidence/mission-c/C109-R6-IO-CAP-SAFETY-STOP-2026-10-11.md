# Missione C #109 — r6: cap I/O applicato, stop del guard durante il database

**Esito:** `MISSION-C: BLOCKED`; `READY_FOR_OWNER_UAT: NO`. L'Owner ha autorizzato una sola nuova attivazione r6; [autorizzazione e finestra](https://github.com/2008hitch-afk/centrochange_core/issues/109#issuecomment-6111481040) sono state registrate prima della prima mutazione Docker. Inizio 2026-10-11 17:03:33 UTC, cutoff test 23:03:33 UTC, hard stop/recupero 2026-10-12 00:03:33 UTC. La prova è terminata anticipatamente alle **17:04:06 UTC** al primo evento di sicurezza. Nessun retry.

## Identità e preflight

- PR #112 DRAFT HEAD harness `0b5a68ffcc0aca56e39c81ef4d77204bc913cc27`, dipendenza #107 DRAFT. Immagine applicativa già presente, senza rebuild: OCI `sha256:602b7a1930a918dce5b957602e645a34fb4947092b6fbd55fd60e62b5694f1c1`, codice prodotto `97092a06659b4d3322bf4ce30ff6cbb06f8c28c1`.
- Preflight GREEN: RC22 HTTP 200 e nove ID; nessun C109 running; porta privata 8109 libera; volumi/reti C109 disgiunti da RC22; 5,45 GiB MemAvailable, 43,46 GiB disco libero, PSI I/O e memoria full 0%, OOM host 7, writer Docker libero. I container r4/r5 sono rimasti fermati e intatti.
- Progetto nuovo `centrochange-c109-gated-r6`; Compose controllato prima del create: otto servizi, 2 GiB RAM aggregati, swap zero, cap per servizio di 4 MiB/s read e 2 MiB/s write su `/dev/sda` (`8:0`). Monitor eventi, watchdog ed expiry indipendenti erano attivi prima del create/release; soglia PSI I/O host full **1% invariata**.

## Prova effettiva e stop

Compose ha creato otto container inerti. **Solo il database** è stato rilasciato. Prima del rilascio, il suo HostConfig riportava `/dev/sda` con 4.194.304 byte/s read e 2.097.152 byte/s write; il PID/cgroup effettivo aveva `memory.max=536870912`, `memory.swap.max=0` e `io.max` sul dispositivo `8:0` con gli stessi cap. Gli altri sette workload e il QA/Chromium non sono stati rilasciati.

| Ora UTC | PSI I/O full host | DB `io.stat` su `8:0` | PSI I/O full DB |
| --- | ---: | --- | ---: |
| 17:03:56 | 0,00% | DB non rilasciato | — |
| 17:04:01 | 0,54% | 475.136 byte letti, 0 scritti | 0,00% |
| 17:04:06 | **11,05%** | 19.922.944 byte letti, 0 scritti | **12,73%** |

Il watchdog ha scritto `IO_PSI`; il launcher ha osservato il medesimo guard e ha fermato solo r6. I 19.922.944 byte letti dal DB nei cinque secondi sono coerenti con il cap di 4 MiB/s, che quindi era **effettivamente applicato**. L'alta PSI locale e host mentre il cap limitava la lettura costituisce forte evidenza che **il throttling di questo carico contribuisce alla pressione**; non esiste però una misura contemporanea di tutti gli altri processi host sufficiente a quantificare un'attribuzione esclusiva. Non aumentare il cap o la soglia per inferenza: non è stato provato un profilo sicuro.

Al termine: `safety-stop.json=["IO_PSI"]`, `monitor-finish` presente, zero container C109 r6 in esecuzione, nessun evento protetto. Memoria PSI full 0%, MemAvailable minimo 5,27 GiB, OOM host **7→7**, disco libero 43,46 GiB. RC22: **stessi nove ID e HTTP 200** prima/dopo. Immagini, container fermati, volumi e dataset sintetico conservati; nessuna migrazione, backup, cleanup o modifica RC22.

## Matrice dei test su r6

Il guard è scattato prima che l'applicazione e il QA browser fossero disponibili. Le 24 aree della matrice GOAL-02 sono **NOT TESTED** in r6: (1) Agenda; (2) prenota/sposta/cancella; (3) seduta/storico/note; (4) pazienti; (5) professionisti; (6) disponibilità; (7) catalogo/prezzi/pacchetti; (8) contabilità/registri; (9) fatture; (10) incassi/pagamenti; (11) banca/riconciliazione; (12) report Centro/Professionisti/Pazienti; (13) report ERPNext generici; (14) SdI simulato; (15) TS simulato; (16) audit; (17) accessi/centri; (18) compensi/coda; (19) notifiche/job; (20) login/logout; (21) primo incontro pubblico; (22) stampa/export; (23) validazione DEV; (24) identità e confronto C3. **NOT TESTED** anche i sette ruoli cliente, Guest, Administrator, API/direct/query/export/print, desktop/mobile, italiano e confronto funzionale RC22. I PASS storici non vengono attribuiti a questo tentativo.

**Blocco materiale:** il profilo I/O r6 si è applicato correttamente ma non ha mantenuto la pressione host sotto il limite invariato; il primo servizio ha prodotto uno stop di sicurezza. Una successiva prova richiede una nuova decisione Owner su un percorso con margine I/O verificabile (per esempio capacità isolata diversa o un profilo operativo nuovo motivato da evidenza), e una nuova singola autorizzazione. Nessun retry r6, merge, cutover, upgrade UAT o produzione.
