# EMPV AI Software Factory — SOP v1.1 (Goal-Driven)

```yaml
sop_id: EMPV-AI-SOFTWARE-FACTORY
version: '1.1'
status: APPROVATO
approved_on: '2026-10-22'
approved_by: FOUNDER
execution_model: GOAL_DRIVEN_AI_DEVELOPMENT
implementation_status: CANDIDATE_UNDER_VALIDATION
supersedes: SOP.md (v1.0 preserved as history)
```

## Principio inderogabile: autonomia finalizzata alla velocità

Il valore commerciale è **consegnare in fretta software di qualità**. Il Founder approva obiettivi (Goal), priorità, architettura e direzione UX rilevanti; Codex organizza autonomamente attività, sotto-task, uso delle skill, test e correzioni fino a consegnare un **risultato verificabile**. **Non è richiesto un micro-task, una Issue o un'approvazione per ogni passaggio interno.**

La Factory resta separata da Discovery, cliente e commercio. Riceve solo un handoff attendibile di requisiti, scopo, vincoli e autorizzazioni: l'handoff non autorizza sviluppo o produzione per implicazione.

## Unità operativa: il Goal

Ogni Goal ha un **outcome utile e verificabile**, non soltanto un compito tecnico. Contiene:
- ID, scopo, business outcome e criteria di accettazione; una Issue GitHub come tracciamento principale;
- autorizzazione pertinente, dipendenze, rischio e confini;
- report consolidato di esecuzione, collegamenti alle PR, commit e ambiente;
- evidenze proporzionate dei test e review indipendente;
- eventuale decisione Founder solo ai checkpoint strategici o quando emergono rischi materiali.

Goal tipici: **FOUNDATION** (architettura e Product Identity, Founder), **FEATURE** (capacità utente end-to-end, autonoma se autorizzata), **RELEASE** (rilascio, Founder e autorizzazione production specifica), **MAINTENANCE** (correzione/operatività nel perimetro autorizzato).

Non creare decine di Goal piccoli: un Goal può comprendere più vertical slices, UI, API, backend, database e PR. Codex tiene una struttura interna di task proporzionata, senza chiedere al Founder di approvarla a ogni cambiamento.

## Le dieci fasi v1.0 restano una guida interna, non dieci semafori

Le aree `HANDOFF → ARCHITECTURE → UX → PLANNING → FOUNDATIONS → BUILD → QA_UAT → READINESS → GO_LIVE → CONTINUITY` rimangono come **checklist di qualità e completezza di metodo**. Codex può iterare e sovrapporre il lavoro dove sensato, senza richiedere dieci permessi Founder o un hard-stop per ogni fase. Il risultato di ciascun Goal deve comunque dimostrare che le verifiche pertinenti sono state fatte.

**Non si perde** il lavoro approvato su sicurezza, architettura, Art Direction, performance, matrice requisiti, ruoli, QA, UAT o handover: si verificano quando sono pertinenti al Goal e al prodotto.

## Design e sviluppo con velocità

Per il progetto iniziale, il Goal `FOUNDATION` comprende architettura e direzione visuale; Codex può proporre **tre Art Directions** con esempi e tre utili *Design Signatures*. Il Founder approva la scelta **una volta**. Dopo l'approvazione, le feature seguono quella direzione senza una nuova richiesta per ogni schermata. Modifiche sostanziali della Product Identity richiedono un nuovo gate.

Codex costruisce **vertical slices end-to-end**, riusando fonte autorevole del dato e componenti già presenti, con PR frequenti e contenute. Quando una slice fallisce i test, corregge autonomamente e ripete; non aspetta un nuovo prompt per ogni errore. Il prodotto deve essere usabile, sicuro nei limiti testati, con permessi server-side, error/empty/loading, responsive e regressioni adeguate.

### Product Experience First: risultato della persona prima del database

L'interfaccia di ogni applicazione EMPV si progetta partendo dalle **attività reali e dai risultati attesi dagli utenti**, non dalle tabelle, dai DocType o dai campi del backend. L'ordine obbligatorio è: ruolo/obiettivo → percorso utente → interazioni e UI → mappatura su API e fonte autorevole → test di completamento attività con revisione indipendente. Backend/database nativi (per esempio Frappe/ERPNext) rimangono fonti di verità, ma non costituiscono la specifica grafica. Un form CRUD generico non dimostra che l'esperienza sia corretta. La UX deve ridurre la conoscenza tecnica richiesta all'utente, senza aggirare workflow, permessi o validazioni. Vedere `docs/EXPERIENCE-FIRST.md`.

### Conformità UI approvata per ogni Goal

Per qualunque Goal che modifica l'interfaccia (`ui_impact=YES`), anche FEATURE e MAINTENANCE, sono obbligatorie le skill UX pertinenti, il contratto grafico/versionato approvato dal Founder, la verifica dei workflow reali e una review premium indipendente con confronto screenshot desktop/mobile di **tutte** le interfacce modificate. Il backend nativo non determina i form visibili: si progettano schermate attorno ai compiti dell'utente. Per nuove identità visive serve una decisione Founder; per modifiche ordinarie vale la direzione già approvata, senza micro-gate. Il validatore blocca i Goal privi di evidenze, ma le dichiarazioni devono essere verificate esternamente. Protocollo: `docs/UI-QUALITY-GATE.md`.

## Un unico ciclo completo per Goal: sviluppo, CI, DEV e collaudo

Per un Goal `FEATURE` o `MAINTENANCE` con DEV autorizzato, l'outcome è **una funzionalità funzionante su DEV, verificata con API e browser reali e pronta per il walkthrough Owner**, non soltanto una PR con test sintetici verdi.

**Un solo mandato iniziale** può coprire ricognizione → sviluppo verticale UI/React + backend/API/dati necessari → fix autonomi → test/CI → **installazione DEV condizionatamente preautorizzata** → test live multiruolo e regressioni → fix/test successivi → report consolidato e Owner UAT. Non fermarsi dopo la sola CI a richiedere un secondo prompt per la medesima installazione già autorizzata. Codex sceglie autonomamente sottotask, skill, ordini dei test e fix nel perimetro del Goal.

### Il gate DEV è distinto ma può essere concesso all'avvio

**Autorizzazione allo sviluppo ≠ autorizzazione al deploy**. Il Founder può rilasciare, contestualmente al Goal, una autorizzazione DEV **separata, esplicita, circoscritta e condizionata**, registrata nell'Issue e nel Goal:
- Ambiente non produttivo identificato, soli servizi/risorse modificabili e risorse da preservare; vincoli di runtime, ruoli, dati esclusivamente sintetici e operazioni vietate.
- Artefatto derivato dal Goal autorizzato, HEAD/SHA e manifest/immagine verificati prima di ogni switch; nessuna installazione da branch sconosciuti.
- Condizioni preventive: CI/test pertinenti PASS, review tecnica proporzionata, preflight risorse e lock, checkpoint/backup privato e integro, restore su risorse isolate quando previsto, rollback dimostrabile e piano di stop.
- Prove live previste: API Frappe/autorizzazioni server e 403/IDOR reali, desktop/mobile, ruoli, centri, navigazione, persistenza, errori e regressioni in scope; non promuovere mock a PASS live.
- Limiti: nessuna migrazione/schema, modifica permessi/ruoli, dati personali, provider/costi, produzione/cutover o altre mutazioni escluse senza nuovo gate.

Per il motore v1.1, il Goal dichiara `risk_flags: ["controlled_dev_deploy"]` e l'approvazione specifica `approvals.controlled_dev_deploy` con riferimento alla decisione Owner. Il validatore locale controlla la **presenza dichiarata** del gate prima di `READY_FOR_REVIEW`, ma non autentica l'Owner né autorizza il server: Codex deve verificarne indipendentemente fonte, ambiente e condizioni **prima** di operare sul DEV.

Se condizioni e ambito restano invariati, Codex aggiorna DEV e ripete test/fix/CI **senza ulteriori micro-approvazioni**. Ogni nuova immagine richiede nuovamente controlli sullo SHA, preflight e rollback. Se il gate manca, Codex termina comunque analisi, codice e test isolati e chiede **una sola decisione raggruppata** per il DEV.

**STOP + nuova approvazione** soltanto se occorre ampliare il perimetro: migrazione/DocPerm/schema, dati reali, operazione distruttiva, ambiente diverso, rollback non affidabile, rischio materiale, spesa, produzione o cambio scopo. Non usare un permesso DEV di un Goal per il successivo.

**Accettazione distinta:** `PASS_OFFLINE` ≠ `PASS_LIVE` ≠ `OWNER_ACCEPTED`. La Issue resta aperta finché i criteri in scope non sono verificati e l'Owner ha svolto il walkthrough, se richiesto. **Merge PR, go-live, produzione e cutover non sono mai autorizzati implicitamente dal gate DEV**; ogni decisione è tracciata separatamente.

## UAT automatizzato: Codex simula il cliente, Owner approva il risultato

Un Goal autorizzato comprende anche il **collaudo funzionale e visuale automatico**, così l'Owner non deve ripercorrere decine di bottoni dopo ogni ciclo. Codex **parte dagli acceptance criteria approvati indipendenti dal codice**, poi verifica con browser reale, backend/API reali, ruoli e centri, prove mutative con fixture test-owned isolate, screenshot desktop/mobile e report di copertura. Un controllo sui soli mock o un test inventato per assecondare il codice non è accettazione del cliente.

Codex corregge autonomamente i problemi nel Goal, ripete regressioni, CI e (solo con specifico gate DEV) test live. Consegna **un unico rapporto** con PASS/FAIL/BLOCKED/NOT_TESTED, prove sanificate, commit, build e limiti, oltre a poche schermate rappresentative. Il reviewer è indipendente dall'implementatore. **Codex deve coprire tutte le interfacce modificate dal Goal**, non soltanto alcune schermate rappresentative: ogni interfaccia ha test dei flussi, azioni, validazioni, stati, permessi, persistenza, responsive, accessibilità e regressioni pertinenti, con prova e screenshot collegati al commit e all'ambiente. Codex corregge e ripete autonomamente fino alla verifica dei risultati, senza interrompere il Founder con microtask. **Voi Founder effettuate la verifica finale di ogni interfaccia coinvolta in un unico walkthrough del Goal**, approvando o richiedendo correzioni per ciascuna schermata. Questo è un controllo finale sui risultati, non una serie di approvazioni a ogni passo tecnico. Il Goal è `READY_FOR_REVIEW` dopo i controlli Codex e la review indipendente; passa a `VERIFIED/OWNER_ACCEPTED` solo con la vostra accettazione per le interfacce interessate.

La **UAT automatizzata non equivale ad OWNER_ACCEPTED** e non concede merge o produzione. Vedere [Protocollo UAT automatizzato](docs/AUTOMATED-OWNER-UAT.md) per oracle, test end-to-end, fixture, report e limiti.

## Organizzazione GitHub e skill

- **1 Goal → 1 Issue principale**; sub-issue facoltative solo per attività indipendenti, rischi o tracciamento necessario.
- Codex può preparare più PR piccole sotto lo stesso Goal. Evitare branch di durata e dimensione eccessive.
- `AGENTS.md` dà il mandato di **raggiungere l'outcome**, non di fermarsi a ogni micro-fase.
- Skill versionate richiamate quando pertinenti. Le skill obbligatorie si definiscono **per tipo di Goal** e si usano con prove; non introdurre verifiche artificiose per ogni file o pulsante.
- Aggiornare GitHub a progressi/decisioni **significativi**, al completamento del Goal e sui blocker reali.
- Limite WIP prudente di 3 Goal ACTIVE nel template, regolabile con decisione; non un vincolo di sequenzialità delle dieci fasi.

## Controlli e autorizzazioni che restano

- **Tutti i Goal READY_FOR_REVIEW:** acceptance criteria e test realmente eseguiti, review indipendente, risultato su commit e riferimenti di evidenza. Codex non può autocertificare il PASS.
- **FOUNDATION e RELEASE:** gate Founder.
- **FEATURE e MAINTENANCE:** niente gate Founder automatico se il Goal è già autorizzato e non aggiunge rischi; serve review tecnica e evidence gate.
- **Qualsiasi Goal:** chiedere decisione prima di modificare scopo, permessi sensibili, dati reali, migrazioni distruttive, dipendenze a pagamento, produzione o accettare eccezioni di sicurezza.
- **Production:** autorizzazione esplicita separata, restore/rollback e verifica post-deploy in base al rischio. Un APPROVED nel JSON non autorizza la produzione.

I criteri `NOT_TESTED ≠ PASS`, `DOCUMENTED ≠ EXECUTED`, `PR ≠ MERGED`, `MERGED ≠ DEPLOYED` restano invariati.

## Validazione e velocità

`factory/goal_cli.py` e `templates/v1.1/` costituiscono un **nuovo candidato tecnico** indipendente dalla implementazione v1.0, preservata per confronto e regressioni. Il validatore locale controlla struttura e coerenza delle dichiarazioni; **non autentica** chi ha approvato, la realtà dei test, la genuinità delle skill, la qualità del codice e l'enforcement GitHub. Sono necessari review indipendente, pilot su app sintetica e controlli di merge/deploy esterni.

I tempi si riducono eliminando i semafori e la burocrazia non necessari, **non** eliminando test, sicurezza o autorizzazioni materiali.

## Cosa la Factory non fa

Non è Discovery, pricing, governance clienti o commerciale. Non esegue autonomamente comandi su account Codex o macchine cliente senza tool, capacità e permessi configurati. La versione 1.1 è approvata come metodo dal Founder, mentre il motore tecnico resta `CANDIDATE_UNDER_VALIDATION`.
