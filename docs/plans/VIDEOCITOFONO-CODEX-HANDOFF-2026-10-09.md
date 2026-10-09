# Handoff Codex — Centro Change Videocitofono

**Stato: WORK PACKAGE PLANNED / EXECUTION NOT AUTHORIZED.**
**Data: 2026-10-09.**
Questo file prepara la consegna a Codex, non gli conferisce un mandato server.

## Artefatti della pianificazione

- Piano: docs/plans/VIDEOCITOFONO-SOFTWARE-MASTERPLAN-2026-10-09.md
- Simulazione offline: docs/plans/sim/intercom-demo.html
- Repository: 2008hitch-afk/centrochange_core
- Active conflict/safety boundary: Missione C issue #109, GOAL-02/UAT RC22, draft upgrade #99/#107/#110/#111/#112.

## Come provare la simulazione adesso

1. Scaricare il solo file HTML dal ramo GitHub e aprirlo in un browser locale (non è una webapp pubblicata).
2. Inserire le **credenziali fittizie** demo/demo.
3. Selezionare presenza simulata in studio.
4. Premere **Simula una persona che suona**, **Visualizza ingresso**, **Attiva audio (demo)**, **Apri porta (demo)**.
5. Disattivare presenza o permesso e riprovare: apertura rifiutata.
6. Non dichiarare video/audio/apriporta reali: tutta l'interazione è sintetica, senza rete, senza microfono e senza storage.

## Codex — mandato PRE-APPROVAL (read only / proposal only)

Obiettivo: leggere documentazione già presente e proporre una scomposizione tecnica senza modificare infrastruttura, repository corrente fuori dal ramo di planning o dati.

1. Leggi AGENTS.md, README.md, ARCHITECTURE.md, SECURITY.md, docs/DECISIONS.md, docs/RUNTIME-BASELINE.md, roadmap approvata e issue #109.
2. Leggi masterplan Intercom; confronta gli endpoint/ruoli esistenti per identificare estensioni supportate. Se occorre valutare versioni/stack, distinguere CURRENT da TARGET proposto e dalla Missione C attiva.
3. Mappa le API e i permessi in una proposta, distinguendo gateway locale, flusso video WebRTC e frontend gestione esistente. Nessuna duplicazione delle credenziali.
4. Rileva soltanto da fonti pubbliche/documentazione quali modelli Comelit sono supportati dal codice open source, distinguendo fatti da ipotesi sul 20005000.
5. Produci un report di gap/decisioni necessarie in una PR DRAFT documentale, senza test runtime, build, server deploy, modifiche a container, accesso a dati reali o hardware.

NON utilizzare un processo Codex alternativo in parallelo alla Missione C: un solo writer operativo e tutti i limiti risorse/host #109 prevalgono. Nessun server accesso o nuova build implicita.

## Codex — mandato POST APPROVAL (solo con approvazione Owner separata)

Quando e solo quando ci sono (a) approvazione esplicita Mx, (b) preflight nuovo, (c) esclusività writer, (d) Gate H hardware per i sottosistemi interessati e (e) separazione da #109/UAT:

- Sviluppa una sola fase M alla volta, su branch issue-specifico e DEV sintetico dedicato, senza toccare produzione e senza cambiare core upstream.
- Non installare package/nuove image sul server per la semplice simulazione; usa la demo HTML già committata.
- Se la topologia in uso non permette un clone indipendente nel budget risorse disponibile, restituisci BLOCKED con alternativa (host locale separato, hardware dedicato o rischedulazione).
- Per M3 (POC hardware) chiedi l'ok del tecnico e svolgi solo operazioni consentite, nessuna trasmissione apriporta non autorizzata; non collegare Raspberry GPIO direttamente a L-L.
- Per M4+ riusa User/Role nel medesimo site Frappe, preferisci estensione supportata di centrochange_core; se app separata, motivane rischio e costi; niente secondo DB account.
- Gateway Comelit locale non pubblico; video/audio volatili, stream TTL, stato RAM. Le autorizzazioni sono server-side e testate sulle API dirette.
- Per ogni fase: issue, PR, elenco file cambiati, comandi eseguiti, risultati dei test, versioni vere, evidenze sintetiche, rischi, stato PASS/PARTIAL/FAIL/BLOCKED.
- Nessuna promozione a RC22/UAT/prod, migrator, data copy, upgrade upstream, apertura firewall o segreti senza decisione Owner nuova.

## Template report di fine milestone

**Milestone:** Mx  
**Issue / PR:** link  
**Baseline:** commit, versioni, DEV runtime e suo isolamento verificato  
**Test ed evidenze:** pass/fail e output minimizzati  
**Compatibilità 20005000:** NOT_TESTED / PARTIAL / VERIFIED + per funzionalità  
**Impatto 6801W:** NOT_TESTED / PASS / FAIL  
**Privacy:** media/storage/log controllati  
**Risultato:** PASS / PARTIAL / FAIL / BLOCKED  
**Rischi residui e proposta:** ...  
**Serve decisione Owner:** sì/no; precisa singola autorizzazione richiesta

## Prompt di avvio da incollare in Codex

> Lavora sul repository 2008hitch-afk/centrochange_core. Leggi prima AGENTS.md e issue #109. Questo incarico riguarda solo il nuovo piano VIDEOCITOFONO-SOFTWARE-MASTERPLAN-2026-10-09.md e la simulazione docs/plans/sim/intercom-demo.html. **Mandato: analisi READ-ONLY e proposta; NON eseguire server/host, non creare stack, non modificare UAT/RC22, non installare hardware, non cambiare la Missione C e non aprire PR di codice operativo.** Verifica la coerenza dell'architettura con la versione realmente pinned, indica dipendenze, test e stimati per M0-M9, poi pubblica un report DRAFT con decisioni aperte e stop. Non auto-autorizzarti alle fasi successive.

## Nota importanti sul costo e sul tempo

Il simulatore può essere mostrato prima dell'acquisto dell'hardware, ma non anticipa il test del 20005000. POC, integrazione app, streaming, presenza Wi-Fi e audio restano lavoro tecnico da autorizzare. Non attribuire tempi calendario certi prima che la Missione C e il sopralluogo Comelit siano pianificati.
