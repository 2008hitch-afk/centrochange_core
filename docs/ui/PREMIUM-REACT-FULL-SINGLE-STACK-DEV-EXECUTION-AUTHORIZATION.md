# #148 — DECISION-064 Owner APPROVATO: Full Single-Stack DEV Rebuild

**Data approvazione:** 21/10/2026  
**Autorità HITCH:** [HC-0005 DECISION-064](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-064-authorize-full-single-stack-dev-rebuild.md) · [PR HITCH #114 merged](https://github.com/2008hitch-afk/hitch-client-discovery/pull/114)  
**Fonte piano esatto:** [SINGLE-STACK-COMPLETE-REBUILD-EXECUTION-PLAN.md](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/SINGLE-STACK-COMPLETE-REBUILD-EXECUTION-PLAN.md) — blob `27c64b26249a7045f66954ce42fa7cf06555ea2f`.  
**Candidato PR:** [#150 DRAFT](https://github.com/2008hitch-afk/centrochange_core/pull/150), HEAD al momento dell'autorizzazione `ca58e2fa1aa199244553718a5b5268717db2de90`.  
**Stato corrente:** `OWNER_AUTHORIZED_PENDING_PREFLIGHT` — **nessuna build, backup, restore, sostituzione o UAT live ancora eseguita**.

## Cosa è ora autorizzato

L'Owner ha detto **«OK approvo e procediamo»** alla richiesta di una sola ricostruzione completa sul server esistente in **DEV con dati sintetici**. È **un solo intervento condizionato**, non un permesso generalizzato per modificare il server.

- Usare il solo host `srv2033673`, Compose `centrochange-dev`, Site `centrochange.local`, DB applicativo esistente `_4f614b4543aa5230`, porta loopback `127.0.0.1:8082`. **Preservare** Site, DB, MariaDB, Redis, quattro volumi nominati, rete, segreti e stato legittimo.
- Read-only fingerprint preflight su tutti i container, pin app/immagini, HEAD PR, manifest, config Compose privata (identità già autorizzata, niente chmod/bypass/secret nei log), cgroup, risorse, assenza di dati reali o altri progetti. Qualunque divergenza materiale => **STOP**.
- Build **completa da codice sorgente** con `infra/Dockerfile.single-stack-full`, `infra/verify_full_single_stack.py` e `infra/full-single-stack-manifest.json`, partendo dalla base digest-pinned `frappe/erpnext:v16.50.0@sha256:833bceb57233908cbc949d7aa533942b18e54b329d846b933b66937c62b7e4ae`; Builder e Healthcare/Marley su commit immutabili. Non riutilizzare `infra/Dockerfile.premium-single-stack` o cinque override vecchi. Distinguere `SOURCE_PARITY_PASS` da `BUILT_IMAGE_PASS`.
- Backup cifrato, checksum/decryption test, prova **vera** di restore su risorse effimere nominate nel piano e rete interna no-port, confronto schema/ruoli/custom fields/fixtures. Conservare backup e chiavi in percorsi riservati separati fuori Git. Ripristino fallito => **STOP**, non switch.
- Solo dopo tutti i gate PASS, ricreare i **sei container applicativi** `backend/frontend/websocket/queue-short/queue-long/scheduler` nello stesso Compose con la **nuova immagine completa**, mantenendo 3 servizi db/redis e stato. Non avviare configurator, non migrare, non cancellare DB/volumi. Il nuovo Compose `infra/compose.single-stack-full.yaml` deve avere diff effettivo non materiale rispetto alle impostazioni runtime correnti al netto della nuova app/retirement configurator.
- Bloccare nuove scritture per massimo **120 minuti** dalla sospensione a smoke health; build/preparazione prima del blocco. Se si avvicina la scadenza senza PASS, scegliere un rollback sicuro e non continuare il deploy.
- Test **Frappe live** con soli dati sintetici: 7 ruoli + Guest, centri A/B, auth/CSRF, ACL native e scoped, 11 liste/form, agenda/booking, pazienti, professionisti, catalogo, pacchetti, Finance, pagamenti, stampa, XML, audit/replay, export, desktop/mobile e performance (p50/p95), OOM. Non trasferire come PASS risultati di mock/vecchie build.
- Se test o safety falliscono, rollback solo secondo schema/data fingerprint: immagine precedente quando dati/schema invariati; ripristino verificato soltanto nella procedura approvata se necessari, evitando perdita di scritture e senza forzare. STOP se recupero non dimostrato, escalation Owner.
- Test visivo **Owner separato**: lasciare `cc_premium_primary=0` fino a `TECHNICAL_LIVE_PASS` e **accettazione visiva esplicita Owner**. Solo dopo, flag `1` e React come ingresso primario dei ruoli operativi; Desk tecnico ai soli ruoli specializzati con ACL native. Non promuovere automaticamente a `OWNER_ACCEPTED`.
- Cleanup: è consentita **solo la rimozione nominativa delle risorse temporanee restore** dopo esito e prove. Immagini storiche, configurator, volumi log e altra pulizia finale: dopo UAT/accettazione e **nuova conferma Owner sulla whitelist aggiornata**. No `prune`, no reset o wildcard.

## Limiti non estesi

Non autorizza produzione, GOAL-03, Site/DB/volume wipe, `migrate`/schema change, altri server, clienti o progetti, nuovi permessi/ruoli, nuove business rules, provider reali o dati veri, licenze, merge #150, cleanup storico automatico, attivazione di React prima di UAT Owner. Le operazioni Item/Patient/Practitioner standalone create e Payment Entry create/allocate non autorizzate restano fail-closed in DECISION-063.

## Istruzione Codex — UN SOLO CICLO

```text
Riprendi nella stessa sessione Codex l'UNICO macro-goal #148, PR DRAFT #150, senza /goal e senza ricominciare. HC-0005 DECISION-064 è APPROVATO: esecuzione condizionata dell'intero SINGLE-STACK-COMPLETE-REBUILD-EXECUTION-PLAN.md (blob 27c64b26249a7045f66954ce42fa7cf06555ea2f), non il precedente piano overlay. Leggi DECISION-060/061/062/063/064, AGENTS.md e questo mandato.

Prima di ogni mutazione confronta HEAD, source manifest, Compose privato accessibile con identità legittima, identificativi attuali, schema/ruoli, data synthetic-only, cgroup, RAM/PSI/OOM/disco, dipendenze di altri progetti. Se un prerequisito fallisce, STOP; non interpretare l'approvazione come permesso di bypassarlo. Registra fingerprint/checkpoint fuori Git senza segreti.

Esegui l'intero flusso autorizzato come una missione: build immagine full-source pinned e verifica con container effimero senza mount DEV; backup cifrato e prova di restore realmente isolata sui cc148-restore-* nominati; soltanto dopo PASS_restore e schema/Compose equivalenti ricrea i SEI container applicativi su centrochange-dev con il Compose canonico unico preservando Site/DB/volumi/DB Redis, senza migrate. Write freeze <=120 minuti e rollback sicuro immediato se fail. Verifica health e app versions; esegui QA Frappe live con 7 ruoli+Guest, sicurezza, centri, 11 liste/form, funzioni MVP/Finance/Agenda, print, API, prestazioni e mobile/desktop, con dati sintetici. Riferisci PASS/PARTIAL/BLOCKED provato.

La UI React NON diventa home predefinita automaticamente: lascia cc_premium_primary=0 e predisponi URL privato/credenziali Owner UAT solo dopo technical PASS. Aspetta accettazione grafica Owner prima del flag; non fare cleanup storico prima di Owner confirm whitelist, né merge PR, go-live, dati reali, nuove policy, reset o migrazioni. Rimuovi soltanto restore effimero per ID dopo prove, preservando backup cifrato.

Non fermarti per micropassaggi ordinari già nel piano. Alla fine fornisci: stato tecnico reale, versione/HEAD/image IDs, esiti backup/restore, diff Compose sanitizzato, suite security/ruoli/UI/performance, URL di collaudo quando sicuro, stato del rollback, gap e un solo gate Owner residuo. Non dichiarare READY_FOR_OWNER_VISUAL_UAT finché live tests non sono PASS.
```
