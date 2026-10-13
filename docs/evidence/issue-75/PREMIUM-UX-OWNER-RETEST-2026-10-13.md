# Issue #75 — Premium UX: evidenze per il nuovo test Owner

**Stato: `CENTROCHANGE_PREMIUM_UX_READY_FOR_OWNER_RETEST`.** PASS tecnico e funzionale nei casi indicati; valutazione visiva Owner aperta. PR #126 resta DRAFT. Nessun merge o GOAL-03.

## Runtime

- Unico progetto operativo `centrochange-dev`: nove container, un Bench, Site `centrochange.local`, database applicativo `_4f614b4543aa5230`. Nessun reset o seed. Immagine applicativa servita: `sha256:b60c11e382127a47ce8638953334c1684dba25807a9b60a5363bcd67cce77171`.
- Stack pinned invariata: Frappe/ERPNext 16.50.0 (`f20f92d` / `7474d9e`), Healthcare 16.6.1 (`dda107b`), Builder 1.35.1 (`37e958b`); codice Centro Change dalla PR #126 sopra #125. Il commit di questa correzione è registrato nella PR.
- Accesso Owner invariato: `ssh -N -L 8082:127.0.0.1:8082 empv26@179.198.222.100`, quindi `http://127.0.0.1:8082/login`. Credenziali demo solo nel file privato `/home/empv26/.local/state/centrochange-single/demo-owner.json`, non nel repository.

## Cause e correzioni

1. **Launcher dopo il login.** Frappe apriva `/desk` o `/app` quando `default_app` non portava alla pagina Centro Change. L'app è ora registrata nello schermo app tramite hook supportato; `default_app` viene configurato per gli utenti cliente già presenti e per i successivi aggiornamenti User. Un redirect server limita solo gli URL esatti `/`, `/app`, `/desk`: Agenda per Direzione, Segreteria e Professionisti; Finanza per Finance e Commercialista. I deep link autorizzati e l'Administrator tecnico restano separati.
2. **Splash durante la navigazione interna.** I link laterali verso pagine native provocavano una nuova richiesta di documento: il router Frappe pinned non intercettava quei link `/app/` dalla pagina dedicata. La sidebar passa ora attraverso `frappe.set_route`; la pagina dedicata aggiorna il contenuto senza svuotarlo prima delle richieste asincrone e conserva la cronologia. Il brand Centro Change rimane nel solo caricamento completo/login. Nessun overlay artificiale.
3. **Form tecnici.** La fattura paziente presenta ora subito soggetto, stato, totale/residuo, scadenza e passo successivo. Direzione e Segreteria vedono i dettagli tecnici in una sezione espandibile; Finance e Commercialista conservano la scheda nativa completa. “Get Items From”, colonne Stock e tab tecniche non dominano la vista operativa, ma restano accessibili quando necessari. Anche fattura professionista, incasso/pagamento e movimento bancario hanno un riepilogo contestuale senza cambiare dati o workflow.
4. **Comprensibilità Finanza.** Ogni vista interna usa intestazione e guida breve basate sui dati e sulle azioni esistenti. Banca espone stato e riferimento di riconciliazione; SdI/TS dichiarano esplicitamente la simulazione. Il menu Finanza approvato non è stato riordinato o rinominato.

## Azioni e autorizzazioni osservate

| Documento/stato | Direzione e Finance | Commercialista |
|---|---|---|
| Fattura paziente bozza | Approva e contabilizza | Consultazione |
| Contabilizzata, non saldata | Registra pagamento, annulla, nota di credito, differisci scadenza con motivo | Consultazione |
| Parzialmente saldata | Come sopra, con residuo visibile | Consultazione |
| Saldata | Annulla o nota di credito; nessuna azione di nuovo pagamento | Consultazione |

Le azioni elencate vengono dal workflow esistente e dalle verifiche di ruolo lato server. Le fatture annullate non sono presenti nel dataset sintetico: il comportamento è stato verificato solo al confine read-only, senza creare o annullare documenti per il test. Non sono stati eseguiti salvataggi contabili o riconciliazioni irreversibili.

## Collaudo reale

| Verifica | Esito/evidenza |
|---|---|
| Login, `/`, `/app`, `/desk`, Inizio per sette account demo | PASS: `m/s/a/b/c` → Agenda; `f/t` → Finanza. Deep link interno conservato. |
| Percorso Chromium Agenda → Ricerca pazienti → Pazienti → Professionisti → Fatture pazienti → Incassi → Movimenti → Banca → Report → Agenda | PASS. [Video completo](premium-ux/journey.webm), [misure e traccia](premium-ux/journey.json). Dieci passaggi: zero richieste di documento interne, zero splash ripetuti, sidebar persistente, zero errori JS. Tempi di route osservati 372–1173 ms; campionamento ogni 50 ms, fino a 10 campioni di contenuto non pronto in una lista nativa. |
| Fatture in quattro stati, fattura professionista, pagamento, movimento, Banca, SdI/TS; ruoli `m/f/t` | PASS read-only: [dettaglio](premium-ux/finance.json). Nessuna operazione contabile scritta. |
| Sette ruoli × desktop/tablet/mobile: landing, menu, shell, overflow, branding | PASS: [matrice](premium-ux/roles.json); screenshot `premium-ux/role-{m,s,a,b,c,f,t}-{desktop,tablet,mobile}.png`. |
| Administrator tecnico | PASS: Desk Frappe nativo, shell cliente assente (`infra/browser/issue75_admin_boundary.cjs`). |
| API e accesso diretto | PASS (`infra/issue75_role_api.py`): visibilità pazienti 6/1/0 per professionisti, Finance negata ai ruoli non autorizzati, Medical Department 403. |
| Dati demo e runtime | PASS: 8 Patient, 2 Practitioner, 10 Appointment, 4 Sales Invoice, 1 Purchase Invoice, 2 Payment Entry, 2 Bank Transaction e 3 Fiscal Transaction invariati; login HTTP 200 e nove servizi attivi. |

Confronto concreto: [fattura prima](premium-native/final-fatture-pazienti-form.jpg), [fattura operativa dopo](premium-ux/native-invoice-simple.png), [dettagli contabili accessibili](premium-ux/native-invoice-advanced.png). Screenshot del percorso: [Agenda](premium-ux/agenda.png), [Ricerca](premium-ux/ricerca-pazienti.png), [Pazienti](premium-ux/pazienti.png), [Professionisti](premium-ux/professionisti.png), [Fatture](premium-ux/fatture.png), [Incassi](premium-ux/incassi.png), [Movimenti](premium-ux/movimenti.png), [Banca](premium-ux/finance-banca.png), [Report](premium-ux/report.png), [Agenda finale](premium-ux/agenda-ritorno.png).

## Limiti per il nuovo test Owner

- Nessuna fattura annullata nel dataset; test di tale stato non dichiarato PASS funzionale.
- Il video mostra alcuni intervalli brevi di caricamento delle liste native, senza splash o ricaricamento del documento. La continuità percepita richiede conferma Owner.
- Gli identificativi sintetici canonici restano nei documenti e nei riferimenti contabili; sono secondari nel riepilogo operativo, ma non sono stati alterati.
- L'accettazione visiva Owner, l'accettazione finale GOAL-02 e gli invii fiscali reali restano fuori da questo stato.
