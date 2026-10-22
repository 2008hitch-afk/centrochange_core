# Codex — avvio singolo Premium Frontend Goal (autorizzato Owner)

**Documento storico di avvio (21/10/2026), non riutilizzare come mandato corrente.** Il macro-goal #148 è già stato eseguito nella PR #150 e sono intervenute DECISION-062–066. Il testo seguente conserva il prompt originario della [DECISION-061](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-061-authorize-premium-react-frontend-macro-goal.md); per nuovi interventi consultare #148, #156 e le decisioni approvate applicabili. Non creare un secondo goal né dedurre un'autorizzazione runtime da questo prompt.

## Preflight CLI

- Dentro una shell **non** nel prompt Codex: `codex --version`; in Codex controllare la disponibilità effettiva di `/goal` digitando `/` e cercando il comando; la presenza potrebbe dipendere anche da versione/feature flag.
- Se `/goal` non compare, **NON aggiornare CLI/global config automaticamente**. Usare il testo come prompt Codex normale e segnalare il limite di automazione.
- Verificare `git status`, repository, HEAD, branch, modifiche non committate e PR prima di spostarsi; **non cambiare branch in modo distruttivo**. Leggere la issue #148 e la PR documentale del mandato. Per il lavoro implementativo creare un worktree/branch sicuro, preservando le linee di lavoro preesistenti.

## Prompt pronto (< 4.000 caratteri)

```text
/goal CENTROCHANGE-PREMIUM-FRONTEND-REBUILD: consegna un frontend React premium completo e realmente collaudato nel perimetro funzionale MVP autorizzato di Centro Change, con UX ispirata a Fresha e brand/logo/colori originali di centrochange.it, preservando Frappe+ERPNext+Marley+centrochange_core come backend canonico. AUTORITÀ: HC-0005 DECISION-060 (architettura), DECISION-061 (esecuzione isolata), issue centrochange_core #148 e docs/ui/PREMIUM-FRONTEND-MACRO-GOAL-v1.md nel ramo documentale PR correlato. Prima verifica repo, HEAD, git status, worktree non committati, stato di GOAL-02, PR #133/#138/#140 e Missione C #109/#112. Leggi AGENTS.md, lo stack pinned, la skill repo-local .agents/skills/centrochange-premium-ui/SKILL.md e references/; controlla la supply chain prima di ogni dipendenza/skill gratuita e non fare installer remoti. NON riprendere in parallelo la vecchia UI Frappe-first di #139: riusa solo codice/test/diagnosi validi. Esegui autonomamente un solo macro-goal con W0-W7: preflight, asset brand e licenze, contratti API/auth/CSRF/permessi, design system React riusabile, Agenda/Pazienti/operatività, Finanza/Amministrazione/Report, regressioni Playwright desktop/mobile multiruolo e sicurezza, completion report. Requisiti: Agenda come home per ruolo autorizzato, tutte le aree MVP, 11 liste + 11 schede UAT, ricerca/combobox uniforme, nessun Frappe Desk cliente, italiano globale GG/MM/AAAA e HH:mm Europe/Rome, nessuna nuova business logic, SdI/TS solo simulati. Esegui build/test solo in worktree/workspace o runtime isolati già autorizzati, con fixture sintetiche e cleanup sicuro, senza sovrascrivere dati o fare reset. Verifica browser reale, ruoli, API negative, audit, regressioni, sicurezza, performance p50/p95 su baseline documentata; non dichiarare PASS con HTTP200 o risultati di vecchie build. Produci PR DRAFT, commit/build SHA, matrice coverage, screenshot sanitizzati, licenze/lockfile, prove QA e un report finale READY_FOR_OWNER_VISUAL_UAT solo se tutto il critico è PASS; altrimenti PARTIAL/BLOCKED con gap e prossimo gate. STOP senza bypass se occorrono nuova spesa/licenza premium, nuova regola/material architecture/security change, accesso a dati veri/provider, server-clone o altre modifiche host rischiose, terza installazione o qualsiasi mutazione del DEV condiviso, merge di PR di prodotto, cutover, GOAL-03 o produzione. Continua senza microconferme sulle correzioni ordinarie autorizzate. Non dichiarare OWNER ACCEPTED.
```

## Se non è disponibile /goal

Inviare **lo stesso testo senza il prefisso `/goal`**, preceduto da:
`Esegui questa missione autorizzata come unico incarico a risultati, prosegui autonomamente per W0-W7 e fermati solo ai gate materiali previsti. Non modificare CLI o permessi per abilitare feature sperimentali.`

## Regola finale

`/goal` non concede capacità extra né autorizza attività fuori dal mandato; il prodotto deve rimanere sicuro anche dopo compaction/resume di Codex. Se la PR documentale non è ancora accessibile, attendere o usare un worktree che la contenga, **non inventare contenuti mancanti**.
