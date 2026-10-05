# Runtime Baseline — Centro Change

> Baseline corrente GOAL-01: Frappe 16.31.0 / ERPNext 16.32.0 / Builder 1.33.0 / Marley Healthcare 16.5.2 e app Centro Change implementata. Pin e bootstrap sono in `infra/Dockerfile` e `infra/compose.yaml`; final immutable acceptance **PASS**, fresh/recreate and complete regression, in [WP-09](evidence/WP-09-2026-10-05.md). Le sezioni seguenti conservano le evidenze storiche degli spike e non descrivono lo stato corrente delle feature.

**Stato:** SPIKE 01 VALIDATED LOCALLY — proposta soggetta a architecture review.

Evidenze raccolte il 2026-09-02 sul workstation reale. Il nuovo site contiene solo metadati standard e dati sintetici, mai dati cliente.

## Host

- Host: Windows 10 Pro build `26200`, 24 logical processor, 15.9 GiB RAM.
- WSL2 kernel: `6.6.87.2-microsoft-standard-WSL2`.
- Docker runtime: `Barcicletta-Ubuntu`, Ubuntu `24.04.4 LTS`; Engine `29.7.2`, Compose `v5.4.0`.
- Clone operativo: `/home/barcicletta/src/centrochange_core`.
- `Ubuntu-24.04` (Ubuntu `24.04.3 LTS`) non ha Docker integration abilitata.
- Risorse WSL osservate: 24 vCPU, 7.7 GiB RAM, 2.0 GiB swap.

## Stack live rilevato

| Componente | Contabilita_Barci live | Centro Change live | Fonte |
|---|---:|---:|---|
| Frappe | 16.31.0 | 16.31.0 | `bench version` |
| ERPNext | 16.32.0 | 16.32.0 | `bench version` |
| Builder | non installato | tag `v1.33.0`, commit `41987c0` | `bench version` |
| MariaDB | 11.8.8 | 11.8.8 | runtime/image |
| Redis | 8.6.5 | 8.6.5 | runtime/image |
| Python | 3.14.2 | 3.14.2 | runtime |
| Node | 24.12.0 | 24.12.0 | runtime base image |

Da Contabilita_Barci è stato riusato soltanto il pattern Compose: configuratore one-shot, servizi backend/frontend/websocket, due Redis, queue e scheduler. Non sono stati riusati image, app, mount, dati, Neo4j, variabili o secret Barcicletta.

## Baseline Centro Change proposta

| Componente | Versione/tag | Stato |
|---|---|---|
| base image | `frappe/erpnext:v16.32.0@sha256:481168fa7ba34bb9803e80139dff6df80bc161352cc7b478ae90b0c0da814f90` | VALIDATED LOCALLY |
| Frappe / ERPNext | 16.31.0 / 16.32.0 | VALIDATED LOCALLY |
| MariaDB | `11.8.8@sha256:24e76fcec8c003a0362d0dd53f4806e7e79458d7fdeaf47437760e19496f5a9c` | VALIDATED LOCALLY |
| Redis | `8.6.5-alpine@sha256:cd218f4b106a332c5c992e38a9480bfb9d7e9f8f7b0ec9a0023bfa36d9a408f9` | VALIDATED LOCALLY |
| Builder | tag `v1.33.0`, commit `41987c064da4650e6901b5da82b7c76add452ebf` | VALIDATED LOCALLY |
| centrochange_core | 0.0.1 scaffold `bench new-app` | VALIDATED LOCALLY |
| Marley Health | non installato | OPEN — Spike 02 |

## Policy di pinning e upgrade

Le image runtime sono pin `tag@sha256:digest`; Builder è recuperato esclusivamente dal tag ufficiale `v1.33.0` e il Docker build termina in errore se il commit non coincide esattamente con `41987c064da4650e6901b5da82b7c76add452ebf`. Non esiste tracking o auto-update di `master`, tag o digest. Ogni upgrade richiede una nuova PR, modifica intenzionale dei pin e test runtime completi.

## Isolamento ambiente

```text
Docker Engine (Barcicletta-Ubuntu)
├── barcicletta-dev / barcicletta-shadow   [immutati; porte 8080 / 8081]
└── centrochange-dev
    ├── image: centrochange-dev:frappe-v16.32.0
    ├── site: centrochange.local; frontend: 127.0.0.1:8082
    ├── network: centrochange-dev-net
    ├── volumes: centrochange-dev-db-data, centrochange-dev-sites
    └── Redis: centrochange-dev-redis-cache-data, centrochange-dev-redis-queue-data
```

DB e Redis non espongono porte host. Le credenziali locali sono esterne a Git in `~/.config/centrochange-dev/runtime.env` (0600); nel repository resta solo `infra/runtime.env.example` con placeholder.

## Bootstrap ripetibile

```text
cd /home/barcicletta/src/centrochange_core/infra
mkdir -p ~/.config/centrochange-dev && chmod 700 ~/.config/centrochange-dev
cp runtime.env.example ~/.config/centrochange-dev/runtime.env
chmod 600 ~/.config/centrochange-dev/runtime.env
# sostituire placeholder con secret locali non versionati
docker compose --env-file ~/.config/centrochange-dev/runtime.env up -d --build
curl -fsS http://127.0.0.1:8082/api/method/ping
```

Il configuratore crea il site se assente, installa ERPNext/Builder/app, esegue `migrate` e abilita lo scheduler. Un eventuale reset DEV è limitato a `centrochange-dev-*`: `docker compose --env-file … down --volumes`; mai applicarlo ai progetti Barcicletta.

## Evidenze e test

- rebuild hardening image indipendente: `sha256:3b2af1e8e826c3291a48de35fb1b514b09f331504d4034d61b1e22f060ef92c3`;
- il build ha clonato Builder dal tag `v1.33.0` e ha verificato lo SHA `41987c064da4650e6901b5da82b7c76add452ebf`;
- configurator: exit code `0`; app installate `frappe`, `erpnext`, `builder`, `centrochange_core`;
- `GET /api/method/ping` e `/login`: `200`;
- backend, frontend, websocket, queue-short, queue-long, scheduler: `running`;
- `bench doctor`: 2 worker online e scheduler abilitato;
- restart completo Centro Change: ping `200`;
- network e sites volume sono `centrochange-dev-*`, separati da `barcicletta-dev_*` e `barcicletta-shadow_*`;
- prima/dopo i test, tutti i container Barcicletta DEV/SHADOW osservati erano `Up`, senza restart o comandi rivolti a loro.

## Decisione proposta dopo Spike 01

Proporre allo Spike 02 la baseline pinata documentata sopra: Frappe 16.31.0, ERPNext 16.32.0, MariaDB 11.8.8, Redis 8.6.5, Compose `centrochange-dev` e Builder `v1.33.0` / `41987c0`.
