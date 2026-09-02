# Runtime Baseline — Centro Change

**Stato:** DA COMPILARE DA CODEX DURANTE SPIKE 01

Questo file deve essere aggiornato solo con evidenza runtime reale.

## Host

- OS host: `TBD`
- WSL2 distro: `TBD`
- Docker Engine/Desktop: `TBD`
- Docker Compose: `TBD`
- CPU/RAM disponibili: `TBD`

## Stack live rilevato

| Componente | Versione runtime live | Fonte/comando | Note |
|---|---|---|---|
| Frappe | TBD | TBD | |
| ERPNext | TBD | TBD | |
| Builder | TBD | TBD | |
| MariaDB | TBD | TBD | |
| Redis | TBD | TBD | |
| Python | TBD | TBD | |
| Node | TBD | TBD | |

## Baseline Centro Change proposta

| Componente | Versione/tag proposta | Motivo | Stato |
|---|---|---|---|
| Frappe | TBD | | RUNTIME VALIDATION REQUIRED |
| ERPNext | TBD | | RUNTIME VALIDATION REQUIRED |
| Builder | TBD | | RUNTIME VALIDATION REQUIRED |
| centrochange_core | repository current | app custom | RUNTIME VALIDATION REQUIRED |
| Marley Health | TBD / non installato baseline | Spike 02 | OPEN |

## Isolamento ambiente

- Compose project: `TBD`
- Site name: `TBD`
- HTTP localhost port: `TBD`
- DB volume: `TBD`
- sites volume: `TBD`
- Redis volume/network: `TBD`
- network: `TBD`
- secret env path esterno a Git: `TBD`

## Non interferenza

Codex deve registrare prova che start/stop/rebuild di Centro Change non modifica o interrompe gli altri stack locali.

- baseline altri stack prima: `TBD`
- test Centro Change: `TBD`
- baseline altri stack dopo: `TBD`
- risultato: `PASS / PARTIAL / FAIL`

## Bootstrap ripetibile

Comandi/procedura finale:

```text
TBD by Codex
```

## Evidenze

- issue: `TBD`
- PR: `TBD`
- test: `TBD`
- log sintetico: `TBD`
- rischi residui: `TBD`

## Decisione proposta dopo Spike 01

`TBD — Codex deve proporre la baseline esatta, senza dichiararla definitiva autonomamente.`
