# AGENTS.md — Centro Change

Queste istruzioni valgono per Codex e per qualsiasi agente operativo che modifica questo repository.

## Prima di sviluppare

Leggere nell'ordine:

1. `README.md`
2. `ARCHITECTURE.md`
3. `SECURITY.md`
4. `docs/DECISIONS.md`
5. `docs/RUNTIME-BASELINE.md`
6. la issue GitHub assegnata

## Ruolo operativo

Codex è il **runtime engineer / implementer**. Deve verificare sul runtime ciò che non può essere dimostrato dal solo codice o dalla documentazione.

Per ogni task:

1. leggere issue, acceptance criteria e dipendenze;
2. verificare lo stato del runtime prima di mutare;
3. creare branch dedicato;
4. implementare il minimo necessario;
5. eseguire test automatici e manuali pertinenti;
6. produrre evidenze sintetiche;
7. aprire PR collegata all'issue;
8. indicare `PASS`, `PARTIAL` o `FAIL` senza sovrastimare il risultato.

## Regole non negoziabili

- Non modificare direttamente il core di Frappe, ERPNext o Builder.
- Non patchare container running manualmente come soluzione permanente.
- Non introdurre dipendenze da altri progetti/clienti.
- È consentito riusare **pattern infrastrutturali generalizzati**, non dati, business logic o codice client-specific non autorizzato.
- Nessun secret, password, token, backup, dump DB o dato cliente reale in Git.
- DEV/test usano solo dati sintetici o esplicitamente sanitizzati.
- Ogni controllo di sicurezza critico deve essere server-side e testato anche via API/accesso diretto.
- Ogni retry o job critico deve essere progettato per idempotenza.
- Non considerare una UI nascosta come un controllo di autorizzazione.
- Non dichiarare compliance GDPR sulla sola base di controlli tecnici.

## Native-first

Per ogni requisito valutare nell'ordine:

1. funzionalità nativa Frappe/ERPNext con fit corretto;
2. estensione supportata del nativo;
3. app ufficiale Frappe pertinente;
4. custom pulito in `centrochange_core`;
5. integrazione esterna solo se necessaria.

Se il nativo introduce semantica errata, rischio di sicurezza, UX significativamente peggiore o forte upgrade risk, preferire custom pulito.

## Git workflow

- una issue per unità di lavoro;
- branch suggerito: `issue-<n>/<slug>`;
- nessun lavoro diretto su `main` dopo il bootstrap iniziale;
- PR obbligatoria;
- niente merge se gli acceptance criteria critici non hanno evidenza;
- evitare commit che mescolano refactor non richiesti e feature;
- documentare migrazioni e cambi schema.

## Evidenze minime in PR

- issue collegata;
- runtime/versioni usate;
- file/moduli cambiati;
- comandi principali eseguiti;
- test automatici;
- test manuali rilevanti;
- risultato `PASS / PARTIAL / FAIL`;
- rischi o unknown residui;
- screenshot/log sintetico solo quando utile e senza dati sensibili.

## Confine ChatGPT ↔ Codex

ChatGPT prepara architettura, issue, acceptance criteria e review.
Codex esegue runtime, implementazione e test.
GitHub è il canale di coordinamento.

Se una decisione architetturale non è ancora definita, Codex deve produrre evidenza e una **raccomandazione**, non trasformarla autonomamente in decisione finale.

## Implementation mode — HC-0005

L'implementazione del MVP Centro Change è autorizzata dal gate HC-0005 DECISION-052.

Prima di scrivere feature code, Codex deve chiudere `WP-00 / M0 — Reproducible Clean Runtime` (issue #21).

Le 40 capability storiche sono evidenza architetturale da riusare: non vanno ridiscusse da zero, ma i relativi scenari decisivi devono diventare regression test del prodotto quando pertinenti.

Le capability Finance/Admin `CC-CAP-041..050` derivano dal delivery design approvato e richiedono nuova implementazione/evidenza.
