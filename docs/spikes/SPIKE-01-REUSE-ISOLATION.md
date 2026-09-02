# Spike 01 — Reuse & Isolation Runtime Frappe/ERPNext/Builder

## Obiettivo

Verificare la foundation Frappe/ERPNext già presente sul workstation Windows/WSL2 usato da Codex e creare un ambiente **Centro Change DEV isolato e parallelo**, senza modificare o interferire con altri stack locali.

Non partire dall'ipotesi di installazione da zero. Prima censire il runtime reale e riusare solo ciò che migliora qualità, sicurezza, tempo di sviluppo e manutenibilità.

## Ipotesi candidata

```text
Windows
└── WSL2 / Docker Engine esistente
    ├── altri stack locali       [NON TOCCARE]
    └── centrochange-dev         [NUOVO COMPOSE PROJECT ISOLATO]
        ├── DB dedicato
        ├── Redis dedicato
        ├── site volume dedicato
        ├── network dedicata
        ├── Frappe
        ├── ERPNext
        ├── Builder
        └── centrochange_core
```

## Attività Codex

1. Censire:
   - WSL2 distro;
   - Docker/Compose;
   - container/stack esistenti;
   - porte;
   - volumi/network;
   - versioni live Frappe/ERPNext/MariaDB/Redis;
   - risorse host disponibili.

2. Non fermare, migrare, ricreare o aggiornare altri stack per eseguire questo spike.

3. Riutilizzare pattern infrastrutturali già collaudati sul workstation, evitando dipendenze da app, dati o componenti client-specific di altri progetti.

4. Creare `centrochange-dev` con:
   - Compose project dedicato;
   - DB dedicato;
   - Redis dedicato;
   - site volume dedicato;
   - network dedicata;
   - porta localhost distinta;
   - secrets/config fuori da Git;
   - dataset sintetico.

5. Creare image Centro Change separata contenente la baseline candidata:
   - Frappe;
   - ERPNext;
   - Builder;
   - `centrochange_core`.

6. Generare/validare lo scaffold reale della Frappe app `centrochange_core` sul runtime compatibile. Se il repository necessita di riorganizzazione per diventare installabile come Frappe app, farlo in branch/PR senza perdere la documentazione di bootstrap.

7. Marley Health non va assunto come dipendenza definitiva; sarà oggetto dello Spike 02.

8. Verificare:
   - site bootstrap;
   - ERPNext install;
   - Builder install;
   - `centrochange_core` install;
   - migrate;
   - build assets;
   - backend/frontend/websocket;
   - worker;
   - scheduler;
   - Desk login;
   - website;
   - restart;
   - bootstrap ripetibile.

9. Provare non-interferenza: start/stop/rebuild Centro Change non deve produrre effetti sugli altri stack locali.

10. Aggiornare `docs/RUNTIME-BASELINE.md` con evidenza reale.

## Acceptance criteria

- runtime host censito;
- versioni live documentate;
- `centrochange-dev` isolato e ripetibile;
- DB/Redis/sites/network distinti;
- image Centro Change indipendente da app di altri progetti;
- `centrochange_core` installabile;
- Builder operativo;
- Desk/website operativi;
- worker/scheduler operativi;
- nessuna regressione/interferenza osservata sugli altri stack;
- nessuna modifica core upstream;
- nessun secret/dato reale in Git;
- evidenza runtime in issue/PR;
- esito `PASS / PARTIAL / FAIL`.

## Output richiesto

- inventario runtime;
- matrice versioni live → baseline proposta;
- schema isolamento;
- bootstrap commands;
- porte/naming;
- log sintetico test;
- non-regression evidence;
- proposta baseline esatta per Spike 02.
