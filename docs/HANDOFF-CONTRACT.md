# Handoff Contract — unico ingresso della Factory

La Factory **non richiede uno specifico processo Discovery**; riceve invece un trasferimento di informazioni standard approvate:

```yaml
handoff_version: '1.0'
project_id: DEMO-001
source:
  type: DISCOVERY | PRODUCT_BRIEF | OTHER
  uri: github:owner/repo/path#revision
  approval_ref: decision:source-approved
scope:
  must_have: [REQ-001]
  exclusions: []
users_roles: []
constraints: []
assumptions: []
unknowns: []
authorizations:
  architecture_planning: pending
  implementation: pending
  environment_access: pending
  production: pending
```

I valori di esempio **non autorizzano** nulla. Richiedere una fonte verificabile e decisioni autenticate secondo il sistema origine. L'handoff è il confine informativo: la Factory non altera la fonte e non reintervista automaticamente il cliente.

Quando incontra informazioni insufficienti, produce un report di differenza (cosa sappiamo / cosa manca ora) e una domanda mirata al responsabile. Il blocco è limitato al gate impattato; gli altri dati approvati non sono riscritti.

**Gate di esecuzione:** un riferimento di handoff permette solo il bootstrap di una workspace sintetica; per avviare sviluppo, accessi o release occorre autorizzazione specifica e separata.
