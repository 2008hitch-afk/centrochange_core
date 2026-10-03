# Centro Change Core

Repository tecnico della soluzione **Centro Change** costruita su Frappe Framework / ERPNext con app custom `centrochange_core` e sito web nell'ecosistema Frappe.

## Stato

**IMPLEMENTATION AUTHORIZED / WP-00 CLEAN RUNTIME**

Non è ancora una baseline definitiva di produzione. Le decisioni che dipendono dal runtime devono essere validate tramite spike e riportate con evidenze.

## Baseline implementativa corrente

L'implementazione HC-0005 è autorizzata. La guida canonica per il build è:

- `docs/MVP-IMPLEMENTATION-BASELINE-v0.1.md`
- `docs/MVP-IMPLEMENTATION-CAPABILITY-MAP-v0.1.yaml`
- epic GitHub #20
- primo task eseguibile: WP-00 / issue #21

Le evidenze delle 40 capability già validate vengono riusate come vincoli architetturali e regression basis; Finance/Admin / SdI / TS sono tracciati nelle nuove capability di delivery `CC-CAP-041..050`.

## Principi architetturali

1. **Native-first, non native-at-all-costs**: usare prima funzioni Frappe/ERPNext quando il fit è corretto.
2. Se il nativo introduce semantica errata, rischio permessi, fragilità o costi di upgrade, implementare in `centrochange_core`.
3. **Mai modificare direttamente il core upstream** di Frappe, ERPNext o Builder.
4. Priorità: **qualità + sicurezza + tempo di sviluppo + manutenibilità/upgrade**.
5. Le regole specifiche Centro Change devono essere versionate nel repository.
6. Dev/test usano dataset sintetici. Nessun dato cliente reale o secret in Git.

## Architettura candidata

```text
Frappe Framework
│
├── ERPNext
│   ├── anagrafiche/economia/reporting nativi dove semanticamente corretti
│   └── future capability: fatture, pagamenti reali, accounting, CRM/integrations
│
├── Frappe Builder / Website
│   └── sito pubblico branded + prenotazione iniziale
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

## Prima attività

La priorità iniziale è lo **Spike 01 — Reuse & Isolation Runtime**: verificare la foundation Frappe/ERPNext già presente sul workstation Windows/WSL2 e creare un ambiente `centrochange-dev` isolato, senza interferire con altri stack locali.

Vedi `docs/spikes/SPIKE-01-REUSE-ISOLATION.md` e le issue del repository.

## Struttura prevista

```text
centrochange_core/
├── README.md
├── AGENTS.md
├── ARCHITECTURE.md
├── SECURITY.md
├── CONTRIBUTING.md
├── docs/
│   ├── DECISIONS.md
│   ├── RUNTIME-BASELINE.md
│   └── spikes/
└── .github/
    └── PULL_REQUEST_TEMPLATE.md
```

Lo scaffold Frappe applicativo vero e proprio verrà generato/validato da Codex sul runtime compatibile durante lo Spike 01, invece di inventare a priori metadati non testati.
