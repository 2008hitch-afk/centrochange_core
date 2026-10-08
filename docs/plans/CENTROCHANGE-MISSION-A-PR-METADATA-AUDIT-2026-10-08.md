# Missione A — Primo audit metadata PR (2026-10-08)

**Status:** READ-ONLY METADATA AUDIT COMPLETATO; **CODE/DIFF AUDIT NON COMPLETATO**; merge NON autorizzato.
**Tracker:** [#95](https://github.com/2008hitch-afk/centrochange_core/issues/95) • **Plan:** [Roadmap](CENTROCHANGE-MISSION-A-AND-UNIFIED-DESK-ROADMAP-2026-10-08.md)

## Risultati osservati in GitHub

- **34/34 PR** aperte, **34/34 draft**, **34/34 metadata `mergeable=true`** al momento dell'osservazione. Questo non dimostra che siano pronte al merge, né che i permessi e i test siano sicuri.
- Catena base/head consecutiva verificata dall'ultima **#94** fino alla prima **#27 -> main**. L'ordine documentato nel piano e' la sequenza candidata bottom-up.
- `main` osservato a `a3c34a7dd52d4e0df8c5faf99d596cd76f4b383b`, segnalato non protetto.
- HEAD ultimo branch PR #94 `84e9df1ebf80aab9905cdfc08df598a07bef0f3a`; immagine prodotto RC22 si riferisce invece al **source commit** `f06acca4f6c2ac757dbd3e187709f94b18554b65`. Distinguere source version e review/docs version.
- Per HEAD #94, **0 statuses (combined status) e 0 workflow runs PR-triggered** restituiti da GitHub. Non confondere l'assenza di check GH con l'assenza dei test riportati nelle evidenze runtime; tuttavia sono da convalidare CI/release/rebuild indipendentemente.
- [#75](https://github.com/2008hitch-afk/centrochange_core/issues/75): Owner Agenda visual retest ancora PENDING. **NO MERGE #94** prima dell'esito e dell'autorizzazione.
- #94 ha **173 changed files, 39 commits** rispetto alla sua base #93: di questi 173, **133 file sotto `docs/evidence/`**, 7 `docs/uat/`, 15 `infra/`, 16 `app/`, 2 altra documentazione. Volume di diff dovuto in larga parte a evidenze, ma **scope delle 16 modifiche app deve essere revisionato prima del merge**.
- #92 ha 57 changed files e 27 commits; include local Tabler v1 e implementazione trasversale. Controllare licenze/asset, accesso Frappe nativo, sessioni e report, come gia' rilevato dagli UAT. Anche #65 (Agenda) ha numerosi commit di rifinitura; non sovrapporre in modo cieco ulteriori fix.

## Elenco completo metadata PR

Numeri di file/commit sono **relativi al diff di ciascuna PR sulla propria base**, non vanno sommati per ottenere dimensioni del prodotto. Osservazione puntuale 2026-10-08.

| Sequenza dal basso | PR | File | Commit | Metadata mergeable |
|---:|---:|---:|---:|---|
| 1 | #27 | 7 | 4 | true |
| 2 | #30 | 23 | 1 | true |
| 3 | #32 | 22 | 3 | true |
| 4 | #34 | 43 | 1 | true |
| 5 | #36 | 33 | 2 | true |
| 6 | #38 | 18 | 1 | true |
| 7 | #40 | 12 | 1 | true |
| 8 | #42 | 26 | 1 | true |
| 9 | #44 | 15 | 1 | true |
| 10 | #47 | 20 | 1 | true |
| 11 | #48 | 14 | 1 | true |
| 12 | #50 | 21 | 1 | true |
| 13 | #52 | 14 | 1 | true |
| 14 | #54 | 26 | 6 | true |
| 15 | #56 | 44 | 4 | true |
| 16 | #57 | 1 | 1 | true |
| 17 | #60 | 1 | 1 | true |
| 18 | #61 | 51 | 2 | true |
| 19 | #65 | 30 | 14 | true |
| 20 | #67 | 23 | 3 | true |
| 21 | #70 | 34 | 10 | true |
| 22 | #82 | 12 | 4 | true |
| 23 | #83 | 4 | 3 | true |
| 24 | #84 | 8 | 4 | true |
| 25 | #85 | 7 | 2 | true |
| 26 | #86 | 5 | 3 | true |
| 27 | #87 | 14 | 2 | true |
| 28 | #88 | 6 | 3 | true |
| 29 | #89 | 9 | 2 | true |
| 30 | #90 | 7 | 3 | true |
| 31 | #91 | 6 | 1 | true |
| 32 | #92 | 57 | 27 | true |
| 33 | #93 | 8 | 2 | true |
| 34 | #94 | 173 | 39 | true |

## Blocchi per la review di codice e merge (ancora da eseguire)

1. **Security:** focus PR #30/#32/#34, finance #38–#54, #93 e #94; permessi `has_permission`/`permission_query_conditions`, print/export/query/report, accesso diretto, confidenzialita' note.
2. **Runtime:** garantire no source overlay/manual patch e clean build; controllare se merge su main aziona un deployment automatico.
3. **Integrity:** confrontare app tree di `main` candidato finale con esatto git archive RC22; differenza attesa solo file evidenze/test/doc, salvo motivazioni esplicite.
4. **UAT:** non dichiarare #75 completata o passare a GOAL-03; prima retest Owner.
5. **Git stack:** provare sequenza in clone, preservando tutte le PR/commits e confronto diff prima/dopo retarget; decidere metodo di merge prima di modificare `main`.
6. **CI:** validare test su branch di integrazione pulito e documentare perche' non risultano status/workflow nel commit #94; i test manuali e runtime sono evidenza, non sostituto automatico dei gate di repo.
7. **Backup:** GitHub non e' database backup; Missione A non modifica DB. Piano di DR operativo e upgrade solo nelle successive missioni autorizzate.

## Handoff da preparare a Codex (non ancora avvio esecuzione)

Una sola missione **`integrate-stacked-prs-safely`**, con lista PR/SHA fissa, rehearsal non distruttivo, verifica dei diff, nessun `force-push`, nessun patch al runtime UAT e stop su qualunque contenuto o conflitto non previsto. **Emissione dell'incarico solo dopo approvazione Owner del piano di merge.**

**Criterio d'uscita Missione A:** audit e strategia testati per iscritto + Owner retest (#75) + decisione esplicita sul merge. Non significa GOAL-02 accepted.

## Supplemento di verifica: review GitHub campionate (2026-10-08)

Sono state lette le review PR tramite l'API GitHub per **17 PR campionate**: #27, #30, #32, #34, #38, #40, #42, #44, #47, #50, #54, #56, #61, #65, #92, #93, #94. La risposta per ognuna riporta **zero review submission registrate**. Questo non elimina le evidenze dei test, le discussioni PR o l'accettazione Owner di GOAL-01, ma conferma che **non si puo' assumere che il processo di code review GitHub sia gia' completato**. Non estrapolare a tutte le 34 PR: il controllo non e' esaustivo.

**Decisione tecnica ancora da preparare:** approvazione per una prima review aggregata del prodotto da HEAD #94 verso main o merge sequenziale delle 34 PR preservando tracciabilita'. Va simulato su clone e analizzata la parita' dei commit/finali prima di scegliere. La scelta non e' automatica e non va delegata implicitamente a Codex.
