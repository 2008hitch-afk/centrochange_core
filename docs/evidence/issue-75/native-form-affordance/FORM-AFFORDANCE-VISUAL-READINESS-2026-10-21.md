# PR #146 — verifica grafica delle Form native

**Esito:** `READY_FOR_SINGLE_UX_DEV_DEPLOY: YES`, subordinato a un nuovo gate operativo Owner. Il candidato è versionato e verificato in anteprima browser e nel clone isolato; **non è installato** sul DEV condiviso. Questo esito riguarda solo la presentazione, non certifica salvataggi contabili né l'accettazione visiva Owner.

## Identità e perimetro

- Branch `issue-75/native-form-affordance`, PR #146 DRAFT sopra PR #145 DRAFT.
- Candidato applicativo `1f88207c6a71c4bf0252b912fe83313337cab16f`. Differenza dalla sorgente installata: `cc_premium_nexus.css` e due script di presentazione/localizzazione già preparati nella #145 (`cc_item_form.js`, `cc_patient_form.js`). Nessun cambio a DocType, ruoli, permessi, contabilità o API.
- DEV verificato in sola lettura: sorgente `e52a88a960a699b08cfad91d2b86e2fbfdcfb6ec`, immagine `sha256:6ecc23d0fe6ddc25b294d265546889aedee6049849a2cf58358f0087cb6c611e`, 9/9 servizi. Nessuna mutazione, build, cache clear o riavvio in questa missione.
- I test live applicano il CSS candidato **solo nella pagina Chromium** e confrontano la pagina servita prima e dopo; non dimostrano che il candidato sia installato sul DEV.

## Causa e correzione

Il bundle `desk.bundle.P52FIUJ5.css` di Frappe 16.50 imposta `.form-control { border: none }` dopo la vecchia regola Centro Change, che cambiava solo `border-color`. Il Form Paziente mostra quindi input vuoti con bordo computato `0px none`. Il CSS candidato imposta il bordo completo, il focus, lo stato non modificabile e l'errore con selettori limitati a `body.cc-client-desk.cc-native-view .form-page .frappe-control`. Non interviene su Agenda o sulle liste. Nel confronto live mirato, **10/10 input editabili Paziente** avevano bordo 0 px prima e **0/10** dopo, su desktop e mobile. La distinzione read-only è visibile nei Form Finance; nessun test ha tentato di salvare documenti contabili.

## Matrice visiva delle 11 route native

`PASS` indica rendering List/Form, desktop/mobile, senza icone oltre 96 px, overflow orizzontale, sovrapposizione alla sidebar o campi editabili senza bordo. `BLOCKED` indica che la Segreteria non può aprire la route; è un limite della prova live con quel ruolo, non una regressione UI. Le Form accessibili al Manager furono già provate nel clone isolato, con evidenza nel [rapporto precedente](FORM-AFFORDANCE-2026-10-21.md).

| Route | Ruolo live | Prima / causa visiva | Anteprima dopo | Esito live |
|---|---|---|---|---|
| Patient | Segreteria | 10 input editabili senza bordo nel confronto mirato | 10 bordi visibili; List/Form desktop/mobile | 4/4 PASS |
| Healthcare Practitioner | Segreteria | Route non autorizzata per questo ruolo | Form editabile già verificato nel clone Manager; nessuna modifica di permesso | 4 BLOCKED |
| Item | Segreteria | Nessuna icona gigante o sovrapposizione osservata | List/Form leggibili a entrambe le larghezze | 4/4 PASS |
| Appointment Type | Segreteria | Route non autorizzata per questo ruolo | Form editabile già verificato nel clone Manager | 4 BLOCKED |
| CC Center Service | Segreteria | Route non autorizzata per questo ruolo | Form editabile già verificato nel clone Manager | 4 BLOCKED |
| CC Package Template | Segreteria | Nessuna icona gigante o sovrapposizione osservata | List/Form leggibili a entrambe le larghezze | 4/4 PASS |
| Sales Invoice | Finance | Consultazione nativa read-only; nessun campo editabile da pretendere | Campi di sola lettura distinguibili; List/Form desktop/mobile | 4/4 PASS visivo |
| Purchase Invoice | Finance | Come sopra | Come sopra | 4/4 PASS visivo |
| Item Price | Finance | Come sopra | Come sopra | 4/4 PASS visivo |
| Payment Entry | Finance | Come sopra | Come sopra | 4/4 PASS visivo |
| Bank Transaction | Finance | Come sopra | Come sopra | 4/4 PASS visivo |

Lo sweep completo ha prodotto **32 PASS, 0 FAIL, 12 BLOCKED**. Un secondo sweep Finance dopo aver chiuso nel browser il dialogo informativo di permesso ha prodotto **20/20 PASS**. Il confronto rigoroso Paziente + Sales Invoice, che rimuove l'anteprima CSS fra uno screenshot e l'altro, ha prodotto **8/8 PASS**. Massima dimensione icona visibile: 16 px; overflow orizzontale: 0 px. Non sono stati registrati `pageerror` nei gruppi finali. Il dialogo Finance è conseguenza del guard applicativo esistente e non è stato soppresso nel prodotto.

## Evidenze visuali e regressioni

- Paziente: [prima](patient-live-form-before.png), [dopo desktop](patient-live-form-preview.png), [dopo mobile](patient-live-mobile-preview.png).
- Finance: [fattura read-only desktop](invoice-readonly-desktop-preview.png), [pagamento read-only mobile](payment-readonly-mobile-preview.png).
- [Runner ripetibile](../../../../infra/browser/issue75_native_visual_scope.cjs) (percorso repository: `infra/browser/issue75_native_visual_scope.cjs`). Risultati JSON e screenshot completi restano nell'archivio privato `~/.local/state/centrochange-single/browser-evidence/issue75-native-{visual-corrected,finance-final,comparison}-20261021/` e non contengono credenziali nei report pubblicati.
- Agenda Segreteria: confronto pixel desktop/mobile **identico** nel precedente clone/anteprima CSS; selettori CSS confinati alle Form native. Questo non sostituisce il confronto successivo al deploy. #145 resta nel delta cumulativo e richiede regressione mirata dopo installazione; la localizzazione live attuale non è attribuita al nuovo CSS.
- Test precedente nel clone: Patient compilazione → salvataggio → refresh → persistenza PASS. Form editabili Patient, Practitioner, Item, Appointment Type, Center Service e Package Template desktop/mobile: 12/12 verifiche di campi visibili. Clone eliminato, DEV invariato. Non è una nuova certificazione funzionale delle altre Form.

## Residui separati

1. Tre route native non sono verificabili con la Segreteria; serve un controllo post-installazione con il ruolo già autorizzato, senza ampliare i permessi.
2. Alcuni identificativi sintetici preesistenti restano prominenti nella Fattura di consultazione. È un limite di presentazione più ampio, non causato dal bordo degli input; non si risolve alterando documenti o contabilità in questa PR.
3. La prova CSS browser-only non verifica il bundle servito dopo l'installazione. Il gate DEV dovrà verificare hash asset, screenshot e Agenda reale.

## Singolo gate operativo richiesto

Il wrapper `infra/issue75_form_affordance_install.py` fissa sorgente, immagine base, overlay e SHA delle suite. Eredita preflight fail-closed, backup cifrato dei quattro componenti Site, checkpoint, fingerprint di dati e permessi, finestra 4h + 1h e un solo rollback. Il `--dry-run` sul DEV invariato deve essere PASS prima di creare un gate privato con identità esatta del candidato e dell'executor. Il commento PR #146 `6311746324` **non autorizza il deploy**. Richiedere una sola autorizzazione Owner per installare questo candidato cumulativo; nessun secondo tentativo automatico, merge o cambio a produzione.

Dry-run read-only del 21/10/2026: `DRY_RUN_PASS`, 9 servizi, 2 centri, 3 file applicativi nel delta, fingerprint dati `82dc3825e195bbcd9300f0a6787c043b9f105db324752f06ea3aae23afec7ecd`. SHA-256 executor `6503e7ed4b49863150cf6e4a06b0d848569c95052102264ac60abf891ffea12c`; SHA-256 overlay `1dc3d7b91d8176e48df2ae613593f2bfa41911d59a20a92882b591ec8b2bb9a9`; SHA-256 runner visivo `717d516fae83c45d36dfdde2fe43260724b9707d97e80dd341078b7753f671b8`. `node --check`, `node infra/tests/test_issue75_native_ux.cjs`, `python3 -m py_compile` e `git diff --check`: PASS.
