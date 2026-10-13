# Issue #75 — Correzione visiva Tabler, pronta per nuovo esame Owner

**Esito tecnico: `CENTROCHANGE_TABLER_UI_READY_FOR_OWNER_RETEST`.** La review visiva Owner della versione precedente della PR #126 è **NOT ACCEPTED — CORRECTION REQUIRED**; questo rapporto documenta la correzione e il collaudo, non attribuisce `OWNER VISUAL PASS` né chiude GOAL-02. Branch `issue-75/tabler-navigation`, PR #126 DRAFT stacked sulla #125. Nessun merge.

## Diagnosi della versione realmente servita

La HEAD di partenza era `4e1c6aa0a00647562627fc515c49f15b7b3eb647`, senza modifiche locali o divergenza remota; l'immagine attiva iniziale era `sha256:64411134578d655f7829495959693c6ea12b53e25a54050215edd607029aaaf8`. La versione precedente importava Tabler 1.6.1 a bassa priorità, lasciando filtri, tabelle, form e toolbar nativi con aspetto Frappe. Il test precedente controllava principalmente la presenza della sidebar dopo navigazioni fresche, non la geometria e la resa delle transizioni.

Una sequenza Chromium Home → Agenda → Pazienti → Professionisti → Catalogo ha riprodotto uno scarto deterministico: entrando in Catalogo Frappe attivava il dock tecnico `#desk-dock` largo **57 px**, spostando `.main-section` da x=0 a x=57; sidebar, navbar e contenuto finivano rispettivamente a x=0, x=305 e x=305. Un semplice reset del margine di `.main-section` non bastava: il dock partecipava al flex del body. La shell cliente ora nasconde il dock solo per `body.cc-client-desk`, mantenendo intatta l'interfaccia Administrator. Dopo la correzione, su Catalogo le coordinate sono x=0, x=248 e x=248.

I sorgenti dell'immagine finale e gli asset serviti hanno SHA-256 identici: `cc_desk_client.js` `f241bf884d0b315126f8610dba741d82ffa6b6601e112489aba5e6d2a5db5d39`, `cc_desk_client.css` `64ca4c9accbfa76a0b2e9d40afae9d7e1c814820e3f26638a601b5bbf4548adf`. `sites/assets/assets.json` è stato rigenerato da `bench build` e la cache Frappe è stata svuotata dopo il deploy. Il codice applicativo Centro Change non registra un service worker; i test sono eseguiti con contesti Chromium nuovi. Il menu orizzontale osservato nella sessione Owner precedente non è stato riprodotto in questi nuovi contesti; il test corretto intercetta anche la sua eventuale comparsa durante le transizioni. Non si attribuisce la discrepanza soltanto alla cache.

## Correzione distribuita

La shell cliente usa le classi Tabler `.page`, `.navbar.navbar-vertical`, `.page-wrapper`, `.page-header` e `.page-body`, con una sola sidebar, navbar essenziale e icone locali. La shell viene ricreata se Frappe la sostituisce durante un cambio rotta; l'offset del dock è eliminato; la larghezza desktop della sidebar resta 248 px, con modalità a icone volontaria e menu mobile. Le viste native sono adattate senza modificare Frappe: superfici, intestazioni, filtri, campi, righe, stati, paginazione e moduli seguono i token Tabler. Il nome leggibile è primario nelle liste; gli ID canonici restano in link, attributi e titoli. Etichette e stati comuni sono resi in italiano in sola presentazione.

Agenda, Finanza, Report e Home condividono spaziature, card, filtri, tipografia e colori. I breadcrumb di navigazione globale ripetuti nei report sono rimossi perché le destinazioni restano nella sidebar. Il calendario settimanale mantiene sette intestazioni giorno e sette colonne. Nessun cambiamento a schema, dati, API, permessi, contabilità, prenotazioni, note cliniche, SdI/TS o workflow.

Immagine finale installata: **`sha256:d7fde9fc7211359df2c127469bb3c3d9aa83f4d317501f4f1fc3b07a79f34fc0`**. Solo i sei servizi applicativi del progetto `centrochange-dev` sono stati ricreati; DB e Redis e i loro volumi sono rimasti. Un solo Bench logico, Site `centrochange.local`, DB `_4f614b4543aa5230`, nove servizi attivi. Frappe/ERPNext 16.50.0, Builder 1.35.1, Healthcare 16.6.1 e Tabler Core 1.6.1 invariati.

## Collaudo

- `infra/browser/issue75_visual_retest.cjs`: **PASS** Home → Agenda → Pazienti → Professionisti → Catalogo → Finanza → Report → Home nella sessione Chromium autenticata. Verifica geometria sidebar/navbar/contenuto, assenza di dock/sidebar nativa/barra orizzontale/branding visibile, Tabler caricato e stili computati, righe e intestazioni native, assenza di overflow, sette colonne Agenda, indietro/avanti/refresh e zero errori JavaScript. Osservatore DOM registra eventuale chrome upstream visibile durante le transizioni. Il browser QA rimane nel limite di 512 MiB; Chromium viene riciclato dopo sei screenshot preservando cookie e localStorage della stessa sessione.
- `infra/browser/issue75_native_surfaces.cjs`: **PASS** nove liste native (Pazienti, Professionisti, Servizi, Tariffe, fatture pazienti/professionisti, Incassi, banca, Registro modifiche), form Patient e layout tablet/telefono senza overflow; menu mobile apribile.
- `infra/browser/issue75_navigation.cjs`: **PASS 7/7** account demo m, s, a, b, c, f, t su desktop, tablet e telefono; menu per ruolo, links, modalità compatta, tastiera e zero errori JavaScript.
- `infra/browser/issue75_six.cjs`: **PASS 6/6** sezioni principali con dati demo visibili; zero errori JavaScript.
- `infra/issue75_role_api.py`: **PASS** accessi diretti server-side dei sette ruoli, inclusi pazienti A/B/C 6/1/0 e divieti finance/audit. `infra/uat_runtime_health.py`: **PASS**, nove servizi, HTTP/asset, WebSocket, worker e scheduler. `infra/uat_demo.py validate`: **PASS**, hash semantico invariato `9e1a61146ce666e50f5bf78ccd9995989dbc302e9c2dc6f6942d370583a9c09a`.
- `node --check` sugli script, `git diff --check` e SHA-256 sorgente/asset nell'immagine: **PASS**.

Screenshot reali della sequenza sono in [correction-screenshots](correction-screenshots/) con prefisso `issue75-correction-` (`home`, `agenda`, `pazienti`, `professionisti`, `catalogo`, `finanza`, `report`, `home-ritorno`). Nella stessa directory ci sono le nove liste native, il form Patient, tablet e telefono, screenshot con dati nelle sezioni Agenda/Finanza/Report e i JSON di misure browser. Le immagini contengono soltanto dati demo sintetici.

## Accesso e residui

Accesso Owner invariato: `ssh -N -L 8082:127.0.0.1:8082 empv26@179.198.222.100`, poi `http://127.0.0.1:8082/login`. Credenziali solo nel file privato 0600 `/home/empv26/.local/state/centrochange-single/demo-owner.json`; usare `users.m` per la Direzione. Nessun secret in GitHub. L'ambiente DEV è persistente e non ha scadenza automatica.

Residui precisi per la review Owner: i valori **editabili** dei record nativi conservano alcuni identificativi demo (`CC-HTTP-UAT...`) e il valore canonico Frappe Gender `Female`; non sono riscritti perché sono dati/Link, non etichette di presentazione. I nomi visibili in titoli, liste e pannelli sono resi leggibili; ID e valori tecnici restano disponibili dove servono alla tracciabilità. I test non sostituiscono il giudizio visivo Owner sul risultato. Nessuna final acceptance #75/GOAL-02 è dichiarata.
