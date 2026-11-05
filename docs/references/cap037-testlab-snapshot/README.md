# CAP-037 — copia documentale e di riferimento (non operativa)

**Stato: SNAPSHOT NON AUTORIZZATO ALL'ESECUZIONE / DA REVISIONARE.**

## Provenienza e autorità

- Fonte autorevole: [`2008hitch-afk/centrochange-testlab`](https://github.com/2008hitch-afk/centrochange-testlab).
- Commit sorgente immutabile: [`4dacbbae43d6f83e91f34ee5c41118d3caa21cf6`](https://github.com/2008hitch-afk/centrochange-testlab/tree/4dacbbae43d6f83e91f34ee5c41118d3caa21cf6).
- Copia preparata per rendere consultabile a Codex la procedura CC-CAP-037 mentre la sua identità GitHub riceve HTTP 404 sul repository sorgente.
- Questa è una **copia fedele dei file elencati**, non una nuova versione approvata del protocollo, né un trasferimento di autorità o un'approvazione di esecuzione. In caso di divergenze, prevale la fonte originale; confrontare sempre revisioni e hash prima dell'uso.
- Stato della Missione B #99: manifesto `DRAFT_PROPOSED_NOT_ACTIVE`, `execution_allowed_now=false`; upgrade, build, migrate e restore **non autorizzati** da questa PR.
- La copia conserva i path originali sotto `./testlab/` così da preservare i riferimenti relativi del materiale. Non eseguire comandi senza adattamento verificato al workdir e all'ambiente isolato.

## Materiale incluso

- `testlab/probes/cap037/`: runbook, probe, Dockerfile e template relativi a CAP-037.
- `testlab/fixtures/cap037/`: override Compose CAP-037.
- `testlab/fixtures/cap040/compose.rehearsal.override.yaml`: dipendenza Compose citata nel runbook.

Non sono inclusi dati paziente, backup, dump, secret, credenziali o log runtime. `runtime.env.example` contiene soltanto segnaposto e nomi delle variabili richieste; i valori reali restano esterni a Git.

## ATTENZIONE: riferimenti storici da NON usare come target B99

- `target-manifest.v16.34.1.json` è uno **storico CAP-037** e non identifica il target della Missione B (candidato Frappe/ERPNext 16.50, da confermare con pin immutabili).
- `runtime-inputs.current-v16.32.0.json` fa riferimento a un commit storico del prodotto; non sovrascrive la baseline corrente B99.
- Non utilizzare project/site/volumi/porte o ricette hardcoded dalla procedura storica senza risoluzione esplicita delle risorse e isolamento rispetto a `centrochange-dev` (UAT RC22), laboratorio #97 e G2D.
- Il requisito CAP-037 comprende migrazione e **rollback realmente verificati su clone sintetico**, non semplice creazione di backup.
- I risultati #97/G2D conservati altrove non vengono modificati né sostituiti da questa copia.

## Registro dei blob originali (Git SHA-1)

| Percorso nella fonte | Blob SHA-1 Git |
|---|---|
| `fixtures/cap037/compose.no-build.override.yaml` | `cf242d7141bc2f452c79e3c00b62a10bbe5a03b5` |
| `fixtures/cap040/compose.rehearsal.override.yaml` | `b9fd8a116d4d77ced9cdfd6d69b4da0c9b055d54` |
| `probes/cap037/Dockerfile.provisioned-rehearsal` | `50ecb247ea5b077f3dc0b34c8ab9a75d0c6b1c94` |
| `probes/cap037/README.md` | `cc4e1927b618ea5a378037f87971fe8aa1731731` |
| `probes/cap037/provisioned-rehearsal.md` | `19025ec368f08c9bc4a4738d88232e3798bd21af` |
| `probes/cap037/rehearsal_probe.py` | `f1558e3a2b1c27bba756229479e710729ca552be` |
| `probes/cap037/result-template.json` | `9c7fc54d99d3f71bb0e81c5b24cad47d5755cace` |
| `probes/cap037/runtime-inputs.current-v16.32.0.json` | `55edea716589085f63b6758a5cb36d152a95bd7c` |
| `probes/cap037/runtime.env.example` | `f7a632cd3e75ff1a800c34a959fef3c10c9ceef0` |
| `probes/cap037/target-manifest.example.json` | `feaae3413cfcd6632397e904047541a1f66e7ba6` |
| `probes/cap037/target-manifest.v16.34.1.json` | `1df7f98cdbdda7c18be1682c116507794a7b8c7c` |

## Utilizzo da Codex

1. Leggere questo README e `testlab/probes/cap037/README.md`.
2. Verificare origine e hash dei file copiati.
3. Riconciliare parametri/commit con il manifesto B99 **senza attivarlo automaticamente**.
4. Se la PR non è mergiata, leggere la copia direttamente dal branch `docs/cap037-source-snapshot-20261008` e non presumere che sia presente su `main`.
5. Preparare soltanto la proposta di attivazione per decisione Owner separata. Non eseguire nulla per effetto della disponibilità di questi materiali.

Tracking: [centrochange_core #99](https://github.com/2008hitch-afk/centrochange_core/issues/99) e [centrochange-testlab #65](https://github.com/2008hitch-afk/centrochange-testlab/issues/65).
