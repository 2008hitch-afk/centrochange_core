# Centro Change #148 — DECISION-066 APPROVATO — FIX → RETEST → CONTINUE

**Owner authorization:** [HC-0005 DECISION-066](https://github.com/2008hitch-afk/hitch-client-discovery/blob/main/clients/HC-0005/decisions/DECISION-066-autonomous-fix-retest-continue-dev-delivery.md) · [HITCH PR #116 merged](https://github.com/2008hitch-afk/hitch-client-discovery/pull/116).  
**Data:** 21/10/2026  
**Scope:** una sola webapp Centro Change DEV, PR implementativa [#150 DRAFT](https://github.com/2008hitch-afk/centrochange_core/pull/150), [issue #148](https://github.com/2008hitch-afk/centrochange_core/issues/148), branch `issue-148/premium-react-frontend`, HEAD registrata al gate `16cc5cd9fa465956c4747ed3371ea98ecdb591ff` (verificare HEAD reale).  
**Stato storico (non stato corrente da dichiarare come PASS):** primo e secondo tentativo runtime finiti in `BLOCKED_SAFE_ROLLBACK`; `centrochange-dev` su vecchia immagine, nove servizi attivi, Site/DB/volumi preservati; `cc_premium_primary=0`, nuova UI non installata.

## Risultati già dimostrati e limiti

[Report DECISION-065](https://github.com/2008hitch-afk/centrochange_core/blob/issue-148/premium-react-frontend/docs/ui/premium-react/DECISION-065-SECOND-ATTEMPT-REPORT-2026-10-21.md): restore cifrato full-Site a **6 componenti realmente PASS**, tutti i **55 elementi Site** e **929 tabelle** confrontati, Playwright **12/12 live PASS**, integrated suite **192 PASS**. Questi sono PASS della precedente candidata temporanea, **non** un collaudo globale della HEAD attuale. In quel tentativo `security_acceptance.py` ha creato una prenotazione attraverso la route persistente `Marco` anziché la route della fixture `Francesca`; il teardown ha negato la cancellazione non-possessore (comportamento fail-closed corretto) e il runtime è stato recuperato integralmente. I due fix (HTTP fixture route owned; ruolo di reporting non super-admin) sono sulla PR #150 ma il corretto harness HTTP **non è ancora stato rieseguito live**. Quattro checkpoint/chiavi rimangono privati sul server.

**L'Owner ha autorizzato l'autonomia tecnica**, non una deregolamentazione. Il test fragile va corretto e provato senza rischiare la UAT persistente.

## Nuova regola di lavoro

Ogni difetto ordinario = **riproduci → analizza → correggi → aggiungi test → riesegui → continua**. Non occorre tornare all'Owner per bug React/CSS, form, asset, fixture, assertion, build, test o API già autorizzate. Non basta scrivere un report e fermarsi dopo due correzioni. Codex lavora sullo stesso macro-goal e PR DRAFT.

**Un rischio materiale** su dati UAT, ownership delle fixture, backup/restore, sicurezza, ruoli, schema, privacy, risorse o rollback **non è** un semplice bug. In caso di rischio materiale si sospendono scritture e modifiche DEV, si fa safe rollback/isolation se verificabile e si segnala una sola barriera concreta Owner.

### Ordine esecutivo vincolante

1. Preflight su branch/HEAD/manifest/image, nove servizi `centrochange-dev`, Site/DB/volumi/porta, Compose privato con identità legittima, `cc_synthetic_dev=1`, cgroup/RAM/PSI/OOM/disco, identità e stop gate. Nessuna patch manuale nei container; no dati reali. **Non assumere che l'immagine `sha256:a792...` corrisponda alla HEAD `16cc5cd`**, che contiene test/backend fixes successivi.
2. Audit **di tutte le suite potenzialmente mutative** (`security_acceptance.py`, `reporting_acceptance.py`, altre API/HTTP/finance/booking): nessun riferimento hardcoded a `Marco`, a una route persistente né a nome/ID di documenti non posseduti. Fixture univoche con tag, scope sede e owner espliciti, ispezione prima di scrivere, cleanup soltanto record `owned`, test negativi sul teardown, abort se non si riesce a dimostrare ownership/isolamento. Non indebolire permessi o modificare fixture ufficiali senza fonte.
3. Stage su **restore isolato vero** del Site, con il nuovo backup cifrato a 6 componenti, `private/uat` e manifest completo, rete interna, no port exposure, no volume/DB DEV montati, risorse temporanee `cc148-restore-*` nominate nelle decisioni. Dimostrare verifiche Site/DB e, quando tecnicamente sicuro/possibile, eseguire qui prima tutte le suite con scritture e regressioni, anche più volte dopo normali bugfix. Ogni nuova build/immagine deve provenire dal codice pinned, non da patch in container. Se capacità host/isolamento impedisce staging, STOP prima di modificare DEV con test pericolosi.
4. **Solo quando il candidato è realmente pronto**, promozione controllata nell'UNICO `centrochange-dev`: backup/restore PASS aggiornati, source pinned, image ID corretto, Compose static/live diff PASS, no migrate/schema change, protezione 4 volumi+DB+Site/rete/porta, ricreare soltanto sei servizi applicativi. Finestra di write freeze <=120 minuti (non estendibile implicitamente), preserve rollback/checkpoint/chiavi.
5. **Live QA per intero MVP autorizzato**: 7 ruoli+Guest, centri A/B, permessi Frappe/CSRF, route dirette/IDOR, 11 liste+11 schede/form, Agenda/booking, pazienti/professionisti, tariffe/catalogo/pacchetti, Finanza, Invoice/Payment Entry read, XML, stampa, audit, p50/p95, desktop/mobile, locale IT. Test di scrittura soltanto su propri record synthetic-owned. Completo pass visuale automatizzato, screenshot/log sanificati. Vietato attribuire PASS ai mock/alla prima versione.
6. Errori ordinari in QA live: classificare e correggere. **Non fare automaticamente rollback su una semplice assertion UI o test fragile** se tutto lo stato è sicuro, i dati non sono contaminati, i vincoli temporali sono rispettati e la correzione può essere fatta in isolamento; poi ritestare il caso e continuare. Se richiede nuova immagine, ricostruire prima fuori Site/volumi DEV, verificare recovery/freeze/safety; non autorizza cicli illimitati di reinstallazione, né aggirare STOP.
7. **Consegna**: `SINGLE_STACK_DEV_INSTALLED` + `FULL_MVP_LIVE_QA_PASS` + `REACT_PREMIUM_VISUAL_QA_PASS` = `READY_FOR_OWNER_VISUAL_UAT` con URL locale/privato e modalità di accesso sicure, **non** `OWNER_ACCEPTED`. Il flag `cc_premium_primary=0` resta tale finché l'Owner non approva esplicitamente la nuova interfaccia. Cleanup storico separato per lista di ID e conferma Owner; solo restore effimero esatto eliminabile senza nuova approvazione.
8. **Rapporto** finale solo PASS comprovato oppure BLOCKED per autentico rischio materiale. Se BL0CKED non perdere comunque le correzioni offline; la PR #150 resta DRAFT, non mergiare.

## Esclusioni permanenti

Niente nuovi deployment permanenti, nuovo VPS/server/GOAL-03, produzione, real customer/patient data, provider TS/SdI/PEC/SMTP/banca, nuove business rules o escalation ruolo, `ignore_permissions`, Payment Entry create/allocate diretto o Patient/Practitioner/Item standalone create non autorizzate, `migrate` o reset Site/DB, `down -v`/prune/cancellazioni storiche, merge PR #150, default React anticipato, licenze a pagamento. Un accesso root non autorizza decisioni ulteriori.

## Prompt per Codex: unico ciclo senza micropassaggi

```text
CENTRO CHANGE #148 — DECISION-066 APPROVATO — FIX → RETEST → CONTINUE.

Nella STESSA sessione Codex riprendi l'unica PR DRAFT #150, dalla sua HEAD effettiva. L'Owner ha APPROVATO E AUTORIZZATO DECISION-066 (HITCH clients/HC-0005/decisions/DECISION-066-autonomous-fix-retest-continue-dev-delivery.md). Leggi questo documento docs/ui/PREMIUM-REACT-DECISION066-AUTONOMOUS-FIX-RETEST-CONTINUE.md su main, AGENTS.md, DECISION-060–066, il report del secondo tentativo DECISION-065 e il piano di recovery full-site.

OBIETTIVO: UN SOLO Centro Change DEV funzionante con React Premium e l'intero MVP approvato, pronto al collaudo visivo Owner. Non un altro report di pianificazione.

Codex deve correggere e ritestare AUTONOMAMENTE ogni difetto ORDINARIO di test/fixture/UI/API in scope, aggiungere regression checks e andare avanti; NON effettuare rollback automatico al primo test fallito. Stop solo per rischio MATERIALE a dati, permessi, restore, schema, risorse, privacy o recovery, non bypassare ACL né nuovi business gate.

Prima dell'unico switch DEV:
- riprendere HEAD e preservare worktree e PR; allineare e validare immagine integrale pinned con tutti i fix della HEAD;
- audit di TUTTI i test e delle fixture (HTTP, booking, finance, reporting, teardown) per ogni nome/ID/route hard-coded o UAT persistente, test owned-only e transazionali; no Marco route o altri record legacy di terzi;
- backup cifrato completo Site+DB a 6 componenti, restore vero isolato con confronto file/metadata/929 tabelle attuali (i numeri storici non sono hard gate), checkpoint salvati fuori Git, test invasivi eseguiti e iterati per quanto sicuro sulla restore isolata cc148-restore-* invece che sul Site canonico; verifica memoria/PSI/cgroup e assenza dipendenze di altri progetti.

Quando questa validazione è PASS, un'unica promozione riproducibile dei sei servizi app dentro centrochange-dev, preservando Site/DB/MariaDB/Redis/4 volumi e stessa rete/porta; no migrate, write freeze <=120min, checkpoint e rollback verificati. Esegui tutto QA live: 7 ruoli+Guest, centro A/B, ACL/CSRF/native/IDOR, 11 liste e 11 form, workflow MVP e Finance, Playwright desktop/mobile, screenshot e performance. Quando un semplice test non passa e non c'è rischio materiale, FIX → RETEST → CONTINUE nello stesso incarico. Niente reinstallazioni DEV illimitate.

Se e solo se FULL_LIVE_QA_PASS e grafica verificata, lascia la nuova immagine sul singolo DEV con React /premium accessibile per Owner UAT, ma cc_premium_primary=0; Owner sceglierà dopo la promozione a unica home React. Non fare cleanup storico o merge. Consegna URL privato e checklist sintetica. Se autentico blocco, stop sicuro con un report conclusivo; non inventare PASS.

Non chiedere micropassaggi per attività ordinarie. NON creare un nuovo goal, non reiniziare React, non fare 10 report parziali.
```
