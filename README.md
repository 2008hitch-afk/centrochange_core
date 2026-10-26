# Centro Change Core

Repository tecnico della soluzione **Centro Change** costruita su Frappe Framework / ERPNext con app custom `centrochange_core` e sito web nell'ecosistema Frappe.

## FASE ATTIVA / RIPRESA OBBLIGATORIA (26/10/2026)

**PUNTO DI INGRESSO UNICO:** [REGISTRO OPERATIVO — AUDIT e CORE attivi](docs/qa/ACTIVE-GOAL-ROUTER.md). Prima di prendere decisioni, leggere questo indice e verificare live **Issue #171, #173 e PR #172, #175, #174**. Non partire dalle roadmap datate, da una vecchia chat o dal paragrafo storico sotto.

**Percorso attuale (SOP v1.1 GOAL-DRIVEN, un'area alla volta):**

- **AUDIT-03 Agenda:** accettazione Owner precedente registrata.
- **AUDIT-04 Pazienti #167:** CLOSED / Owner accettato.
- **AUDIT-05 Professionisti #171:** **OWNER_ACCEPTED_SCOPED** ([gate](https://github.com/2008hitch-afk/centrochange_core/issues/171#issuecomment-6427680735)); PR #172 **DRAFT/UNMERGED**, non ancora consolidata su `main`.
- **CORE #173 «Chiudi la mia giornata» e recupero autonomo arretrati:** **UNITÀ CORRENTE**. PR #175 **DRAFT/UNMERGED**, ultimo DEV `d500fff` installato **secondo AGY**. Owner UAT-173-01..06 svolte; 2 correzioni UX + audit post-save **solo lettura** affidati ad AGY tramite [mandato unico vigente](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428463645). **Owner acceptance CORE #173 PENDING**. **NOVITÀ 26/10:** [Owner ha autorizzato condizionatamente il gate DEV per sola candidata `500c882`](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6428982304): prima dell'installazione devono risultare PASS test/reviewer/backup nuovo+restore isolato/identità+fingerprint+rollback. **Non è stata attestata alcuna installazione della nuova immagine**; un fallimento impone STOP. Nessun merge o produzione.
- **AUDIT-06 Servizi/catalogo/prezzi/disponibilità:** **pianificato** in #171, NON avviato/autorizzato. **AUDIT-07+**: non ancora definiti e autorizzati in una sequenza canonica; non inventarli.

**Attenzione alla numerazione:** `AUDIT-05` del flusso professionisti **non** equivale al `GOAL-05 Delivery Closure` nella [roadmap MVP storica del 03/10/2026](docs/MVP-GOAL-ROADMAP-v0.1.md). Tale documento NON è il dispatcher dell'attività corrente. Ogni ripresa deve usare l'unità con **nome + issue**, mai solo un numero.

**Documentazione attuale:** [checkpoint dettagliato della fase](docs/qa/CURRENT-PHASE-AUDIT05-CORE173-2026-10-26.md), [matrice 110 requisiti CSV](docs/qa/FUNCTIONAL-COVERAGE-DETAIL.csv), [riepilogo requisiti](docs/qa/FUNCTIONAL-COVERAGE-MATRIX.md). **Tutte le modifiche documentali in PR #174 sono DRAFT/UNMERGED** e non sono ancora la versione `main`; non confondere gli stati di due branch.

**Stop gates:** nessun altro AUDIT/GOAL, merge, produzione, variazione credenziali, DocPerm, schema o dati storici senza decisione pertinente Owner. `CI PASS` ≠ `DEV INSTALLED` ≠ `OWNER ACCEPTED` ≠ `MERGED`.

---

## Stato storico MVP (fotografia precedente al checkpoint attuale)

**GOAL-01 OWNER_ACCEPTED / DEV PASS — GOAL-02 TECHNICAL DONE / UAT READY**

Non è ancora una baseline definitiva di produzione. Le decisioni che dipendono dal runtime devono essere validate tramite spike e riportate con evidenze.

Candidate **goal02-20261005-rc1**: [Completion Report](docs/GOAL-02-COMPLETION-REPORT-2026-10-05.md), [Client Validation Guide](docs/uat/CLIENT-VALIDATION-GUIDE.md), [UAT Evidence Package](docs/uat/UAT-EVIDENCE-PACKAGE.md). UAT cliente e accettazione Owner restano da eseguire.

## Baseline storica MVP (non sostituisce il checkpoint in alto)

L'implementazione HC-0005 è autorizzata. La guida canonica per il build è:

- `docs/MVP-GOAL-ROADMAP-v0.1.md`
- `docs/MVP-IMPLEMENTATION-BASELINE-v0.1.md`
- `docs/MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml`
- macro-goal corrente: GOAL-02 / issue #23, HC-0005 DECISION-056 (baseline accettata DECISION-055)
- implementation epic #20
- WP-00 e wave operative/Finance sullo stack draft #27–#52; verifica integrata WP-09 #53 / PR #54 e delta correttivo DECISION-054 #55

Le evidenze delle 40 capability già validate vengono riusate come vincoli architetturali e regression basis; Finance/Admin / SdI / TS sono tracciati nelle nuove capability di delivery `CC-CAP-041..050`.

## Principi architetturali

1. **Native-first, non native-at-all-costs**: usare prima funzioni Frappe/ERPNext quando il fit è corretto.
2. Se il nativo introduce semantica errata, rischio permessi, fragilità o costi di upgrade, implementare in `centrochange_core`.
3. **Mai modificare direttamente il core upstream** di Frappe, ERPNext o Builder.
4. Priorità: **qualità + sicurezza + tempo di sviluppo + manutenibilità/upgrade**.
5. Le regole specifiche Centro Change devono essere versionate nel repository.
6. Dev/test usano dataset sintetici. Nessun dato cliente reale o secret in Git.

## Architettura implementata in DEV

```text
Frappe Framework
│
├── ERPNext
│   ├── anagrafiche/economia/reporting nativi dove semanticamente corretti
│   └── Sales Invoice, Purchase Invoice, Payment Entry, Bank Transaction, GL e Payment Ledger
│
├── Frappe Builder / Website
│   └── Website autenticato + primo incontro sintetico; sito branded differito
│
└── centrochange_core
    ├── DocTypes specifici
    ├── business rules
    ├── permission logic
    ├── scheduler/background jobs
    ├── report custom
    ├── web/API endpoints
    └── automated tests
```

## Modello operativo

```text
ChatGPT → issue/spec/acceptance criteria → GitHub → Codex → runtime/code/test/PR → GitHub → ChatGPT review
```

- **ChatGPT**: architect, product/requirements reviewer, issue/AC, PR review.
- **Codex**: runtime engineer, implementer, website developer, test executor.
- **GitHub**: source of truth tecnico e coordination layer.

ChatGPT non deve dichiarare `PASS` su comportamento runtime senza evidenza prodotta da Codex.

## Uso e verifica DEV

Il bootstrap versionato è in `infra/compose.yaml`; `infra/compose.dev.yaml` è un overlay di sviluppo. Il candidato riproducibile usa l’immagine costruita da Git, senza overlay. Configurazione e credenziali locali restano fuori Git; vedere `infra/README.md`.

- `/centrochange`: agenda, prenotazione/spostamento/cancellazione, chiusura, note, storico paziente, pacchetti, disponibilità e report; segreteria/Management creano identità sintetiche e assegnazioni esplicite.
- `/finanza`: documenti contabili nativi, XML passivi, riconciliazione, compensi parametrici, coda amministrativa, report e adapter SdI/TS simulati. Accountant in sola lettura.
- `/primo_incontro`: ingresso pubblico limitato ai professionisti configurati Marco/Francesca.
- Desk nativo e API protette completano le azioni amministrative; le autorizzazioni sono server-side.

```sh
python3 infra/runtime_acceptance.py --env-file /percorso/esterno/runtime.env --snapshot /tmp/cc-runtime.json
python3 infra/image_acceptance.py --source-ref ba45816
python3 infra/integrated_acceptance.py --env-file /percorso/esterno/runtime.env --output-dir /tmp/cc-integrated
python3 infra/dev_backup.py --destination /tmp/cc-dev-backups
```

Eseguire con accesso Docker e in sequenza sul solo ambiente DEV sintetico. Le fixture HTTP committano esclusivamente dati sintetici e li eliminano verificando la proprietà esatta; le prove dirette usano rollback. Gli output temporanei e le credenziali browser restano fuori Git.

[Report GOAL-01](docs/MVP-GOAL-COMPLETION-REPORT-2026-10-05.md) e [prova WP-09](docs/evidence/WP-09-2026-10-05.md) riportano lo stato finale e i limiti. Compenso per seduta svolta ma non incassata: DECISION-054, soglia esplicita per professionista e conteggio per paziente/professionista; tariffa alla data di prenotazione con snapshot immutabile; esattamente 48h è puntuale. Nessun provider o traffico SdI/TS reale. UAT e produzione richiedono i gate della roadmap.
