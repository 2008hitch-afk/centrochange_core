# GOAL-02 — ricognizione funzionale dopo HC-0005 DECISION-057

**Esito: `PARTIAL — FUNCTIONAL EVIDENCE GATE PENDING`.** Nessun nuovo difetto di prodotto funzionale dimostrato da questa ricognizione. Un difetto concreto del fixture impediva la suite generale di sicurezza sul Site persistente; la correzione è versionata ma **non distribuita né collaudata sul runtime** per il divieto di nuovi interventi server. Non equivale a GOAL-02 Owner PASS.

## Autorità e baseline controllata

- Fonte cliente: `hitch-client-discovery/clients/HC-0005/CLIENT-CONTEXT-MANIFEST.yaml`, `delivery/IMPLEMENTATION-001.yaml`, `decisions/DECISION-057-accept-ui-draft-and-defer-final-polish.md` letti da GitHub il 13 ottobre 2026. GOAL-02 resta `AUTHORIZED_ACTIVE` nel manifest; issue #23 è chiusa **tecnicamente** dal 5 ottobre. Il disallineamento formale non conferisce accettazione Owner.
- Roadmap `docs/MVP-GOAL-ROADMAP-v0.1.md`: candidate UAT riproducibile, regressione critica, permessi/audit, limitazioni ed evidenza. `docs/GOAL-02-COMPLETION-REPORT-2026-10-05.md` dichiara il gate tecnico della vecchia candidate, con UAT/Owner ancora pendenti. Il backlog del 7 ottobre e le issue aggiornate prevalgono sulle frasi storiche del report.
- Issue #109 sospesa, PR #112 DRAFT; niente R15, ripresa Missione C, promozione della UI come definitiva o modifica della webapp primaria. PR #126 è una revisione UI tecnica DRAFT, non accettazione finale.
- Attuale unico DEV: report #124 `CLEAN_SINGLE_STACK_DEV_READY` documenta Frappe/ERPNext 16.50.0, Healthcare 16.6.1, Builder 1.35.1, un Site/DB e dati sintetici. La sua prova Chromium copre sei sezioni e la prova HTTP copre un sottoinsieme dei permessi. Non trasferiamo automaticamente i PASS completi della precedente RC22/16.31–16.32 al nuovo Site/16.50.

## Gap funzionali e stato dimostrato

| Priorità | Requisito/issue | Evidenza corrente | Residuo |
|---|---|---|---|
| 1 | Sicurezza e regressione dell'unico DEV (#77, #124) | Sette ruoli e HTTP diretto mirato PASS nel report #124. Suite `infra/security_acceptance.py --with-booking --with-operations` fermata dal fixture che tenta di creare `Marco`, già presente nel seed. | Eseguire la suite completa e le regressioni critiche sul codice effettivamente distribuito **solo dopo un gate server separato**. Nessun PASS attribuito ora. |
| 2 | UAT dei fix operativi e Finance (#62, #71–74, #78–81) | Tutte le issue hanno implementazione e test tecnici PASS documentati nel backlog; restano OPEN per verifiche Owner mirate. #64 ha definizione profilo Direzione esplicitamente approvata senza nuovi grant. | Owner ripete UAT-08, UAT-11, UAT-15, riconciliazione, TS, prima prenotazione, ricerca e percorsi Finance sui casi sintetici correnti. Non riscrivere funzionalità già presenti. |
| 3 | Report gestionali e Agenda (#63, #66, #68) | #63 Agenda, #66 Professional View e #68 Patient/Customer View risultano chiuse con PASS Owner specifico. | Nessun nuovo sviluppo motivato senza un difetto riprodotto. |
| 4 | Contabilità e integrazioni simulate | Il Completion Report documenta invoice/payment/bank, compensi, code, report e worker SdI/TS simulati sulla candidate precedente; #124 conferma installazione e dati demo, non un nuovo collaudo integrale di tutti gli stati. | Riconciliare gli scenari UAT già scritti con il nuovo Site; nessun provider, SMTP o traffico reale. |
| 5 | UI/UX finale (#75, #76, #109) | Revisione tecnica PR #126 e DRAFT provvisorio DECISION-057. | Backlog finale dopo il gate funzionale; richiede verifica visiva Owner distinta. |

## Correzione minima versionata, senza runtime

`create_http` sceglie ora una delle due route pubbliche approvate (`Marco`, `Francesca`) **solo se libera**, prima di creare alcun fixture. Se entrambe sono occupate, fallisce esplicitamente senza sostituirle. `security_acceptance.py` usa la route che il fixture ha creato e verifica il replay per `name`/`replay`, lasciando il campo `confirmation` aggiunto successivamente al contratto. Restano invariati ingress pubblico, permessi, dati demo e cleanup esatto. Nessuna modifica a logica contabile o modello dati.

Verifica eseguita: compilazione Python dei due file e `git diff --check` PASS; lettura della whitelist `Marco/Francesca`, dell'autoname `field:route`, del contratto di replay corrente e del cleanup fixture. **Non eseguiti** `bench`, Docker, HTTP, browser, seed, migration, reset, test mutativi o deploy. La correzione deve ancora superare il test runtime prima di poter chiudere il gap di evidenza.

## Prossimo gate HITCH raccomandato

Registrare la ricognizione come stato funzionale `PARTIAL`. Chiedere una decisione circoscritta per distribuire **solo il fixture corretto** nell'unico DEV e lanciare la regressione di sicurezza e gli scenari funzionali ancora non dimostrati sulla stack 16.50, preservando il dataset sintetico con verifica prima/dopo. Poi far eseguire all'Owner gli UAT mirati delle issue OPEN e il gate visivo finale. Nessun merge, intervento server o GOAL-03 è implicito in questo report.
