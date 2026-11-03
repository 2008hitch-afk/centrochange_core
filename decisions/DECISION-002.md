# DECISION-002 — Goal-Driven Factory v1.1

```yaml
decision_id: FACTORY-DECISION-002
status: APPROVATO
approved_on: '2026-10-22'
approved_by: FOUNDER
supersedes_execution_model: FACTORY-SOP-v1.0
new_version: '1.1'
technical_implementation: PROPOSED_IN_PR
```

## Motivazione commerciale

Il Founder ha confermato esplicitamente che la **velocità di consegna** è una caratteristica competitiva; Codex deve avanzare autonomamente con **Goal di valore**, non restare vincolato a micro-step e numerose approvazioni.

## Decisione

1. La SOP v1.0 resta conservata come storico; il modello operativo v1.1 è **GOAL_DRIVEN**.
2. Le dieci fasi rimangono una checklist interna di qualità, **non** dieci passaggi Founder obbligatori.
3. L'unità di controllo GitHub è il Goal; Codex decide sotto-task e vertical slices.
4. Le verifiche su risultati, test, sicurezza, review e tracce GitHub restano obbligatorie.
5. Founder interviene in punti di architettura/UX iniziali, rischio materiale, cambio scope, production/release e accettazione dove pertinente. Non approva ogni fase o micro-PR.
6. L'implementazione tecnica va collaudata con test positivi/negativi, review e pilot; niente attivazione produttiva implicita.
7. Un Goal FEATURE/MAINTENANCE può comprendere **nel solo mandato iniziale** analisi, sviluppo, CI, allineamento DEV preautorizzato con condizioni, test live, correzioni e walkthrough Owner. Non richiedere un secondo permesso per la stessa installazione DEV già esplicitamente e condizionatamente approvata.
8. **Gate DEV distinto dal mandato di sviluppo**, con ambiente/risorse precise, test e manifest, backup, restore, rollback, dati sintetici e stop su rischio materiale. Nuove migrazioni, schema/permessi, costi o produzione restano oggetto di gate separati. Merge non automatico.

9. Per i GOAL UI/API Codex svolge **UAT funzionale e visuale automatizzato** da criteri e requisiti approvati indipendenti dal codice, con browser e API reali quando autorizzati, fixture test-owned reversibili, prove screenshot e un unico report; reviewer indipendente e accettazione Owner finale sono distinti da PASS dell'agente. Nessuna sequenza di micro-collaudi manuali come default.

L'autorizzazione condizionata del DEV deve comparire sulla Issue del Goal e come `controlled_dev_deploy`; non autorizza interventi in altri GOAL/ambienti. Qualora il gate non sia stato concesso all'inizio, l'agente chiede una singola decisione consolidata.

Le autorizzazioni di progetto, la separazione dalla Discovery e i gate per dati reali e produzione non cambiano. Questa decisione **autorizza** a proporre e revisionare il motore Goal su branch/PR, non a utilizzarlo automaticamente per clienti.

### Conferma Founder: Codex responsabile del pre-UAT di ogni interfaccia (22 ottobre 2026)

Per ogni Goal con impatto UI, **Codex deve collaudare ogni interfaccia interessata** (funzioni, permessi, errori, persistenza, responsive e visual QA, regressioni), correggendo e ritestando autonomamente e consegnando un unico report con prove per interfaccia. Non ci sono approvazioni Founder ad ogni micro-step. **I Founder effettuano il controllo finale di ciascuna interfaccia**, raggruppato in un unico walkthrough per Goal, con accettazioni o richieste di correzione distinte. L'UAT di Codex è preliminare, non sostituisce l'accettazione umana. Uno stato strutturale PASS non autentica test, reviewer o Owner.
