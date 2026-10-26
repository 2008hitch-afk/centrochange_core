# Centro Change Core

Repository tecnico della soluzione **Centro Change** costruita su Frappe Framework / ERPNext con app custom `centrochange_core` e sito web nell'ecosistema Frappe.

## Checkpoint operativo vigente — 26/10/2026 (solo fase corrente)

**Per riprendere Centro Change SENZA PERDERE IL PUNTO:** [Checkpoint AUDIT-05 → CORE #173](docs/qa/CURRENT-PHASE-AUDIT05-CORE173-2026-10-26.md), [matrice requisiti 110 ID CSV](docs/qa/FUNCTIONAL-COVERAGE-DETAIL.csv) e [matrice leggibile](docs/qa/FUNCTIONAL-COVERAGE-MATRIX.md).

- **AUDIT-05 #171:** PR #172 `DRAFT/UNMERGED` (candidato `a3e41a1`), CI verde, DEV installato **secondo report AGY**, Owner UAT mirati PASS visivi, **Owner acceptance formale ancora PENDING**. Nessun merge o produzione.
- **CORE #173:** requisito «Chiudi la mia giornata» approvato, **non ancora implementato al checkpoint**; chiusura arretrati autonoma del professionista **senza sblocco Direzione**, mantenendo audit e controlli server-side. [Mandato AGY registrato](https://github.com/2008hitch-afk/centrochange_core/issues/173#issuecomment-6424378839), da eseguire sequenzialmente dopo il gate #171 e con nuova autorizzazione DEV dedicata.
- **Matrice:** 110 ID invariati; sulla PR #172 `12 PASS / 60 PARTIAL / 27 NOT_TESTED / 11 BLOCKED` **tecnici**, non accettazione Owner. I GOAL successivi non sono trattati nel presente checkpoint.

Il seguito del README contiene la **baseline storica MVP / GOAL-02 di inizio ottobre**, da consultare come fonte storica e non sostitutiva del checkpoint corrente.

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
