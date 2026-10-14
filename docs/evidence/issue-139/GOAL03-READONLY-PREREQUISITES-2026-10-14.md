# GOAL-03 — panoramica documentale, senza avvio

Fonti lette in sola lettura: [roadmap MVP](../../MVP-GOAL-ROADMAP-v0.1.md) e issue GitHub #24. GOAL-03 è **QUEUED**. Il suo gate di ingresso richiede GOAL-02 concluso e un'evidenza UAT cliente utilizzabile. Il secondo tentativo #139 è `ROLLED_BACK`; pertanto il gate di ingresso non è soddisfatto da questo rapporto. La issue #23 appare chiusa su GitHub, mentre la roadmap la descrive ACTIVE/AUTHORIZED: questa divergenza di governance non viene risolta automaticamente.

Attività previste dalla roadmap e dalla #24, da valutare **solo dopo** il gate GOAL-02:

1. Verifica fiscale e contabile con Commercialista.
2. Scelta definitiva della route SdI; verifica soggetto trasmittente, credenziali e regole TS.
3. Decisione su migrazione dati e saldi iniziali, se applicabile.
4. Topologia e sizing del runtime di produzione.
5. Modello di configurazione e gestione segreti.
6. Backup, prova di restore, rilascio, cutover e rollback governati.
7. Review finale dei permessi di produzione.
8. Identificazione e verifica di un release candidate.
9. Classificazione dei blocker produttivi come chiusi oppure accettati esplicitamente dall'Owner.

Questa lista non autorizza produzione, dati reali, traffico SdI/TS reale, credenziali provider, modifica del server o avanzamento di stato. GOAL-03 stesso non autorizza il go-live: quello appartiene al gate separato GOAL-04.
