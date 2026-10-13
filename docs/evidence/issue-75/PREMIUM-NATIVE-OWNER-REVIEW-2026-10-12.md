# Issue #75 — Premium native UI: evidenze per la review Owner

**Stato: `CENTROCHANGE_PREMIUM_NATIVE_UI_READY_FOR_OWNER_REVIEW` — PASS tecnico e funzionale circoscritto. Review visiva Owner ancora aperta.** PR #126 resta DRAFT; nessun merge e nessuna attività GOAL-03.

## Runtime e provenienza

- Unico progetto Docker operativo `centrochange-dev`, nove servizi; un Bench, Site `centrochange.local`, database `_4f614b4543aa5230`. Il Site e il dataset sintetico della issue #124 non sono stati resettati o riseminati.
- Immagine applicativa effettivamente servita dai sei servizi app: `sha256:bd297406bcc83aac0e50280763741b92df3387dd93799b183e4c714500e0e725` (`infra/Dockerfile.issue75`, derivata dalla base pinned della single-stack). DB e Redis restano i tre servizi tecnici della stessa stack.
- Versioni installate: Frappe/ERPNext `16.50.0` (pin `f20f92d` / `7474d9e`), Healthcare `16.6.1` (`dda107b`), Builder `1.35.1` (`37e958b`), `centrochange_core` `0.0.1`. Codice di questa revisione: branch `issue-75/tabler-navigation`, PR DRAFT #126 sopra PR #125; commit indicato nella PR.
- Le credenziali demo restano solo nel file privato Owner `/home/empv26/.local/state/centrochange-single/demo-owner.json` (`0600`). Per accedere: `ssh -N -L 8082:127.0.0.1:8082 empv26@179.198.222.100`, poi `http://127.0.0.1:8082/login`. Nessuna credenziale inclusa nelle evidenze.

## Modifiche installate

1. **Splash e identità prima del Desk.** `website_brand.context` fornisce il wordmark Centro Change al template Frappe prima di `app_include_js`. La diagnosi nel Frappe pinned ha individuato `splash_screen.html` in `desk.html` e il riuso del medesimo splash dopo il login in `login.js`; il vecchio logo appariva prima che gli script Desk potessero intervenire. Il video Chromium parte prima del login e il rilevatore di elementi visibili non registra ERPNext/Frappe/Marley. L'Administrator tecnico mantiene il Desk nativo.
2. **Stile condiviso native-first.** CSS circoscritto a `body.cc-client-desk`: palette `#12665F`, sidebar scura, superficie chiara, densità coerente per List/Form e pagine dedicate, focus e viewport mobili. Il file conserva la licenza MIT e l'attribuzione di token palette, focus e densità adattati dai CSS originali Nexus Theme v16, commit `5e6615bf759b8cae80fb52c6e4249eeb45133940`. Nexus non è installato come app. I Tabler Icons locali precedenti restano solo come icone della navigazione; nessuna classe Tabler è richiesta per il PASS.
3. **Form nativi e traduzioni.** Hook `doctype_js` per Item, Item Price, Appointment Type, CC Center Service, CC Package Template, Patient, Healthcare Practitioner, Sales Invoice, Purchase Invoice, Payment Entry e Bank Transaction. `Item` mostra per i servizi esistenti tre tab operative (Dettagli, Tariffe, Collegamenti); “Dettagli tecnici” riapre le tab e i campi originali. `Item Price` conserva prezzo, valuta, validità e regole commerciali, con accesso ai campi tecnici. I Form paziente, professionista e finanziari mantengono dati, controlli nativi e permessi; etichette e titoli cliente sono più leggibili. Traduzioni italiane aggiunte alla app, senza sostituzione di testi nel DOM come meccanismo principale.
4. **Nessun modello o backend cambiato.** Sono cambiati solo asset, hook di presentazione, traduzioni e script Form/List supportati. Nessun nuovo campo, permesso, processo contabile, logica clinica o API.

## Confronto visivo verificato

| Punto | Prima | Revisione servita |
|---|---|---|
| Splash iniziale | Logo ERPNext visibile prima della shell | Wordmark Centro Change, nessun elemento upstream visibile nel video/observer |
| Catalogo Item | 12 tab, stock/accounting/quality in primo piano | 3 tab operative, contenuti tecnici richiamabili |
| Geometria scheda Item | Sidebar tecnica nascosta ma spazio 277 px ancora riservato | Form usa la larghezza disponibile; editor contenuto nella card |
| Professionista | Heatmap “Attività” occupava la prima schermata | Dati e sedute visibili subito; heatmap non mostrata nella vista cliente |
| Tariffa | Campi stock/lotto e sidebar tecnica prioritari | Prezzo, valuta e validità in primo piano; dettagli tecnici richiamabili |
| Shell | Due layer storici in alcuni passaggi | Una sidebar e un header, stabili lungo il percorso testato |

Riferimenti: [prototipo approvato](premium-native/approved-prototype.png), [prima della scheda Servizio](premium-native/before-service-form.png), [scheda Servizio installata](premium-native/final-servizi-form.jpg), [Tariffa installata](premium-native/final-tariffe-form.jpg), [Professionista installato](premium-native/final-professionisti-form.jpg), [video Chromium dall'inizio](premium-native/final-chromium-start-to-native-forms.webm).

## Collaudo

| Controllo | Risultato |
|---|---|
| Browser reale Home → Agenda → Ricerca pazienti → Pazienti → Professionisti → Catalogo → Finanza → Report → Registro → Home, refresh/avanti-indietro, una shell, no overflow o errori JS | PASS, `infra/browser/issue75_native_first.cjs` |
| 11 aree native: elenco → scheda, stile computato, titolo, nessun logo upstream durante caricamento | PASS, `infra/browser/issue75_premium_native.cjs`, tre processi Chromium da massimo 512 MiB; 22 screenshot finali |
| Item sintetico: modifica descrizione nella UI → salva → ricarica → ripristina valore esatto → salva → elenco | PASS, `infra/browser/issue75_premium_edit_save.cjs` |
| Sette account `m/s/a/b/c/f/t`, menu per ruolo, navigazione custom/native, desktop/tablet/telefono, tastiera, nessun errore JS | PASS, `infra/browser/issue75_native_roles.cjs` |
| Nove liste native e form Patient, tablet/telefono | PASS, `infra/browser/issue75_native_surfaces_v2.cjs` |
| Administrator tecnico mantiene il Desk Frappe | PASS, `infra/browser/issue75_admin_boundary.cjs` |
| Accessi server diretti dei sette ruoli, pazienti assegnati `6/1/0`, finance/audit negati ai ruoli non autorizzati, Medical Department 403 | PASS, `infra/issue75_role_api.py` |
| Servizi HTTP/WebSocket/worker/scheduler e dati sintetici | PASS, `infra/uat_runtime_health.py` e `infra/uat_demo.py validate`; hash semantico invariato `9e1a61146ce666e50f5bf78ccd9995989dbc302e9c2dc6f6942d370583a9c09a` |
| Sintassi JS/Python e `git diff --check` | PASS |

Screenshot di percorso: [Home](premium-native/final-issue75-native-first-home.jpg), [Agenda](premium-native/final-issue75-native-first-agenda.jpg), [Ricerca pazienti](premium-native/final-issue75-native-first-ricerca-pazienti.jpg), [Pazienti](premium-native/final-issue75-native-first-pazienti.jpg), [Professionisti](premium-native/final-issue75-native-first-professionisti.jpg), [Catalogo](premium-native/final-issue75-native-first-catalogo.jpg), [Finanza](premium-native/final-issue75-native-first-finanza.jpg), [Report](premium-native/final-issue75-native-first-report.jpg), [Registro](premium-native/final-issue75-native-first-registro.jpg), [ritorno Home](premium-native/final-issue75-native-first-home-ritorno.jpg). I sette screenshot desktop sono `premium-native/final-role-{m,s,a,b,c,f,t}-desktop.png`; disponibili anche `final-role-m-tablet.png` e `final-role-m-phone.png`.

## Limiti rimasti per la review

- I nomi canonici artificiali `CC-HTTP-UAT...` restano visibili in alcuni campi editabili e riferimenti contabili dei dati demo. Titoli e voci principali usano nomi leggibili; cambiare i record sintetici esistenti richiederebbe una decisione separata sui dati.
- I Form contabili nativi espongono ancora alcuni campi tecnici upstream necessari a Finance/Commercialista. Questa revisione ne migliora lo stile e le etichette principali senza rimuovere azioni contabili. La decisione visiva su ulteriore semplificazione resta Owner.
- Il ciclo completo modifica/salva/ripristina è stato eseguito su Item; per le altre dieci aree il collaudo ha aperto lista e scheda senza modificare documenti contabili, clinici o configurazioni demo. Nessun PASS di salvataggio universale è dichiarato.
- La valutazione estetica finale e l'accettazione GOAL-02 richiedono ancora review esplicita Owner.
