# #79 — Autocomplete nella Agenda Frappe

**Stato: READY_FOR_OWNER_RETEST (PR DRAFT; DEV persistente non aggiornato).** La correzione è stata verificata nel browser sulla route reale applicando il solo CSS candidato alla sessione Chromium. Il DEV continua a mostrare il difetto fino a un deploy autorizzato separatamente. Nessun Owner PASS.

## Base e perimetro

- Branch: `issue-79/unified-desk-autocomplete`, da PR #127 HEAD `f0521445257a8298c35d8056c94f7a7b64254f0e` (PR #126 HEAD `dbb02b389e83f2cff0b05dde2689793797fe3e6f`, entrambe DRAFT). PR #128/#78 esclusa.
- Route verificata: `http://centrochange.local:8082/app/cc-unified-desk?cc_view=agenda`, login demo, **+ Prenota**. Risposta HTTP 200.
- Gli asset serviti `search_select.js`, `workspace.js` e `ui_v1.css` coincidono byte per byte con i sorgenti di questo branch, rispettivamente SHA-256 abbreviati `442c43c55cf79cdf`, `0278c88da67a12a5`, `80df1e9b894c8540`.
- Il socket Docker non è accessibile a questo utente; hash immagine e stato dettagliato dei container non sono stati riverificati. Nessun comando Docker mutativo è stato usato.

## Causa riprodotta

Con “Alf” la ricerca server autorizzata risponde HTTP 200; il DOM contiene l'opzione **Alfa**, `aria-expanded=true`, `.cc-options` è `display:block`. Con centro A anche “Beta” compare nel DOM. Tuttavia il browser calcola `.cc-combobox { position: static }`: il menu assoluto viene ancorato al dialogo e appare a `y=884`, mentre il dialogo termina a `y=883`. L'opzione è quindi fuori dall'area cliccabile. Non è un'assenza di dati, né un errore API o soltanto un problema di z-index.

Nel Desk risultano montati lo stylesheet circoscritto `cc-desk-scoped-workspace-css` e il CSS della Page; nessuna regola applicata al combobox. La regola relativa esisteva in `ui_v1.css` per la pagina autonoma, ma non è applicata alla superficie Desk. Il dialogo reale è un `<dialog id="modal">` senza classe `cc-modal`, perciò i selettori della pagina autonoma non definiscono il posizionamento in questa superficie.

## Correzione

In `cc_unified_desk.css` due regole, limitate a `.cc-client #modal-fields`, ancorano il combobox e il menu al campo. Restano invariati `search_select.js`, la ricerca server-side, gli ID canonici, il submit, i permessi e i dati. Nessun nuovo componente o dipendenza.

## Prove

`infra/browser/issue79_unified_autocomplete.cjs` apre la route reale. La modalità `preview` carica il CSS versionato con `page.addStyleTag()` solo nel browser; non scrive asset o database sul DEV. La modalità `live` usa gli asset serviti senza iniezione.

| Prova | Esito |
| --- | --- |
| Chromium `live`, Direzione desktop | **FAIL atteso**: `position: static` prima della correzione distribuita |
| Chromium `preview`, Direzione/Segreteria/Alfa/Beta/Gamma desktop | **PASS**: risultato visibile, hit target, selezione; Gamma senza pazienti/professionisti autorizzati |
| Chromium `preview`, Direzione mobile 390×844 | **PASS**: risultato visibile e cliccabile |
| Tastiera e stato | **PASS**: ArrowDown, Enter, Escape, blur/riapertura, ricerca case-insensitive, vuoto, risposta obsoleta scartata |
| Sicurezza e integrità | **PASS entro lo scope read-only**: Alfa non vede Zeta, Beta non vede Alfa, Gamma riceve lista vuota; selezione conserva gli ID canonici; zero POST booking, zero errori JS |
| `node --check`, `git diff --check` | **PASS** |

Output strutturato: [browser-preview.json](browser-preview.json). Screenshot sintetici: [prima desktop](before-desktop.png), [paziente desktop](preview-patient-desktop.png), [professionista desktop](preview-practitioner-desktop.png), [paziente mobile](preview-patient-mobile.png). Nella preview il menu paziente si sposta a `y≈198`, sopra gli altri campi, e `elementFromPoint()` raggiunge il pulsante dell'opzione.

Comando riproducibile (credenziali fuori Git):

```sh
CC_ISSUE79_FIXTURE=/percorso/privato/demo-owner.json \
CC_BASE_URL=http://centrochange.local:8082 \
CC_ISSUE79_ASSET_MODE=preview \
node infra/browser/issue79_unified_autocomplete.cjs
```

`CC_ISSUE79_ASSET_MODE=live` è il controllo da rieseguire **solo dopo deploy autorizzato**; oggi fallisce come baseline. Il browser locale ha usato librerie Chromium estratte in `/tmp`, senza installazione di sistema. Il Browser plugin non era disponibile.

## Prossimo gate Owner

Autorizzare separatamente il deploy del solo CSS #79 sull'unico DEV; poi eseguire il test in modalità `live` e ripetere manualmente **Agenda → + Prenota → “Alf” e “Beta” → selezione**, da desktop e mobile. Nessun deploy, restart, merge o modifica al DB è avvenuto in questa missione.
