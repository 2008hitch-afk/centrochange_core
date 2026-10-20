# Centro Change — candidato di localizzazione italiana, issue #134

## Esito e confine

**LOCALIZZAZIONE: PARTIAL fino alla verifica del candidato installato.** Il codice è versionato e il gate di installazione ha superato il dry-run; nessun nuovo deploy è stato eseguito. Non è un PASS visivo Owner. PR #143 resta DRAFT; questo lavoro dipende dalla sua HEAD `74de552e42dda437d82eae44f7b57418864102c4`.

Il DEV è rimasto sull'immagine `sha256:17380aa9aed4ee287d8c46ed1d851fe94ef42aa6586f3b9f379e0b8aff3f3602`, source `cc763958c234c9cbcc8cb46ce9f57533e47410ba`, nove servizi attivi. Fingerprint sintetico prima/dopo i controlli di sola lettura: `82dc3825e195bbcd9300f0a6787c043b9f105db324752f06ea3aae23afec7ecd`.

## Causa e soluzione

Il browser reale sul DEV ha mostrato 46 occorrenze inglesi mirate in 22 aperture Form (11 DocType × desktop/mobile), senza errori JS. Esempi: `Occupation`, `Marital Status`, `Internal`, `Charges`, `Free Followup Details`, `Immutable Incoming Source`, `Taxes and Charges`. [Inventario senza dati personali](locale-baseline-sanitized.json). L'italiano degli utenti demo è già `it` (7/7); System Settings usa data `dd/mm/yyyy`, fuso `Europe/Rome`, numeri `#.###,##`. Il Site conserva la lingua di sistema `en` per il Desk tecnico; non la cambiamo globalmente. Il login cliente e i print hanno già hook locali italiani.

La versione pinned Frappe **16.50.0** carica `translations/it.csv` e mantiene la mappa in cache `merged_translations`; il modulo `frappe.translate.clear_cache()` invalida anche `bootinfo`. Questo è stato verificato nel sorgente del container pinned. La [documentazione Frappe sulle traduzioni](https://docs.frappe.io/framework/user/en/guides/basics/translations) descrive il CSV dell'app e la necessità di aggiornare cache/build quando cambiano asset JS. Le indicazioni generiche per release diverse non sostituiscono questa verifica.

Il catalogo app comprende ora 486 traduzioni CSV univoche, inclusi campi Patient, Healthcare Practitioner, Item, fatture, pagamenti e Banca. `Charges` usa il contesto `Healthcare Practitioner` per non attribuire a tutte le voci fiscali il significato di tariffa professionale. `Total Unpaid` è reso «Totale non saldato» perché la voce può riferirsi tanto a credito quanto a debito. Nomi contabili canonici, ID, valori Select/API, XML e audit non cambiano. La UI custom ha corretto le etichette Finance nel menu/account, le date dei report e l'ora nella stampa seduta. Il Registro modifiche interpreta il datetime locale del Site come ora di Roma, evitando una conversione dipendente dal fuso del browser.

### Matrice delle superfici

| Area cliente | Meccanismo | Evidenza disponibile | Candidato live |
|---|---|---|---|
| Login e navigazione | Hook lingua esistente, etichette Desk e CSV | Login/route da precedenti sweep; nuovo codice locale testato | Da verificare |
| Paziente e Professionista | CSV Frappe con contesto; Form nativi invariati | 4 aperture Form baseline, stringhe residue individuate | Da verificare |
| Servizi, tariffe e pacchetti | CSV, incluse descrizioni avanzate Item | 8 aperture Form baseline | Da verificare |
| Fatture pazienti e fornitori | CSV contabile; `cc_finance_form.js` data italiana | 4 aperture Form baseline | Da verificare |
| Incassi, pagamenti e Banca | CSV contabile; codice funzionale intatto | 4 aperture Form baseline | Da verificare |
| Agenda e disponibilità | Nessun file Agenda modificato | Byte di tre file Agenda identici alla baseline; test esistente | Regressione visiva necessaria |
| Report e Registro modifiche | Formattazione locale esplicita, CSV già localizzati | Test date/DST e precedenti report | Da verificare |
| SdI/TS simulati, notifiche, accessi | Dizionario stati e messaggi italiani esistente; CSV nativo ampliato | Codice e precedenti controlli runtime | Da verificare errori/stati vuoti |
| Stampe/PDF/export/email demo | Hook print e CSV human-facing esistenti; ora stampa seduta corretta | Test locale del formato, evidenza funzionale precedente | Da verificare nel runtime candidato |

## Test eseguiti

- Chromium sul DEV **attualmente installato**, sola lettura: 22/22 Form desktop/mobile aperti; 0 errori JS, 46 match inglesi mirati. Sono misure della baseline, non un PASS del candidato.
- `python3 -m unittest infra.tests.test_issue134_install_gate infra.tests.test_issue134_translation_catalog infra.tests.test_issue139_locale_contract -v`: 6/6 PASS. Verificati CSV, contesto, assenza di duplicati, Agenda byte-identica, runner cache/rollback e assenza di validazioni custom palesemente inglesi.
- `node infra/tests/test_issue134_locale.cjs`: PASS su date GG/MM/AAAA, orari HH:mm, fine mese/anno e DST Europe/Rome. `node infra/tests/test_issue75_native_ux.cjs` e `node infra/tests/issue139_rome_date.cjs`: PASS.
- `sudo -n python3 -I infra/issue134_italian_install.py --dry-run`: `DRY_RUN_PASS`, 8 file applicativi cambiati, nove servizi, due sedi, mapping Compose circoscritto ai sei servizi app. Nessuna scrittura al DEV.

## Candidato e unico gate operativo

- Source applicativo immutabile: `0e6299d8a5507cc5d7dde46336870c0cd6667718`.
- Executor: `infra/issue134_italian_install.py`, SHA-256 `17683dda3ac6397c5e68e9295b36862f2fe626bed0bcfa19add79a5e13f15033`.
- Overlay Compose persistente: `infra/compose.issue134_italian.yaml`, SHA-256 `8da3285db7b15e01dadb878a0a2fc0d72bd21ee11669ee39e036117bd269cb1f`; sei immagini applicative, nessun servizio tecnico mutato.
- Procedura: nuovo gate Owner privato con `issue=134`, source ed executor SHA esatti, finestra UTC massimo 4 ore + 1 ora recupero; preflight/read-only, checkpoint, backup cifrato e verificato, immagine derivata dalla baseline, un solo update Compose, cache traduzioni mirata dopo attivazione, prove browser e fingerprint. Un solo rollback in caso critico, con invalidazione della cache traduzioni dopo ripristino. **Il presente mandato non autorizza l'esecuzione del gate**.
- Dopo autorizzazione: rieseguire sweep 11 Form desktop/mobile e ruoli cliente, errori e conferme, login, sezioni custom, PDF/stampe/export/email demo, confrontare Agenda desktop/mobile con screenshot baseline, verificare dati/permessi e chiedere review visiva Owner. Non attribuire un PASS a prove non eseguite.

## Residui noti

1. La traduzione candidata **non è ancora servita**: opzioni, messaggi nativi, rich-text placeholder e testi avanzati richiedono Chromium sul DEV aggiornato. Il CSV non dimostra da solo che ogni componente upstream usa `__()`; i punti non tradotti vanno censiti esattamente nel collaudo live.
2. Identificativi tecnici canonici restano disponibili nei dettagli nativi e nell'audit; non vengono riscritti per la localizzazione.
3. Il gate #80 richiede ancora walkthrough Owner per confermare il linguaggio delle funzioni contabili; il test automatico non sostituisce tale giudizio.

**Decisione necessaria:** autorizzare una sola installazione DEV di questo candidato esatto, con il gate privato sopra definito. Nessuna modifica a produzione, GOAL-03, dati o permessi è prevista.
