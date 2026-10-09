# Centro Change — Piano software Videocitofono v0.1

**Data:** 2026-10-09  
**Stato:** PLANNING / SIMULATION ONLY — NOT AUTHORIZED FOR SERVER EXECUTION  
**Owner approvazione:** da richiedere dopo review.  
**Repository canonico:** 2008hitch-afk/centrochange_core.  
**Dipendenza principale:** GOAL-02 e Missione C, issue #109. Non interferire con UAT, RC22, source checkout, build o container esistenti.

## 0. Scopo e verità di partenza

Costruire la funzionalità Videocitofono nello stesso ecosistema di account e ruoli del Gestionale Centro Change, senza creare un secondo archivio utenti. L'impianto esistente Comelit 6801W deve continuare a funzionare. L'interfaccia deve mostrare chiamata in arrivo, video live e comando Apri agli operatori autorizzati presenti nello studio, con audio bidirezionale come ulteriore obiettivo soggetto a POC specifico.

**Non dimostrato:** che Comelit 20005000 fornisca su rete un endpoint ViP localmente interoperabile con i client open source (chiamata/video/apertura/audio). La presenza della porta LAN, il protocollo ViP e le librerie community NON provano compatibilità con il 20005000. Non acquistare hardware basandosi su una promessa di GO.

**Non è produzione:** la simulazione GitHub contiene solo dati fittizi, non parla a porte o citofoni e non apre alcuna porta. Nessun componente è ancora installato o collaudato da questo piano.

## 1. Ownership dei componenti

| Livello | Responsabilità | Tecnologia candidata | Confine |
|---|---|---|---|
| Gestionale Centro Change | User, sessioni, ruoli e permessi, navigazione e API | Frappe (stack già esistente) e centrochange_core | mai patch upstream |
| Modulo intercom | regole di autorizzazione, policy della presenza e richieste temporanee; NO video nel DB | modulo custom nello stesso sito; eventuale app separata solo se vantaggiosa | non duplicare User e password |
| Gateway locale | interfacciamento Comelit, sessioni video/audio, eventi e comandi; isolare ViP | Raspberry Pi 5 o mini-PC Linux; servizio Python separato | solo LAN, nessun servizio Comelit esposto su Internet |
| Media bridge | riceve eventuale flusso proprietario e pubblica media compatibili con browser | RTP/RTSP -> WebRTC tramite go2rtc/GStreamer o equivalente, dopo POC | niente storage media |
| Presence adapter | stabilisce presenza dalla infrastruttura Wi-Fi vera | access point/router locale con API/query server-side | non fidarsi di Wi-Fi/IP dichiarato dal browser |
| Frontend | esperienza mobile responsive e notifiche | UI custom Gestionale Centro Change / PWA | autorizzazioni sempre server-side |

Una eventuale app Apple/Google è futura fase separata. QR pazienti è FUTURE SCOPE, non va implementato nell'MVP.

## 2. Funzioni e vincoli accettati come ipotesi di prodotto

- Account e password già presenti nel sito gestionale; permessi distinti VIEW_INTERCOM, ANSWER_AUDIO, OPEN_DOOR e MANAGE_INTERCOM.
- Chiamata in arrivo notificata a tutti i professionisti autorizzati **presenti**, con presenza verificata dalla rete (non GPS e non toggle manuale).
- Video on-demand live, non registrato, disponibile a più viewer se la sorgente supporta correttamente fan-out senza creare chiamate concorrenti sul bus.
- Comando Apri solo da utente abilitato, autenticato e presente; controllo server-side nel momento del comando; rate limit e protezione replay.
- Audio bidirezionale desiderato nell'ultima richiesta, ma da trattare come milestone condizionata: prima dimostrare ricezione, trasmissione, latenza, eco, concorrenza e compatibilità con 6801W; un solo speaker alla volta.
- Nessuna registrazione, snapshot salvati, log storico delle chiamate, evento apertura con identità del professionista. Solo stato effimero in memoria con TTL; gli inevitabili log infrastrutturali di sicurezza vanno verificati e minimizzati, senza promettere assenza totale di log di rete.
- Mobile iOS/Android: notifiche a schermo bloccato non equivalgono a chiamate native. Verifica reale su telefoni, permessi microfono su gesto esplicito.
- Conservare funzionamento fisico del 6801W e predisporre percorso di fallback in caso di mancanza rete/server.
- Privacy condominiale: installatore autorizzato per Simplebus2, verificarne topologia, alimentazione, componenti, autorizzazioni e documentazione Comelit.

## 3. Due gate indipendenti

**GATE H (hardware / ViP):** con installatore e dispositivo prestato o reso possibile, dimostrare dalla nostra implementazione: (H1) registrazione/discovery IP, (H2) rilevazione chiamata corretta per Centro Change, (H3) video live decodificabile, (H4) apertura controllata, (H5) audio due vie. Se H3 o H4 falliscono: NO-GO specifico del 20005000 per l'app custom, non NO-GO del progetto generale. Solo TCP 64100 aperta NON basta. L'audio H5 può restare PARZIALE e richiedere decisione sulla fase separata.

**GATE S (server / governance):** verificare in read-only stato della Missione C (#109), UAT/RC22, versione Frappe pinned effettiva, servizi e risorse host, spazio disco, memoria e ripristino. Nessun build, install, migrate, restart, cleanup o creazione stack sul server prima di autorizzazione Owner specifica. La simulazione locale/GitHub non richiede GATE S. Non usare la finestra operativa o i limiti di risorse storici come autorizzazione nuova.

## 4. Percorso utente MVP

1. Professionista apre Gestionale Centro Change con credenziali esistenti.
2. Sistema verifica ruolo; presence adapter conferma Wi-Fi studio da infrastruttura locale.
3. Quando suonano, gateway emette evento interno effimero; fan-out verso utenti presenti via evento realtime/push.
4. Il professionista apre Videocitofono: media bridge apre un'unica sessione video necessaria; più viewer ricevono lo stesso stream.
5. Se autorizzato, preme Apri: backend ricontrolla User/role/presenza/sessione e invia richiesta firmata e a scadenza ravvicinata al gateway.
6. Il gateway comunica con Comelit; UI conferma soltanto l'esito verificato (non al semplice click).
7. Fine chiamata: rilascia canali, cancella stato effimero, nessun salvataggio di video/chiamata/apertura.

## 5. Macro fasi e stime in giornate tecniche (1 implementatore, non giorni di calendario)

| Codice | Fase / output | Durata | Bloccanti e gate |
|---|---|---|---|
| M0 | Inventario read-only + design contratti + review UI/ruoli | 1–2 gg | planning solo |
| M1 | Simulatore fittizio GitHub e walkthrough cliente (offline) | 2–3 gg | nessuna dipendenza hardware |
| M2 | Sopralluogo tecnico e installazione POC autorizzata | 1–2 gg | materiale e tecnico disponibili |
| M3 | Protocol spike 20005000: ring, video, apri, compatibilità 6801W | 3–7 gg | Gate H; STOP a budget/tempo concordato |
| M4 | Integrazione utenti/permessi nel gestionale DEV isolato | 3–5 gg | Gate S, autorizzazione owner |
| M5 | Media bridge WebRTC, multi-viewer, stop stream, nessun recording | 3–5 gg | M3 video PASS |
| M6 | Apriporta protetto + controlli anti-replay e failure cases | 2–4 gg | M3 apri PASS |
| M7 | Wi-Fi presence, notifiche realtime/push, iOS/Android | 4–7 gg | gateway AP e accesso admin compatibili |
| M8 | Audio RX/TX, single talker, gestione permessi, eco | 5–12 gg | gate H5 specifico: milestone condizionata |
| M9 | Regressione, collaudo 6801W, privacy, documentazione e handover | 3–5 gg | tutti i blocchi MVP previsti completati |

**Totale stimato senza audio:** 22–40 giornate tecniche, cioè circa 5–8 settimane lavorative per uno sviluppatore, se i gate sono positivi. **Con audio:** 27–52 giornate, circa 6–11 settimane lavorative. Possibili sovrapposizioni riducono alcuni tempi di calendario, mentre disponibilità installatore, approvazioni, acquisti, Missione C e reverse engineering li possono allungare. Queste sono ipotesi, non promesse contrattuali.

### Milestone calendariali di orientamento (solo dopo autorizzazione)

- **Settimana 1:** M0-M1, storyboard e mock interattivo; sopralluogo da fissare.
- **Settimana 2:** M2-M3, GO/PARTIAL/NO-GO su hardware, con report.
- **Settimane 3–4:** M4, M5 e M6 su DEV isolato, backend/auth e prima demo funzionale.
- **Settimane 5–6:** M7, e prime regressioni M9.
- **Settimane 7–8+:** hardening e consegna MVP; M8 audio in parallelo/ulteriore fase 1–3 settimane se superato H5.
- Se M3 non dà video+apri, pausa tecnica e decisione tra bridge diverso, camera IP aggiuntiva autorizzata o architettura ufficiale Comelit.

## 6. Matrice delle evidenze necessarie (minima)

| ID | Caso | Criterio di uscita |
|---|---|---|
| T01 | Utente autentico con permessi | Videocitofono visibile e API autorizzate |
| T02 | Utente non autorizzato/Guest | tutte le API di stream/open bloccate anche se chiamate direttamente |
| T03 | Utente fuori studio | nessuna notifica studio e nessuna apertura |
| T04 | Ring pertinente | notifica ricevuta da presenti senza leak verso altri appartamenti |
| T05 | Video live | frame reali visualizzati da 3 browser con 1 sola sessione sorgente |
| T06 | Apri | apertura reale solo dopo conferma gateway, con time-out e replay rejection |
| T07 | Audio | mic RX/TX provato nei due sensi, 1 speaker alla volta, senza registrare |
| T08 | 6801W | continua a suonare, mostrare video e aprire come prima |
| T09 | Privacy | nessun media persistito; controllare File, log app, proxy, cache/browser |
| T10 | Resilienza | reboot router/gateway/app, risincronizzazione e nessuna apertura spontanea |
| T11 | Notifiche iPhone/Android | prove con telefono attivo/bloccato e permessi reali |
| T12 | Accettazione | walkthrough professionista/segretaria, report finale PASS/PARTIAL/FAIL |

I test possono generare soltanto evidenze sintetiche o sanitizzate in GitHub. Le prove sul citofono reale devono essere autorizzate e svolte sul posto.

## 7. Coordinamento ChatGPT / Codex / Owner

- **ChatGPT:** requirements, architettura, milestone, issue e acceptance criteria; revisione PR ed evidenze. Non afferma PASS su runtime senza report concreto.
- **Codex:** dopo un gate di esecuzione specifico verifica ambiente, realizza branch e codice isolato, esegue test e redige PR con evidenze. Un solo writer operativo, mai modifiche manuali a container running come soluzione permanente.
- **GitHub:** fonte di verità di piano, stato, issue, blocchi e decisioni.
- **Owner:** autorizza spese, sopralluogo, cambio architettura, lavoro sul server, commit/merge che cambiano scope, produzione.
- **Missione C #109:** mantiene priorità e confini correnti; il piano intercom NON la autorizza né la interrompe.

## 8. Contratti da validare prima del coding reale

- Eventi gateway effimeri: ring_started, video_ready, ring_ended, gateway_unavailable con session_id casuale e scadenza.
- Comandi: open_door(session_id, nonce, issued_at, expiry) e, solo quando dimostrato, audio_start/audio_stop.
- Backend: accesso per permesso + presenza server-side; mai username/ruolo dal client come prova di autorizzazione.
- Single-session gateway: serializzare richieste sorgente Comelit, fan-out WebRTC multiplo.
- Nessuna duplicazione di Doctor/Patient/Appointment nel bridge; solo integrazione opzionale futura QR/accoglienza con gli oggetti canonici già esistenti.

## 9. Fonti e incognite documentate

- Manuale 20005000: https://staticpro.comelitgroup.com/storage/2021/06/29707/mt-20005000.pdf
- Reverse engineering ViP, testato con altri dispositivi: https://github.com/jfmlima/comelit-vip
- Altra integrazione locale (non prova su 20005000): https://github.com/antoiba86/hass-comelit-intercom-local
- Segnalazione Simplebus2 (non demodula A/V): https://github.com/plusvic/simplebus2-intercom
- Regole progetto: README.md, ARCHITECTURE.md, AGENTS.md, docs/MVP-GOAL-ROADMAP-v0.1.md, docs/DECISIONS.md
- Vincolo attuale: https://github.com/2008hitch-afk/centrochange_core/issues/109

## 10. Decisioni da prendere all'avvio

1. Il cliente conferma **audio bidirezionale come incluso nel V1** oppure **V1 video+apri, audio fase successiva**? Non nascondere differenze di costo/tempo.
2. Dispositivo 20005000 in prestito/resituibile e modalità sopralluogo con installatore autorizzato?
3. Router/AP dello studio supporta introspezione presenze Wi-Fi attendibile senza GPS?
4. È autorizzata una nuova prova sul server quando Missione C e capacità saranno compatibili?
5. Niente QR automatico nella V1: soltanto disegno dell'estensibilità.

**Stato attuale:** soltanto plan e simulazione GitHub; ZERO conclusioni di compatibilità hardware o runtime.

## 11. Posizionamento server e connettività: decisione prima della M4

Il documento vigente sul runtime descrive DEV su workstation Windows/WSL2 + Docker, non certifica che esista già un ambiente PROD Centro Change su VPS. Il nuovo gateway fisico sarà nello studio, mentre la collocazione finale del Gestionale Centro Change dovrà essere confermata prima di implementare M4/M5/M7.

- **Gestionale e gateway entrambi in LAN studio:** il traffico multimediale può rimanere sulla LAN dopo autorizzazione; il telefono deve potersi connettere al percorso browser sicuro.
- **Gestionale esterno / cloud e gateway nello studio:** usare un tunnel autenticato outbound dal gateway o altro collegamento privato autorizzato; non esporre direttamente ViP/RTSP, ingresso o apriporta su Internet. Il flusso verso i telefoni dovrà attraversare una infrastruttura sicura con controllo dell'accesso e verifica del budget banda, senza registrazione.
- **Internet studio assente:** monitor 6801W continua a funzionare. Le notifiche o azioni mobile remote non vanno promesse senza test espliciti.
- **Presenza Wi-Fi:** non considerare l'IP pubblico condiviso come prova di essere nello studio. La verifica viene effettuata dal lato AP/router, associata in modo sicuro al dispositivo/user autorizzato; verificare comportamento con MAC randomizzato, standby e connessione dati mobile.

Questa scelta può modificare stime, costi ricorrenti e modalità di push. Codex deve proporre una matrice di alternative e non decidere o installare autonomamente un tunnel.

## 12. Evoluzioni future, non incluse nell'MVP

Le stime seguenti sono per pianificazione, non per il preventivo attuale.

| Future phase | Funzione | Stima ulteriore | Dipendenze |
|---|---|---|---|
| F1 | QR per check-in del paziente, senza apertura automatica | 3–6 giornate | regole appuntamento, consenso/informative, UX, link temporanei |
| F2 | QR personale temporaneo per apertura, lettore ingresso e permessi | 6–12 giornate software + installazione esterna | autorizzazioni condominiali, sicurezza anti-replay, lettore e test |
| F3 | App Centro Change iOS + Android da frontend riusato | 10–20 giornate software + tempi revisione store | push nativo, login, media, sicurezza, account store |
| F4 | Automatismi arrivo paziente / professionista / segreteria | 4–8 giornate | funzionamento già validato di Gestionale + modello evento |

Queste fasi possono partire **solo dopo** accettazione del modulo base e nuova valutazione clinica/privacy, perché ingresso e appuntamenti dei pazienti non devono rendere pubblico chi è in cura o quando arriva.

